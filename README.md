convert voice messages to texts

packaged in a telegram bot

hosted on fly.io

```
fly launch
fly secrets set OPENAI_API_KEY=
fly secrets set BOT_API_TOKEN=
fly deploy
fly scale count 1 --max-per-region 1
```
