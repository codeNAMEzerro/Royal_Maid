import os
import discord
from discord.ext import commands
from discord.ui import View, Button

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ==========================
#     EVENT READY
# ==========================
@bot.event
async def on_ready():
    print(f"Bot {bot.user} sudah online sebagai EMPEROR MAID!")

# ==========================
#     COMMAND SATPAM
# ==========================
@bot.command()
async def satpam(ctx):
    if ctx.author.voice is None:
        return await ctx.send("Kamu tidak berada di voice channel!")

    channel = ctx.author.voice.channel

    if ctx.voice_client:
        await ctx.voice_client.move_to(channel)
    else:
        await channel.connect()

    source = discord.FFmpegPCMAudio("silence.mp3")
    ctx.voice_client.play(source, after=lambda e: print("Looping silence..."))
    await ctx.send(f"EMPEROR MAID menjaga **{channel}**.")

# ==========================
#     MINI GAME BEST OF
# ==========================
class RPSView(View):
    def __init__(self, p1, p2, rounds):
        super().__init__(timeout=60)
        self.p1 = p1
        self.p2 = p2
        self.rounds = rounds
        self.p1_score = 0
        self.p2_score = 0
        self.choices = {}
        self.current_round = 1
        self.playing = True

    async def interaction_done(self, interaction):
        if len(self.choices) == 2:
            await self.process_round(interaction)

    async def process_round(self, interaction):
        mapping = {"✊": "Batu", "✋": "Kertas", "✌️": "Gunting"}
        p1_c = self.choices[self.p1]
        p2_c = self.choices[self.p2]

        win = {"✊": "✌️", "✌️": "✋", "✋": "✊"}

        if p1_c == p2_c:
            result = "Seri!"
        elif win[p1_c] == p2_c:
            self.p1_score += 1
            result = f"**{self.p1.display_name} menang ronde ini!**"
        else:
            self.p2_score += 1
            result = f"**{self.p2.display_name} menang ronde ini!**"

        embed = discord.Embed(title=f"🎮 Satu Satu — Ronde {self.current_round}/{self.rounds}")
        embed.add_field(name=self.p1.display_name, value=mapping[p1_c])
        embed.add_field(name=self.p2.display_name, value=mapping[p2_c])
        embed.add_field(name="Hasil Ronde", value=result, inline=False)
        embed.add_field(name="Skor",
                        value=f"{self.p1.display_name}: {self.p1_score}
{self.p2.display_name}: {self.p2_score}",
                        inline=False)

        await interaction.followup.send(embed=embed)

        self.choices = {}
        self.current_round += 1

        if self.p1_score > self.rounds // 2 or self.p2_score > self.rounds // 2:
            self.playing = False

        if not self.playing or self.current_round > self.rounds:
            await self.end_game(interaction)

    async def end_game(self, interaction):
        if self.p1_score > self.p2_score:
            winner = self.p1.display_name
        elif self.p2_score > self.p1_score:
            winner = self.p2.display_name
        else:
            winner = "Seri!"

        embed = discord.Embed(title="🏆 HASIL AKHIR — Satu Satu")
        embed.add_field(name="Pemenang", value=str(winner), inline=False)
        embed.add_field(
            name="Final Score",
            value=f"{self.p1.display_name}: {self.p1_score}
{self.p2.display_name}: {self.p2_score}",
            inline=False)

        await interaction.followup.send(embed=embed)
        self.stop()

    def make_button(self, label, style, choice):
        btn = Button(label=label, style=style)
        async def callback(interaction):
            if interaction.user not in [self.p1, self.p2]:
                return await interaction.response.send_message("Bukan giliran kamu!", ephemeral=True)

            if interaction.user not in self.choices:
                self.choices[interaction.user] = choice
                await interaction.response.send_message(f"Kamu memilih {label}!", ephemeral=True)
                await self.interaction_done(interaction)

        btn.callback = callback
        return btn


# ==========================
#   COMMAND !satusatu
# ==========================
@bot.command()
async def satusatu(ctx, opponent: discord.Member = None, rounds: int = 3):
    if opponent is None:
        return await ctx.send("Gunakan: `!satusatu @user 3` (harus angka ganjil!)")

    if opponent == ctx.author:
        return await ctx.send("Tidak bisa bermain melawan diri sendiri!")

    if rounds % 2 == 0:
        rounds = 1

    view = RPSView(ctx.author, opponent, rounds)

    view.add_item(view.make_button("✊ Batu", discord.ButtonStyle.primary, "✊"))
    view.add_item(view.make_button("✋ Kertas", discord.ButtonStyle.success, "✋"))
    view.add_item(view.make_button("✌️ Gunting", discord.ButtonStyle.danger, "✌️"))

    await ctx.send(
        f"🎮 **Satu Satu Dimulai!**
"
        f"{ctx.author.mention} vs {opponent.mention}
"
        f"Best of **{rounds}** — siapa yang menang duluan **{(rounds//2)+1}** ronde!",
        view=view
    )

# ==========================
#     RUN BOT
# ==========================
bot.run(os.getenv("TOKEN"))
