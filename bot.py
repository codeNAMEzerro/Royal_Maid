import os
import random
import asyncio
import discord
from discord.ext import commands
from discord.ui import View, Select, Button

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

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
SILENT_FILE = "audio/silence.opus"


@bot.command()
async def satpam(ctx):
    if not ctx.author.voice:
        return await ctx.send("Kamu harus ada di voice channel dulu!")

    channel = ctx.author.voice.channel
    vc = ctx.voice_client

    # Jika sudah di channel tersebut
    if vc and vc.channel == channel:
        return await ctx.send("Satpam sudah di sini bos!")

    # Connect atau move
    if vc:
        await vc.move_to(channel)
    else:
        vc = await channel.connect(reconnect=True)

    await ctx.send("Satpam masuk voice! 🔊")

    # Stop jika ada audio sebelumnya
    if vc.is_playing():
        vc.stop()

    # Loop audio
    def loop(err):
        if err:
            print("loop error:", err)
        vcc = ctx.voice_client
        if vcc:
            try:
                vcc.play(
                    discord.FFmpegPCMAudio(SILENT_FILE),
                    after=loop
                )
            except:
                pass

    try:
        vc.play(discord.FFmpegPCMAudio(SILENT_FILE), after=loop)
    except Exception as e:
        print("FFmpeg error:", e)
        return await ctx.send("⚠ FFmpeg tidak ditemukan!")


@bot.command()
async def tidur(ctx):
    vc = ctx.voice_client
    if vc:
        await vc.disconnect()
        await ctx.send("Satpam izin tidur 😴")
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


class RPSView(View):
    def __init__(self, p1, p2):
        super().__init__(timeout=30)
        self.p1 = p1
        self.p2 = p2
        self.picks = {}
        self.result_message = None

    async def reveal_result(self):
        p1_choice = self.picks[self.p1.id]
        p2_choice = self.picks[self.p2.id]
        winner = determine_winner(p1_choice, p2_choice)

        if winner == "p1":
            scores[self.p1.id] = scores.get(self.p1.id, 0) + 1
            result_text = (
                f"🧍 {self.p1.mention}: **{p1_choice}**\n"
                f"🧑‍💻 {self.p2.mention}: **{p2_choice}**\n\n"
                f"🏆 {self.p1.mention} MENANG!\n🎙️ {random.choice(win_lines)}"
            )
        elif winner == "p2":
            scores[self.p2.id] = scores.get(self.p2.id, 0) + 1
            result_text = (
                f"🧍 {self.p1.mention}: **{p1_choice}**\n"
                f"🧑‍💻 {self.p2.mention}: **{p2_choice}**\n\n"
                f"🏆 {self.p2.mention} MENANG!\n🎙️ {random.choice(lose_lines)}"
            )
        else:
            result_text = (
                f"🧍 {self.p1.mention}: **{p1_choice}**\n"
                f"🧑‍💻 {self.p2.mention}: **{p2_choice}**\n\n"
                "⚔️ Seri!"
            )

        await self.result_message.edit(content=result_text, view=RematchView(self.p1, self.p2))
        self.stop()

    async def countdown(self):
        msg = self.result_message
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
                "Duel ini bukan untukmu!", ephemeral=True)

        pick = choices[select.values[0]]
        self.picks[interaction.user.id] = pick

        await interaction.response.send_message(
            f"Kamu memilih **{pick}** ✔",
            ephemeral=True
        )

        # Jika dua pemain sudah memilih
        if len(self.picks) == 2:
            # Buat pesan publik (semua bisa lihat)
            self.result_message = await interaction.channel.send("🕛 Menghitung hasil...")
            await self.countdown()
            await self.reveal_result()


class RematchView(View):
    def __init__(self, p1, p2):
        super().__init__(timeout=20)
        self.p1 = p1
        self.p2 = p2

    @discord.ui.button(label="🔁 Rematch", style=discord.ButtonStyle.primary)
    async def rematch(self, interaction: discord.Interaction, button: Button):
        if interaction.user not in [self.p1, self.p2]:
            return await interaction.response.send_message(
                "Hanya peserta duel yang bisa rematch!", ephemeral=True)

        await interaction.response.edit_message(
            content=(
                f"🔥 REMATCH DIMULAI!\n"
                f"{self.p1.mention} VS {self.p2.mention}\n"
                "Pilih gerakan kembali 👇"
            ),
            view=RPSView(self.p1, self.p2)
        )



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
