import base64
import hashlib
import os
import struct

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

load_dotenv()

app = FastAPI()

WECHAT_TOKEN = os.getenv("WECHAT_TOKEN")
WECHAT_ENCODING_AES_KEY = os.getenv("WECHAT_ENCODING_AES_KEY")


class ChatRequest(BaseModel):
    user_id: str
    message: str


@app.get("/")
def home():
    return {"status": "AI bot backend is running"}


@app.post("/chat")
def chat(req: ChatRequest):
    return {
        "user_id": req.user_id,
        "reply": f"我收到了：{req.message}"
    }


def verify_signature(token: str, timestamp: str, nonce: str, encrypted: str, msg_signature: str) -> bool:
    items = [token, timestamp, nonce, encrypted]
    items.sort()
    raw = "".join(items).encode("utf-8")
    sha1 = hashlib.sha1(raw).hexdigest()
    return sha1 == msg_signature


def decrypt_wechat_message(encrypted_text: str, encoding_aes_key: str) -> str:
    aes_key = base64.b64decode(encoding_aes_key + "=")
    encrypted_data = base64.b64decode(encrypted_text)

    cipher = Cipher(
        algorithms.AES(aes_key),
        modes.CBC(aes_key[:16])
    )
    decryptor = cipher.decryptor()

    decrypted = decryptor.update(encrypted_data) + decryptor.finalize()

    pad = decrypted[-1]
    if pad < 1 or pad > 32:
        raise ValueError("Invalid padding")

    decrypted = decrypted[:-pad]

    msg_len = struct.unpack(">I", decrypted[16:20])[0]
    msg = decrypted[20:20 + msg_len]

    return msg.decode("utf-8")


@app.get("/wechat")
async def wechat_verify(request: Request):
    params = dict(request.query_params)

    msg_signature = params.get("msg_signature")
    timestamp = params.get("timestamp")
    nonce = params.get("nonce")
    echostr = params.get("echostr")

    print("企业微信验证参数:", params)

    # 关键修改：
    # 如果后台只是空参数测试 URL 是否可访问，就直接返回 200 OK
    if not params:
        print("空参数访问，返回 success")
        return PlainTextResponse(
            content="success",
            status_code=200,
            media_type="text/plain"
        )

    if not all([msg_signature, timestamp, nonce, echostr]):
        print("参数不完整")
        return PlainTextResponse(
            content="success",
            status_code=200,
            media_type="text/plain"
        )

    if not WECHAT_TOKEN or not WECHAT_ENCODING_AES_KEY:
        print("环境变量缺失")
        print("WECHAT_TOKEN:", WECHAT_TOKEN)
        print("WECHAT_ENCODING_AES_KEY:", WECHAT_ENCODING_AES_KEY)
        return PlainTextResponse("missing env config", status_code=500)

    signature_ok = verify_signature(
        WECHAT_TOKEN,
        timestamp,
        nonce,
        echostr,
        msg_signature
    )

    if not signature_ok:
        print("签名错误")
        return PlainTextResponse("signature error", status_code=403)

    try:
        plain_text = decrypt_wechat_message(echostr, WECHAT_ENCODING_AES_KEY)
        print("解密成功:", plain_text)
        return PlainTextResponse(
            content=plain_text,
            status_code=200,
            media_type="text/plain"
        )
    except Exception as e:
        print("解密失败:", repr(e))
        return PlainTextResponse("decrypt error", status_code=500)


@app.post("/wechat")
async def wechat_receive_message(request: Request):
    body = await request.body()
    print("收到企业微信 POST 消息:")
    print(body.decode("utf-8", errors="ignore"))

    return PlainTextResponse(
        content="success",
        status_code=200,
        media_type="text/plain"
    )