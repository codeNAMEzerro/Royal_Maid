import discord
from discord.ext import commands
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
# GENERATE BRANGKAS EMBED
# ======================================================
def generate_embed():
    embed = discord.Embed(
        title="💎 BRANGKAS EMPEROR",
        description="Status brangkas keluarga EMPIRE.\nSemua data diperbarui otomatis.",
        color=discord.Color.purple()
    )

    embed.set_thumbnail(url="https://i.imgur.com/h6Atb5T.png")

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
# EVENT: BOT SIAP
# ======================================================
@bot.event
async def on_ready():
    print(f"Bot online sebagai {bot.user}")
    await bot.tree.sync()
    print("Slash commands synced.")


# ======================================================
# COMMAND: SETUP BRANGKAS
# ======================================================
@bot.command()
async def setupbrangkas(ctx):
    guild = ctx.guild

    category = await guild.create_category("BRANGKAS EMPEROR")
    ch_brangkas = await category.create_text_channel("BRANGKAS EMPEROR")
    await category.create_text_channel("Log Deposit")
    await category.create_text_channel("Log Withdrawal")
    await category.create_text_channel("Laporan")

    msg = await ch_brangkas.send(embed=generate_embed())

    set_meta("brangkas_message", str(msg.id))
    set_meta("brangkas_channel", str(ch_brangkas.id))

    await ctx.send("✔ Brangkas EMPEROR siap dipakai!")


# ======================================================
# VIEW PEMILIHAN AWAL (DEPOSIT / WITHDRAW)
# ======================================================
class MaidSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Deposit", emoji="📥"),
            discord.SelectOption(label="Withdrawal", emoji="📤")
        ]

        super().__init__(
            placeholder="Pilih layanan...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction):
        tipe = "deposit" if self.values[0] == "Deposit" else "withdrawal"
        await interaction.response.send_modal(MaidNameModal(tipe))


class MaidView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(MaidSelect())


# ======================================================
# MODAL STEP 1: NAMA
# ======================================================
class MaidNameModal(discord.ui.Modal):
    def __init__(self, tipe):
        super().__init__(title="✨ EMPEROR MAID — Nama")
        self.tipe = tipe

        self.nama = discord.ui.TextInput(
            label="Nama",
            placeholder="Masukkan nama",
            required=True,
            max_length=50
        )
        self.add_item(self.nama)

    async def on_submit(self, interaction):
        await interaction.response.send_modal(
            MaidGelarModal(self.tipe, self.nama.value)
        )


# ======================================================
# MODAL STEP 2: GELAR
# ======================================================
class MaidGelarModal(discord.ui.Modal):
    def __init__(self, tipe, nama):
        super().__init__(title="✨ EMPEROR MAID — Gelar")
        self.tipe = tipe
        self.nama = nama

        self.gelar = discord.ui.TextInput(label="Gelar")
        self.add_item(self.gelar)

    async def on_submit(self, interaction):
        await interaction.response.send_message(
            "Pilih item yang akan diproses:",
            view=ItemSelectView(self.tipe, self.nama, self.gelar.value),
            ephemeral=True
        )


# ======================================================
# MEMILIH ITEM
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

        super().__init__(placeholder="Pilih item...", options=options)

    async def callback(self, interaction):
        await interaction.response.send_modal(
            MaidJumlahModal(
                self.tipe, self.nama, self.gelar, self.values[0]
            )
        )


class ItemSelectView(discord.ui.View):
    def __init__(self, tipe, nama, gelar):
        super().__init__(timeout=None)
        self.add_item(ItemSelect(tipe, nama, gelar))


# ======================================================
# JUMLAH
# ======================================================
class MaidJumlahModal(discord.ui.Modal):
    def __init__(self, tipe, nama, gelar, item):
        super().__init__(title="✨ EMPEROR MAID — Jumlah")
        self.tipe = tipe
        self.nama = nama
        self.gelar = gelar
        self.item = item

        self.jumlah = discord.ui.TextInput(label="Jumlah")
        self.add_item(self.jumlah)

    async def on_submit(self, interaction):
        await interaction.response.send_modal(
            MaidKetModal(
                self.tipe, self.nama, self.gelar,
                self.item, int(self.jumlah.value)
            )
        )


# ======================================================
# MODAL TERAKHIR: KETERANGAN
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
        guild = interaction.guild

        log_ch = discord.utils.get(
            guild.channels,
            name="Log Deposit" if self.tipe == "deposit" else "Log Withdrawal"
        )

        # CEK STOK UNTUK WD
        current = get_item(self.item)
        if self.tipe == "withdrawal" and self.jumlah > current:
            return await interaction.response.send_message(
                f"❌ Stok `{self.item}` tidak cukup!\nSaat ini: `{current}`",
                ephemeral=True
            )

        # SIMPAN PERUBAHAN INVENTORY
        if self.tipe == "deposit":
            set_item(self.item, current + self.jumlah)
        else:
            set_item(self.item, current - self.jumlah)

        # SIMPAN LOG
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

        # UPDATE EMBED BRANGKAS
        msg_id = int(get_meta("brangkas_message"))
        ch_id = int(get_meta("brangkas_channel"))
        ch = guild.get_channel(ch_id)
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
    embed.set_thumbnail(url="https://i.imgur.com/h6Atb5T.png")
    await ctx.send(embed=embed, view=MaidView())


# ======================================================
# RUN BOT
# ======================================================
init_db()
bot.run(os.getenv("TOKEN_BOT_DISCORD"))
