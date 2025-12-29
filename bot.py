import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime

TOKEN = os.getenv("TOKEN_BOT_DISCORD")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "brangkas.json"

# ===============================
# DATA AWAL BRANGKAS
# ===============================
DEFAULT_BRANGKAS = {
    "Uang Bersih": 0,
    "Uang Kotor": 0,
    "Revolver Mk2": 0,
    "Desert Eagle": 0,
    "Tech 9": 0,
    "Double Action": 0,
    "Mini SMG": 0,
    "Micro SMG": 0,
    "44 Magnum": 0,
    "38 LC": 0,
    "50 AE": 0,
    "9 MM": 0,
    "Vest": 0,
    "Vest Kecil": 0,
    "Joint": 0,
    "Lockpick": 0,
    "ADV Lockpick": 0,
    "Kecubung pack": 0,
    "weed pack": 0,
    "Mushrom pack": 0,
    "Kecubung": 0,
    "weed": 0,
    "Mushrom": 0
}

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump(DEFAULT_BRANGKAS, f, indent=4)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ===============================
# EMBED BRANGKAS
# ===============================
def brangkas_embed(data):
    embed = discord.Embed(
        title="💎 BRANGKAS EMPEROR",
        description="Status brangkas terkini milik EMPEROR.",
        color=0x9b59b6
    )

    embed.add_field(
        name="📦 UANG",
        value=f"Uang Bersih: {data['Uang Bersih']}\nUang Kotor: {data['Uang Kotor']}",
        inline=False
    )

    embed.add_field(
        name="📦 SENJATA",
        value="\n".join([
            f"Revolver Mk2: {data['Revolver Mk2']}",
            f"Desert Eagle: {data['Desert Eagle']}",
            f"Tech 9: {data['Tech 9']}",
            f"Double Action: {data['Double Action']}",
            f"Mini SMG: {data['Mini SMG']}",
            f"Micro SMG: {data['Micro SMG']}",
        ]),
        inline=False
    )

    embed.add_field(
        name="📦 PELURU",
        value="\n".join([
            f"44 Magnum: {data['44 Magnum']}",
            f"38 LC: {data['38 LC']}",
            f"50 AE: {data['50 AE']}",
            f"9 MM: {data['9 MM']}",
        ]),
        inline=False
    )

    embed.add_field(
        name="📦 ITEM",
        value="\n".join([
            f"Vest: {data['Vest']}",
            f"Vest Kecil: {data['Vest Kecil']}",
            f"Joint: {data['Joint']}",
            f"Lockpick: {data['Lockpick']}",
            f"ADV Lockpick: {data['ADV Lockpick']}",
            f"Kecubung pack: {data['Kecubung pack']}",
            f"weed pack: {data['weed pack']}",
            f"Mushrom pack: {data['Mushrom pack']}",
            f"Kecubung: {data['Kecubung']}",
            f"weed: {data['weed']}",
            f"Mushrom: {data['Mushrom']}",
        ]),
        inline=False
    )
    return embed

# ===============================
# SETUP CHANNEL
# ===============================
@bot.command()
@commands.has_permissions(administrator=True)
async def setupbrangkas(ctx):
    guild = ctx.guild

    category = await guild.create_category("BOT LAPORAN BRANGKAS")
    brangkas = await guild.create_text_channel("brangkas", category=category)
    dp = await guild.create_text_channel("laporan-deposit", category=category)
    wd = await guild.create_text_channel("laporan-withdrawal", category=category)

    data = load_data()
    embed = brangkas_embed(data)
    msg = await brangkas.send(embed=embed)
    await msg.pin()

    await ctx.send("✅ Channel brangkas berhasil dibuat!")

# ===============================
# UPDATE BRANGKAS MESSAGE
# ===============================
async def update_brangkas(guild):
    data = load_data()
    channel = discord.utils.get(guild.text_channels, name="brangkas")
    if not channel:
        return
    pinned = await channel.pins()
    await pinned[0].edit(embed=brangkas_embed(data))

# ===============================
# DEPOSIT & WITHDRAW FUNCTION
# ===============================
async def proses(interaction, tipe, items):
    data = load_data()
    waktu = datetime.now().strftime("%d-%m-%Y | %H:%M")

    channel_name = "laporan-deposit" if tipe == "DP" else "laporan-withdrawal"
    channel = discord.utils.get(interaction.guild.text_channels, name=channel_name)

    desc = []
    for item, jumlah in items:
        if item not in data:
            await interaction.response.send_message(f"❌ Item `{item}` tidak valid!", ephemeral=True)
            return
        data[item] += jumlah if tipe == "DP" else -jumlah
        desc.append(f"{item} : {jumlah}")

    save_data(data)
    await update_brangkas(interaction.guild)

    embed = discord.Embed(
        title=f"📥 DEPOSIT BRANGKAS" if tipe == "DP" else "📤 WITHDRAW BRANGKAS",
        color=0x2ecc71 if tipe == "DP" else 0xe74c3c
    )
    embed.add_field(name="Detail", value="\n".join(desc), inline=False)
    embed.set_footer(text=f"{interaction.user} | {waktu}")

    await channel.send(embed=embed)
    await interaction.response.send_message("✅ Data berhasil dicatat!", ephemeral=True)

# ===============================
# SLASH COMMAND (CONTOH 1 ITEM)
# ===============================
@bot.tree.command(name="dpbrangkas")
async def dpbrangkas(interaction: discord.Interaction, item: str, jumlah: int):
    await proses(interaction, "DP", [(item, jumlah)])

@bot.tree.command(name="wdbrangkas")
async def wdbrangkas(interaction: discord.Interaction, item: str, jumlah: int):
    await proses(interaction, "WD", [(item, jumlah)])

# ===============================
# READY
# ===============================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print("Bot Brangkas Emperor Online!")

bot.run(TOKEN)
