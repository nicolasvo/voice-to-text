convert voice messages to texts

packaged in a telegram bot

speech-to-text runs on Modal (faster-whisper large-v3); the bot itself runs via docker compose

```
# one-time: deploy the Modal app
uv run modal deploy modal_app.py

# run the bot
docker compose up -d --build
```

`.env` must define `BOT_API_TOKEN`, `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`.
