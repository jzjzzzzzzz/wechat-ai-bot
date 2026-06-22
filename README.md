# WeChat AI Bot Backend

FastAPI backend prototype for a WeChat/Enterprise WeChat bot. It exposes a simple chat endpoint plus WeChat verification and message receiver routes.

## Features

- `GET /`: health-style status response.
- `POST /chat`: simple JSON echo reply for local testing.
- `GET /wechat`: Enterprise WeChat URL verification flow.
- `POST /wechat`: receives WeChat callback XML/body and returns `success`.
- AES message helper functions for encrypted WeChat payload handling.

## Setup

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
```

Fill `.env` locally. Do not commit real credentials.

## Environment Variables

- `WECHAT_TOKEN`: token configured in the WeChat callback settings.
- `WECHAT_ENCODING_AES_KEY`: WeChat callback encoding AES key.
- `OPENAI_API_KEY`: optional key for future AI reply integration.

## Run

```bash
.venv/bin/uvicorn main:app --reload
```

Open:

```text
http://127.0.0.1:8000/
```

## Smoke Test

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"local","message":"hello"}'
```

## Security Notes

- Keep `.env` local only.
- Avoid printing real token values in logs.
- Use a public HTTPS tunnel or deployment URL only after environment variables are set.
