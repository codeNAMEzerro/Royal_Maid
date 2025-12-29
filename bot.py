import discord
from discord.ext import commands
import json
import os
from datetime import datetime

# ===============================
# KONFIGURASI
# ===============================
TOKEN = os.getenv("TOKEN_BOT_DISCORD")
GUILD_ID = 1331868322710556704
DATA_FILE = "brangkas.json"

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

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

# ===============================
# FILE HANDLER
# ===============================
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
# SETUP CHANNEL (PREFIX)
# ===============================
@bot.command()
@commands.has_permissions(administrator=True)
async def setupbrangkas(ctx):
    guild = ctx.guild

    category = await guild.create_category("BOT LAPORAN BRANGKAS")
    brangkas = await guild.create_text_channel("brangkas", category=category)
    await guild.create_text_channel("laporan-deposit", category=category)
    await guild.create_text_channel("laporan-withdrawal", category=category)

    data = load_data()
    msg = await brangkas.send(embed=brangkas_embed(data))
    await msg.pin()

    await ctx.send("✅ Channel brangkas berhasil dibuat!")

# ===============================
# UPDATE BRANGKAS
# ===============================
async def update_brangkas(guild):
    channel = discord.utils.get(guild.text_channels, name="brangkas")
    if not channel:
        return
    pins = await channel.pins()
    if not pins:
        return
    await pins[0].edit(embed=brangkas_embed(load_data()))

# ===============================
# PROSES DP / WD
# ===============================
async def proses(interaction, tipe, items):
    data = load_data()
    waktu = datetime.now().strftime("%d-%m-%Y | %H:%M")

    channel_name = "laporan-deposit" if tipe == "DP" else "laporan-withdrawal"
    channel = discord.utils.get(interaction.guild.text_channels, name=channel_name)

    desc = []
    for item, jumlah in items:
        if item not in data:
            await interaction.response.send_message(
                f"❌ Item `{item}` tidak tersedia di brangkas!",
                ephemeral=True
            )
            return
        data[item] += jumlah if tipe == "DP" else -jumlah
        desc.append(f"{item} : {jumlah}")

    save_data(data)
    await update_brangkas(interaction.guild)

    embed = discord.Embed(
        title="📥 DEPOSIT BRANGKAS" if tipe == "DP" else "📤 WITHDRAW BRANGKAS",
        color=0x2ecc71 if tipe == "DP" else 0xe74c3c
    )
    embed.add_field(name="Detail", value="\n".join(desc), inline=False)
    embed.set_footer(text=f"{interaction.user} | {waktu}")

    await channel.send(embed=embed)
    await interaction.response.send_message("✅ Berhasil dicatat.", ephemeral=True)

# ===============================
# SLASH COMMAND (GUILD)
# ===============================
@bot.tree.command(
    name="dpbrangkas",
    description="Deposit item ke brangkas",
    guild=discord.Object(id=GUILD_ID)
)
async def dpbrangkas(interaction: discord.Interaction, item: str, jumlah: int):
    await proses(interaction, "DP", [(item, jumlah)])

@bot.tree.command(
    name="wdbrangkas",
    description="Withdraw item dari brangkas",
    guild=discord.Object(id=GUILD_ID)
)
async def wdbrangkas(interaction: discord.Interaction, item: str, jumlah: int):
    await proses(interaction, "WD", [(item, jumlah)])

# ===============================
# READY
# ===============================
@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    await bot.tree.sync(guild=guild)
    print("✅ Bot Brangkas Emperor ONLINE (Slash Command Aktif)")

bot.run(TOKEN)
