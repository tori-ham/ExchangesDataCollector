import os
import time
import sqlite3

from controllers.BithumbController import BithumbController
from controllers.CoinoneController import CoinoneController
from controllers.GopaxDataCollector import GopaxDataCollector
from controllers.KorbitController import KorbitController
from controllers.UpbitController import UpbitController

from dotenv import load_dotenv
load_dotenv()

DB_PATH = os.environ.get("DB_PATH")

def createTable():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orderbook(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exchange TEXT,
            symbol TEXT,
            currency TEXT,
            timestamp INTEGER,
            side TEXT,
            price REAL,
            volume REAL,
            UNIQUE(exchange, symbol, currency, timestamp, side, price) ON CONFLICT IGNORE
        )
    """)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    createTable()
    
    symbol = "BTC"
    currency = "KRW"
    
    collectors = [
        BithumbController(symbol, currency),
        CoinoneController(symbol, currency),
        KorbitController(symbol, currency),
        GopaxDataCollector(symbol, currency),
        UpbitController(symbol, currency)
    ]
    
    for c in collectors:
        c.start()
    
    while True:
        time.sleep(1)