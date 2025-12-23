import os
import discord
from discord.ext import commands
import requests

TOKEN = os.getenv("TOKEN_BOT_DISCORD")

if not TOKEN:
    raise Exception("ENV TOKEN_BOT_DISCORD belum diset di Railway")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

FIVEM_SERVER_LIST = "https://servers-live.fivem.net/api/servers/streamed"
MAX_SERVER_CHECK = 25

@bot.event
async def on_ready():
    print(f"Bot online sebagai {bot.user}")

@bot.command()
async def carihama(ctx, server_keyword: str, *, player_keyword: str):
    await ctx.send("🔍 Mencari player...")

    try:
        servers = requests.get(FIVEM_SERVER_LIST, timeout=10).json()
    except:
        return await ctx.send("❌ Gagal mengambil server list FiveM.")

    hasil = []

    for i, (_, server) in enumerate(servers.items()):
        if i >= MAX_SERVER_CHECK:
            break

        hostname = server.get("hostname", "").lower()
        if server_keyword.lower() not in hostname:
            continue

        endpoints = server.get("connectEndPoints", [])
        if not endpoints:
            continue

        players_url = f"http://{endpoints[0]}/players.json"

        try:
            players = requests.get(players_url, timeout=3).json()
        except:
            continue

        for p in players:
            name = p.get("name", "").lower()
            if player_keyword.lower() in name:
                hasil.append({
                    "server": server.get("hostname"),
                    "player": p["name"],
                    "ping": p.get("ping")
                })

    if not hasil:
        return await ctx.send("❌ Player tidak ditemukan.")

    embed = discord.Embed(
        title="🎮 Hasil Pencarian Player FiveM",
        description=f"Server: **{server_keyword}**\nPlayer: **{player_keyword}**",
        color=0x00ff99
    )

    for h in hasil[:10]:
        embed.add_field(
            name=h["player"],
            value=f"{h['server']}\nPing: {h['ping']}ms",
            inline=False
        )

    embed.set_footer(text="FiveM Public Tracker • Experimental")
    await ctx.send(embed=embed)

bot.run(TOKEN)
