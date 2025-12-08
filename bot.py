import os
import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# URL audio silent (1 detik)
AUDIO_URL = "https://raw.githubusercontent.com/anars/blank-audio/master/1-second-of-silence.mp3"

@bot.event
async def on_ready():
    print(f"Bot online sebagai {bot.user}")

@bot.command()
async def satpam(ctx):
    if not ctx.author.voice:
        return await ctx.send("Kamu harus ada di voice channel dulu!")

    channel = ctx.author.voice.channel
    voice_client = ctx.voice_client

    if voice_client and voice_client.channel == channel:
        return await ctx.send("Satpam sudah di sini bos!")

    if voice_client:
        await voice_client.move_to(channel)
    else:
        voice_client = await channel.connect()

    await ctx.send("Satpam masuk voice! 🔊")

    # Loop audio
    source = await discord.FFmpegOpusAudio.from_probe(
        AUDIO_URL,
        method="fallback",
        before_options="-stream_loop -1 -reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"
    )
    voice_client.play(source, after=lambda e: print("Playing silence loop"))

@bot.command()
async def tidur(ctx):
    voice_client = ctx.voice_client
    if voice_client:
        await voice_client.disconnect()
        await ctx.send("Satpam izin tidur dulu 😴")
    else:
        await ctx.send("Satpam tidak ada di voice!")

bot.run(os.getenv("DISCORD_TOKEN"))
