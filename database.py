import sqlite3

def init_db():
    conn = sqlite3.connect("brangkas.db")
    cur = conn.cursor()

    # Log transaksi
    cur.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            nama TEXT,
            gelar TEXT,
            item TEXT,
            jumlah INTEGER,
            keterangan TEXT,
            timestamp TEXT
        )
    """)

    # Inventory jumlah item
    cur.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            item TEXT PRIMARY KEY,
            jumlah INTEGER DEFAULT 0
        )
    """)

    # Menyimpan ID pesan brangkas
    cur.execute("""
        CREATE TABLE IF NOT EXISTS meta (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    conn.commit()
    conn.close()


def add_log(type, nama, gelar, item, jumlah, ket, ts):
    conn = sqlite3.connect("brangkas.db")
    conn.execute("""
        INSERT INTO logs (type,nama,gelar,item,jumlah,keterangan,timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (type, nama, gelar, item, jumlah, ket, ts))
    conn.commit()
    conn.close()


def get_item(item):
    conn = sqlite3.connect("brangkas.db")
    cur = conn.execute("SELECT jumlah FROM inventory WHERE item = ?", (item,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else 0


def set_item(item, jumlah):
    conn = sqlite3.connect("brangkas.db")
    conn.execute("""
        INSERT INTO inventory (item, jumlah)
        VALUES (?, ?)
        ON CONFLICT(item)
        DO UPDATE SET jumlah = excluded.jumlah
    """, (item, jumlah))
    conn.commit()
    conn.close()


def set_meta(key, value):
    conn = sqlite3.connect("brangkas.db")
    conn.execute("""
        INSERT INTO meta (key, value)
        VALUES (?, ?)
        ON CONFLICT(key)
        DO UPDATE SET value = excluded.value
    """, (key, value))
    conn.commit()
    conn.close()


def get_meta(key):
    conn = sqlite3.connect("brangkas.db")
    cur = conn.execute("SELECT value FROM meta WHERE key = ?", (key,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None
