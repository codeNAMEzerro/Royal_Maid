import discord
from discord.ext import commands
from discord import app_commands
from database import *
import os

TOKEN = os.getenv("TOKEN_BOT_DISCORD")
GUILD_ID = 1331868322710556704

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ==========================
# MODAL
# ==========================
class BrangkasModal(discord.ui.Modal):
    def __init__(self, tipe, item):
        super().__init__(title="Form Brangkas")
        self.tipe = tipe
        self.item = item

        self.nama = discord.ui.TextInput(label="Nama")
        self.gelar = discord.ui.TextInput(label="Gelar")
        self.jumlah = discord.ui.TextInput(label="Jumlah", placeholder="Contoh: 10")

        self.add_item(self.nama)
        self.add_item(self.gelar)
        self.add_item(self.jumlah)

    async def on_submit(self, interaction: discord.Interaction):
        jumlah = int(self.jumlah.value)
        update_item(self.item, jumlah if self.tipe == "DP" else -jumlah)
        add_log(self.tipe, self.nama.value, self.gelar.value, self.item, jumlah)

        await interaction.response.send_message(
            f"✅ {self.tipe} **{self.item}** sebanyak **{jumlah}** berhasil dicatat.",
            ephemeral=True
        )

# ==========================
# DROPDOWN VIEW
# ==========================
class BrangkasView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

        self.tipe = discord.ui.Select(
            placeholder="Pilih Jenis (DP / WD)",
            options=[
                discord.SelectOption(label="Deposit", value="DP"),
                discord.SelectOption(label="Withdraw", value="WD"),
            ]
        )

        self.item = discord.ui.Select(
            placeholder="Pilih Item",
            options=[discord.SelectOption(label=i, value=i) for i in ITEMS]
        )

        self.tipe.callback = self.select_callback
        self.item.callback = self.select_callback

        self.add_item(self.tipe)
        self.add_item(self.item)

    async def select_callback(self, interaction: discord.Interaction):
        if not self.tipe.values or not self.item.values:
            return

        modal = BrangkasModal(self.tipe.values[0], self.item.values[0])
        await interaction.response.send_modal(modal)

# ==========================
# SLASH COMMAND
# ==========================
@bot.tree.command(
    name="botbrangkas",
    description="Form brangkas (DP / WD)",
    guild=discord.Object(id=GUILD_ID)
)
async def botbrangkas(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Silakan isi data brangkas:",
        view=BrangkasView(),
        ephemeral=True
    )

# ==========================
# READY
# ==========================
@bot.event
async def on_ready():
    init_db()
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    print("✅ Bot Brangkas Popup Online")

bot.run(TOKEN)
