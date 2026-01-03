import discord
from discord.ext import commands
import os

TOKEN = os.environ.get("MUSIC_BOT_TOKEN")
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"[MusicBot] Logged in as {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("MusicBot is online 🎵")

if not TOKEN:
    raise RuntimeError("MUSIC_BOT_TOKEN not set")

bot.run(TOKEN)
