import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

from database import init_db, add_log, get_item, set_item, get_meta, set_meta
from items import ITEMS

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ==============================
# GENERATOR EMBED BRANGKAS
# ==============================
def generate_embed():
    embed = discord.Embed(
        title="💎 BRANGKAS EMPEROR",
        description="Status brangkas terkini milik EMPIRE.",
        color=discord.Color.purple()
    )
    embed.set_thumbnail(url="https://i.imgur.com/MYpQnRp.png")  # bisa diganti logo empire

    for kategori, daftar in ITEMS.items():
        text = ""
        for item in daftar:
            jumlah = get_item(item)
            text += f"**{item}**: `{jumlah}`\n"
        embed.add_field(name=f"📦 {kategori}", value=text, inline=False)

    embed.set_footer(text="Update otomatis setiap deposit/withdrawal")
    return embed


# ==============================
# ON READY
# ==============================
@bot.event
async def on_ready():
    print(f"Bot online sebagai {bot.user}")
    try:
        await bot.tree.sync()
        print("Slash command sinkron.")
    except:
        pass


# ==============================
# SETUP BRANGKAS
# ==============================
@bot.command()
async def setupbrangkas(ctx):
    guild = ctx.guild

    category = await guild.create_category("BRANGKAS EMPEROR")

    brangkas = await category.create_text_channel("BRANGKAS EMPEROR")
    log_deposit = await category.create_text_channel("Log Deposit")
    log_withdraw = await category.create_text_channel("Log Withdrawal")
    laporan = await category.create_text_channel("Laporan")

    # kirim embed awal
    msg = await brangkas.send(embed=generate_embed())

    # simpan ID pesan embed untuk update
    set_meta("brangkas_message", str(msg.id))
    set_meta("brangkas_channel", str(brangkas.id))

    await ctx.send("Brangkas EMPEROR berhasil dibuat!")


# ==============================
# FORM & MODAL
# ==============================
class TransactionModal(discord.ui.Modal):
    def __init__(self, item, channel, tipe):
        super().__init__(title=f"Form {tipe.capitalize()}")
        self.item = item
        self.channel = channel
        self.tipe = tipe

        self.nama = discord.ui.TextInput(label="Nama")
        self.gelar = discord.ui.TextInput(label="Gelar")
        self.jumlah = discord.ui.TextInput(label="Jumlah")
        self.keterangan = discord.ui.TextInput(label="Keterangan", style=discord.TextStyle.long)

        self.add_item(self.nama)
        self.add_item(self.gelar)
        self.add_item(self.jumlah)
        self.add_item(self.keterangan)

    async def on_submit(self, interaction):
        jumlah = int(self.jumlah.value)
        now = datetime.now().strftime("%d-%m-%Y %H:%M")

        current = get_item(self.item)

        if self.tipe == "withdrawal":
            if jumlah > current:
                return await interaction.response.send_message(
                    f"❌ Stok `{self.item}` tidak cukup!\nSaat ini tersedia: **{current}**",
                    ephemeral=True
                )
            set_item(self.item, current - jumlah)

        else:  # deposit
            set_item(self.item, current + jumlah)

        # simpan log
        add_log(self.tipe, self.nama.value, self.gelar.value, self.item,
                jumlah, self.keterangan.value, now)

        # kirim ke channel log
        await self.channel.send(
            f"📥 **{self.tipe.capitalize()}**\n"
            f"• Nama: **{self.nama.value}**\n"
            f"• Gelar: **{self.gelar.value}**\n"
            f"• Item: **{self.item}**\n"
            f"• Jumlah: **{jumlah}**\n"
            f"• Ket: {self.keterangan.value}\n"
            f"• Waktu: {now}"
        )

        # update embed brangkas
        msg_id = int(get_meta("brangkas_message"))
        ch_id = int(get_meta("brangkas_channel"))
        channel = interaction.guild.get_channel(ch_id)
        msg = await channel.fetch_message(msg_id)
        await msg.edit(embed=generate_embed())

        await interaction.response.send_message("✔️ Transaksi berhasil!", ephemeral=True)


# ==============================
# DROPDOWN SELECT
# ==============================
class ItemSelect(discord.ui.Select):
    def __init__(self, channel, tipe):
        self.channel = channel
        self.tipe = tipe

        options = []
        for kategori in ITEMS.values():
            for item in kategori:
                options.append(discord.SelectOption(label=item))

        super().__init__(placeholder=f"Pilih item {tipe}…", options=options)

    async def callback(self, interaction):
        modal = TransactionModal(self.values[0], self.channel, self.tipe)
        await interaction.response.send_modal(modal)


class ItemView(discord.ui.View):
    def __init__(self, channel, tipe):
        super().__init__(timeout=None)
        self.add_item(ItemSelect(channel, tipe))


# ==============================
# SLASH COMMAND DP & WD
# ==============================
@bot.tree.command(name="dp", description="Deposit barang ke brangkas")
async def dp(interaction):
    channel = discord.utils.get(interaction.guild.channels, name="Log Deposit")
    await interaction.response.send_message(
        "Silakan pilih item deposit:",
        view=ItemView(channel, "deposit"),
        ephemeral=True
    )


@bot.tree.command(name="wd", description="Withdrawal barang dari brangkas")
async def wd(interaction):
    channel = discord.utils.get(interaction.guild.channels, name="Log Withdrawal")
    await interaction.response.send_message(
        "Silakan pilih item withdrawal:",
        view=ItemView(channel, "withdrawal"),
        ephemeral=True
    )


# ==============================
# RUN BOT
# ==============================
import os
init_db()
bot.run(os.getenv("TOKEN_BOT_DISCORD"))
