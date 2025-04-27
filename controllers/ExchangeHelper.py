import sqlite3 
import os
from dotenv import load_dotenv
from datetime import datetime, UTC
from utils.utils import bindColumn

load_dotenv()
DB_PATH = os.environ.get("DB_PATH")

class ExchangeHelper:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread = False)
        self.createExchangeTable()
    def createExchangeTable(self):
        query = """
            create table if not exists exchanges(
                id integer primary key autoincrement,
                name text not null,
                ws_url text not null,
                message text not null,
                handle_message_func text not null,
                is_visible boolean not null default 1,
                updated_at text
            )
        """
        cur = self.conn.cursor()
        cur.execute(query)
        self.conn.commit()
    
    def addExchange(
        self,
        name,
        wsUrl,
        message,
        handleMessageFunc
    ):
        now = datetime.now(UTC)
        query = """
            insert into exchanges(name,  ws_url, message, handle_message_func, updated_at) values (?, ?, ?, ?, ?)
        """
        cur = self.conn.cursor()
        cur.execute(
            query, (
                name,
                wsUrl,
                message,
                handleMessageFunc,
                now
            )
        )
        self.conn.commit()
    def removeExchange(
        self,
        exchangeId
    ):
        now = datetime.now(UTC)
        query = """
            update exchanges set is_visible = 0 where id=?
        """
        cur = self.conn.cursor()
        cur.execute( query, (id,) )
        self.conn.commit()
    def exchangesList(self):
        query = """
            select * from exchanges where is_visible = 1 order by updated_at desc
        """
        cur = self.conn.cursor()
        cur.execute(query)
        res = bindColumn(cur)
        return res
    def close(self):
        self.conn.close()
        