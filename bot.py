import discord
from discord.ext import commands
from discord import app_commands
from database import *
from datetime import datetime
import os

TOKEN = os.getenv("TOKEN_BOT_DISCORD")
GUILD_ID = 1331868322710556704

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ======================
# ITEM DROPDOWN
# ======================
ITEM_CHOICES = [
    discord.SelectOption(label=i, value=i) for i in ITEMS
]

# ======================
# MODAL
# ======================
class BrangkasModal(discord.ui.Modal):
    def __init__(self, tipe, items):
        super().__init__(title=f"{tipe} BRANGKAS")
        self.tipe = tipe
        self.items = items

        self.nama = discord.ui.TextInput(label="Nama")
        self.gelar = discord.ui.TextInput(label="Gelar")
        self.jumlahs = []

        self.add_item(self.nama)
        self.add_item(self.gelar)

        for i in range(items):
            jumlah = discord.ui.TextInput(
                label=f"Jumlah Item {i+1}", required=True
            )
            self.jumlahs.append(jumlah)
            self.add_item(jumlah)

    async def on_submit(self, interaction):
        nama = self.nama.value
        gelar = self.gelar.value

        for i, item in enumerate(interaction.data["components"][2:]):
            jumlah = int(self.jumlahs[i].value)
            update_item(self.items_selected[i], jumlah if self.tipe=="DP" else -jumlah)
            add_log(self.tipe, nama, gelar, self.items_selected[i], jumlah)

        await interaction.response.send_message(
            f"✅ {self.tipe} berhasil dicatat", ephemeral=True
        )

# ======================
# DROPDOWN VIEW
# ======================
class ItemSelect(discord.ui.View):
    def __init__(self, tipe, jumlah_item):
        super().__init__(timeout=60)
        self.tipe = tipe
        self.jumlah_item = jumlah_item

        self.select = discord.ui.Select(
            placeholder="Pilih item",
            min_values=jumlah_item,
            max_values=jumlah_item,
            options=ITEM_CHOICES
        )
        self.select.callback = self.callback
        self.add_item(self.select)

    async def callback(self, interaction):
        modal = BrangkasModal(self.tipe, self.jumlah_item)
        modal.items_selected = self.select.values
        await interaction.response.send_modal(modal)

# ======================
# SLASH COMMAND
# ======================
@bot.tree.command(
    name="dpbrangkas",
    description="Deposit brangkas (1-3 item)",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(jumlah_item="Jumlah item (1-3)")
async def dpbrangkas(interaction: discord.Interaction, jumlah_item: int):
    await interaction.response.send_message(
        "Pilih item:",
        view=ItemSelect("DP", jumlah_item),
        ephemeral=True
    )

@bot.tree.command(
    name="wdbrangkas",
    description="Withdraw brangkas (1-3 item)",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(jumlah_item="Jumlah item (1-3)")
async def wdbrangkas(interaction: discord.Interaction, jumlah_item: int):
    await interaction.response.send_message(
        "Pilih item:",
        view=ItemSelect("WD", jumlah_item),
        ephemeral=True
    )

# ======================
# READY
# ======================
@bot.event
async def on_ready():
    init_db()
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
    print("🔥 Bot Brangkas FULL SYSTEM ONLINE")

bot.run(TOKEN)
