import discord
from discord.ext import commands
import os

TOKEN = os.environ.get("MOD_BOT_TOKEN")
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"[ModBot] Logged in as {bot.user}")

@bot.command()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason=None):
    await member.kick(reason=reason)
    await ctx.send(f"{member} was kicked")

@bot.command()
async def ping(ctx):
    await ctx.send("ModBot is watching 👮")

if not TOKEN:
    raise RuntimeError("MOD_BOT_TOKEN not set")

bot.run(TOKEN)
