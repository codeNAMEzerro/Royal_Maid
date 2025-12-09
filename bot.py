import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import os

from database import (
    init_db, add_log, get_item,
    set_item, get_meta, set_meta
)
from items import ITEMS

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


# ======================================================
# GENERATOR EMBED BRANGKAS
# ======================================================
def generate_embed():
    embed = discord.Embed(
        title="💎 BRANGKAS EMPEROR",
        description="Status brangkas keluarga EMPIRE.\nSemua data diperbarui secara otomatis.",
        color=discord.Color.purple()
    )

    embed.set_thumbnail(url="https://i.imgur.com/h6Atb5T.png")  # avatar maid cantik

    for kategori, daftar in ITEMS.items():
        teks = ""
        for item in daftar:
            jumlah = get_item(item)
            teks += f"**{item}** : `{jumlah}`\n"
        embed.add_field(
            name=f"👑 {kategori}",
            value=teks,
            inline=False
        )

    embed.set_footer(text="EMPEROR MAID Auto-Update System")
    return embed


# ======================================================
# ON READY
# ======================================================
@bot.event
async def on_ready():
    print(f"Bot online sebagai {bot.user}")
    try:
        await bot.tree.sync()
        print("Slash commands synced.")
    except:
        pass


# ======================================================
# SETUP BRANGKAS
# ======================================================
@bot.command()
async def setupbrangkas(ctx):
    guild = ctx.guild

    category = await guild.create_category("BRANGKAS EMPEROR")

    ch_brangkas = await category.create_text_channel("BRANGKAS EMPEROR")
    ch_dp = await category.create_text_channel("Log Deposit")
    ch_wd = await category.create_text_channel("Log Withdrawal")
    laporan = await category.create_text_channel("Laporan")

    msg = await ch_brangkas.send(embed=generate_embed())

    set_meta("brangkas_message", str(msg.id))
    set_meta("brangkas_channel", str(ch_brangkas.id))

    await ctx.send("Brangkas EMPEROR siap dipakai!")


# ======================================================
# CLASS VIEW -> PILIHAN AWAL (DEPOSIT/WITHDRAWAL)
# ======================================================
class MaidSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Deposit", emoji="📥"),
            discord.SelectOption(label="Withdrawal", emoji="📤")
        ]

        super().__init__(
            placeholder="Pilih layanan yang kamu perlukan...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        pilihan = self.values[0]

        if pilihan == "Deposit":
            await interaction.response.send_modal(MaidNameModal("deposit"))
        else:
            await interaction.response.send_modal(MaidNameModal("withdrawal"))


class MaidView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MaidSelect())


# ======================================================
# STEP 1 — NAMA
# ======================================================
class MaidNameModal(discord.ui.Modal):
    def __init__(self, tipe):
        super().__init__(title="✨ EMPEROR MAID — Input Nama")
        self.tipe = tipe
        self.nama = discord.ui.TextInput(label="Nama", placeholder="Masukkan nama...")
        self.add_item(self.nama)

    async def on_submit(self, interaction):
        await interaction.response.send_modal(MaidGelarModal(self.tipe, self.nama.value))


# ======================================================
# STEP 2 — GELAR
# ======================================================
class MaidGelarModal(discord.ui.Modal):
    def __init__(self, tipe, nama):
        super().__init__(title="✨ EMPEROR MAID — Input Gelar")
        self.tipe = tipe
        self.nama = nama
        self.gelar = discord.ui.TextInput(label="Gelar", placeholder="Masukkan gelar...")
        self.add_item(self.gelar)

    async def on_submit(self, interaction):
        await interaction.response.send_message(
            "Pilih item:",
            view=ItemSelectView(self.tipe, self.nama, self.gelar.value),
            ephemeral=True
        )


# ======================================================
# STEP 3 — PILIH ITEM
# ======================================================
class ItemSelect(discord.ui.Select):
    def __init__(self, tipe, nama, gelar):
        self.tipe = tipe
        self.nama = nama
        self.gelar = gelar

        options = []
        for kategori in ITEMS.values():
            for item in kategori:
                options.append(discord.SelectOption(label=item))

        super().__init__(
            placeholder="Pilih item...",
            options=options
        )

    async def callback(self, interaction):
        await interaction.response.send_modal(
            MaidJumlahModal(self.tipe, self.nama, self.gelar, self.values[0])
        )


class ItemSelectView(discord.ui.View):
    def __init__(self, tipe, nama, gelar):
        super().__init__(timeout=None)
        self.add_item(ItemSelect(tipe, nama, gelar))


# ======================================================
# STEP 4 — JUMLAH
# ======================================================
class MaidJumlahModal(discord.ui.Modal):
    def __init__(self, tipe, nama, gelar, item):
        super().__init__(title="✨ EMPEROR MAID — Jumlah")
        self.tipe = tipe
        self.nama = nama
        self.gelar = gelar
        self.item = item

        self.jumlah = discord.ui.TextInput(label="Jumlah", placeholder="Masukkan angka...")
        self.add_item(self.jumlah)

    async def on_submit(self, interaction):
        await interaction.response.send_modal(
            MaidKetModal(
                self.tipe,
                self.nama, self.gelar,
                self.item, int(self.jumlah.value)
            )
        )


# ======================================================
# STEP 5 — KETERANGAN
# ======================================================
class MaidKetModal(discord.ui.Modal):
    def __init__(self, tipe, nama, gelar, item, jumlah):
        super().__init__(title="✨ EMPEROR MAID — Keterangan")
        self.tipe = tipe
        self.nama = nama
        self.gelar = gelar
        self.item = item
        self.jumlah = jumlah

        self.ket = discord.ui.TextInput(label="Keterangan", style=discord.TextStyle.long)
        self.add_item(self.ket)

    async def on_submit(self, interaction):
        now = datetime.now().strftime("%d-%m-%Y %H:%M")

        # CHANNEL LOG
        if self.tipe == "deposit":
            log_ch = discord.utils.get(interaction.guild.channels, name="Log Deposit")
        else:
            log_ch = discord.utils.get(interaction.guild.channels, name="Log Withdrawal")

        # CEK STOK SDA WD
        current = get_item(self.item)

        if self.tipe == "withdrawal" and self.jumlah > current:
            return await interaction.response.send_message(
                f"❌ Stok `{self.item}` tidak cukup!\nSaat ini tersedia: `{current}`",
                ephemeral=True
            )

        # SIMPAN DATABASE
        if self.tipe == "deposit":
            set_item(self.item, current + self.jumlah)
        else:
            set_item(self.item, current - self.jumlah)

        add_log(
            self.tipe, self.nama, self.gelar,
            self.item, self.jumlah,
            self.ket.value, now
        )

        # KIRIM LOG
        await log_ch.send(
            f"✨ **{self.tipe.capitalize()}**\n"
            f"• Nama: **{self.nama}**\n"
            f"• Gelar: **{self.gelar}**\n"
            f"• Item: **{self.item}**\n"
            f"• Jumlah: `{self.jumlah}`\n"
            f"• Ket: {self.ket.value}\n"
            f"• Waktu: {now}"
        )

        # UPDATE BRANGKAS
        msg_id = int(get_meta("brangkas_message"))
        ch_id = int(get_meta("brangkas_channel"))
        ch = interaction.guild.get_channel(ch_id)
        msg = await ch.fetch_message(msg_id)
        await msg.edit(embed=generate_embed())

        await interaction.response.send_message("✔️ Transaksi selesai!", ephemeral=True)


# ======================================================
# COMMAND !maid
# ======================================================
@bot.command()
async def maid(ctx):
    embed = discord.Embed(
        title="🤍 EMPEROR MAID — Service Panel",
        description="Ada yang bisa ku bantu hari ini?\nSilakan pilih layanan di bawah ini.",
        color=discord.Color.purple()
    )
    embed.set_thumbnail(url="https://i.imgur.com/h6Atb5T.png")  # avatar maid cantik
    await ctx.send(embed=embed, view=MaidView())


# ======================================================
# RUN BOT
# ======================================================
init_db()
bot.run(os.getenv("TOKEN_BOT_DISCORD"))
