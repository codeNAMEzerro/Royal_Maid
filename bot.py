import os
import random
import asyncio
import discord
from discord.ext import commands
from discord.ui import View, Select, Button

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# URL audio silent (1 detik)
AUDIO_URL = "https://raw.githubusercontent.com/anars/blank-audio/master/1-second-of-silence.mp3"

# Leaderboard skor duel
scores = {}

# Voice lines satpam
win_lines = [
    "Satpam menang bos! 🔥",
    "Gampang bos 😎",
    "Heheh kena mental ya? 😏"
]
lose_lines = [
    "Satpam kalah bos 😭",
    "Sial… kurang fokus!",
    "Tadi tangan kepeleset bos 😵"
]

# ================= SATPAM VOICE PROTECT 🎧 ================= #

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

# ================= MINIGAME BATU KERTAS GUNTING 🎮 ================= #

choices = {
    "🪨 Batu": "batu",
    "📜 Kertas": "kertas",
    "✂️ Gunting": "gunting"
}

def determine_winner(p1, p2):
    if p1 == p2:
        return "seri"

    rules = {"batu":"gunting","gunting":"kertas","kertas":"batu"}

    return "p1" if rules[p1] == p2 else "p2"


class RematchView(View):
    def __init__(self, player1, player2):
        super().__init__(timeout=20)
        self.p1 = player1
        self.p2 = player2

    @discord.ui.button(label="🔁 Rematch", style=discord.ButtonStyle.primary)
    async def rematch(self, interaction: discord.Interaction, button: Button):
        if interaction.user not in [self.p1, self.p2]:
            return await interaction.response.send_message(
                "Kamu bukan bagian duel ini!", ephemeral=True
            )

        await interaction.response.edit_message(
            content=(
                f"🔥 **REMATCH DIMULAI!**\n"
                f"{self.p1.mention} VS {self.p2.mention}\n"
                "Pilih gerakan kalian kembali 👇"
            ),
            view=RPSView(self.p1, self.p2)
        )
        self.stop()


class RPSView(View):
    def __init__(self, p1, p2):
        super().__init__(timeout=30)
        self.p1 = p1
        self.p2 = p2
        self.picks = {}

    async def reveal_result(self, interaction):
        winner = determine_winner(
            self.picks[self.p1.id], self.picks[self.p2.id]
        )

        # Update skor
        if winner == "p1":
            scores[self.p1.id] = scores.get(self.p1.id, 0) + 1
            result_text = f"🏆 {self.p1.mention} MENANG!\n🎙️ {random.choice(win_lines)}"
        elif winner == "p2":
            scores[self.p2.id] = scores.get(self.p2.id, 0) + 1
            result_text = f"🏆 {self.p2.mention} MENANG!\n🎙️ {random.choice(lose_lines)}"
        else:
            result_text = "⚔️ **Seri!** Tidak ada yang menang."

        await interaction.edit_original_response(
            content=(
                f"🧍 {self.p1.mention}: **{self.picks[self.p1.id]}**\n\n"
                f"🧑‍💻 {self.p2.mention}: **{self.picks[self.p2.id]}**\n\n"
                f"{result_text}"
            ),
            view=RematchView(self.p1, self.p2)
        )
        self.stop()

    async def countdown_animation(self, interaction):
        msg = await interaction.original_response()
        for num in ["3️⃣", "2️⃣", "1️⃣", "🎯"]:
            await asyncio.sleep(0.7)
            await msg.edit(content=f"{num}...")

    @discord.ui.select(
        placeholder="Pilih gerakan!",
        options=[discord.SelectOption(label=k) for k in choices.keys()]
    )
    async def select_move(self, interaction: discord.Interaction, select: Select):
        if interaction.user not in [self.p1, self.p2]:
            return await interaction.response.send_message(
                "Kamu bukan bagian duel ini!", ephemeral=True
            )

        pick = choices[select.values[0]]
        self.picks[interaction.user.id] = pick

        await interaction.response.send_message(
            f"Kamu pilih **{pick}** ✔",
            ephemeral=True
        )

        if len(self.picks) == 2:
            await asyncio.sleep(1)
            await self.countdown_animation(interaction)
            await self.reveal_result(interaction)


# ================= COMMAND START DUEL ================= #

@bot.command()
async def satusatu(ctx, member: discord.Member = None):
    if not member:
        return await ctx.send("Format salah!\nGunakan: `!satusatu @player2`")
    if member == ctx.author:
        return await ctx.send("Tidak bisa duel diri sendiri!")
    if member.bot:
        return await ctx.send("Tidak bisa duel dengan bot!")

    await ctx.send(
        f"🥊 **DUEL DIMULAI!**\n"
        f"{ctx.author.mention} VS {member.mention}\n\n"
        "Pilih gerakan kalian 👇",
        view=RPSView(ctx.author, member)
    )


@bot.command()
async def leaderboard(ctx):
    if not scores:
        return await ctx.send("Belum ada skor duel 🥲")

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    text = "\n".join(
        f"🏅 <@{user_id}> — **{score}** menang"
        for user_id, score in sorted_scores
    )

    await ctx.send(f"📜 **LEADERBOARD DUEL**\n{text}")


bot.run(os.getenv("DISCORD_TOKEN"))
