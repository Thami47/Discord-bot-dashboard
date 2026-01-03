# Discord Bot Dashboard

A web dashboard to control multiple Discord bots with OAuth login, admin panel, and real-time logs.

## Setup

1. Set environment variables:

export SECRET_KEY="supersecret"
export DISCORD_CLIENT_ID="your_client_id"
export DISCORD_CLIENT_SECRET="your_client_secret"
export DISCORD_REDIRECT_URI="https://YOURAPP.fly.dev/callback"
export MUSIC_BOT_TOKEN="your_music_bot_token"
export MOD_BOT_TOKEN="your_mod_bot_token"

2. Build Docker image:

docker build -t discord-bot-dashboard .

3. Run locally:

docker run -p 8080:8080 discord-bot-dashboard

4. Deploy to Fly.io:

fly launch
fly secrets set SECRET_KEY="supersecret" ...
fly deploy
