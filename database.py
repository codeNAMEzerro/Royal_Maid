import mysql.connector
import os

db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASS"),
    database=os.getenv("DB_NAME")
)

cursor = db.cursor(dictionary=True)

ITEMS = [
    "Uang Bersih","Uang Kotor",
    "Revolver Mk2","Desert Eagle","Tech 9","Double Action",
    "Mini SMG","Micro SMG",
    "44 Magnum","38 LC","50 AE","9 MM",
    "Vest","Vest Kecil","Joint","Lockpick","ADV Lockpick",
    "Kecubung pack","weed pack","Mushrom pack",
    "Kecubung","weed","Mushrom"
]

def init_db():
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS brangkas (
            item VARCHAR(50) PRIMARY KEY,
            jumlah INT DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            tipe VARCHAR(10),
            nama VARCHAR(50),
            gelar VARCHAR(50),
            item VARCHAR(50),
            jumlah INT,
            waktu DATETIME
        )
    """)
    for item in ITEMS:
        cursor.execute(
            "INSERT IGNORE INTO brangkas (item, jumlah) VALUES (%s,0)", (item,)
        )
    db.commit()

def get_item(item):
    cursor.execute("SELECT jumlah FROM brangkas WHERE item=%s", (item,))
    return cursor.fetchone()["jumlah"]

def update_item(item, jumlah):
    cursor.execute(
        "UPDATE brangkas SET jumlah = jumlah + %s WHERE item=%s",
        (jumlah, item)
    )
    db.commit()

def add_log(tipe, nama, gelar, item, jumlah):
    cursor.execute(
        "INSERT INTO logs (tipe,nama,gelar,item,jumlah,waktu) VALUES (%s,%s,%s,%s,%s,NOW())",
        (tipe,nama,gelar,item,jumlah)
    )
    db.commit()
