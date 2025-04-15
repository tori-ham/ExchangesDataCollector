import os
import traceback
import sqlite3
import websocket
import threading
import time
import json
from abc import ABC, abstractmethod

from dotenv import load_dotenv

import sqlite3
from log_util import getLogger

load_dotenv()

DB_PATH = os.environ.get("DB_PATH")

class WSController(ABC):
    def __init__(self, symbol, currency):
        self.symbol = symbol.upper()
        self.currency = currency.upper()
        self.wsUrl = self.getWSUrl()
        self.wsApp = websocket.WebSocketApp(
            self.wsUrl,
            on_open = self.onConnect,
            on_message = self.onMessage,
            on_close = self.onClose,
            on_error = self.onError
        )
        self.t = None
        self.conn = None
        self.logger = getLogger(f"[{self.getName()} / {symbol}-{currency}]")
    
    def start(self):
        if not self.t or not self.t.is_alive():
            self.conn = sqlite3.connect(
                DB_PATH,
                check_same_thread = False
            )
        
            self.t = threading.Thread(
                target = self.wsApp.run_forever,
                daemon = True
            )
            self.t.start()
    def stop(self):
        if self.t:
            self.wsApp.keep_running = False
            self.t.join()
            self.conn.close()
        
    def onConnect(self, ws):
        print(f"[{self.getName()}] Connected")
        self.logger.info(f"WebSocket 연결 성공")
        msg = self.getMessage()
        ws.send(msg)
    
    def onMessage(self, ws, msg):
        try:
            parsed_msg_result, err_msg = self.handleMessage(msg)
            if not parsed_msg_result:
                self.logger.error(f"Error in handleMessage : {err_msg}")
        except Exception as e:
            print(f"[{self.getName()}] Error : {e}")
            self.logger.error(f"Unexpectec Error : {e}")
    
    def onClose(self, ws, status, msg):
        print(f"[{self.getName()}] Closed")
        self.logger.info(f"WebSocket 연걸 종료")
    
    def onError(self, ws, err):
        traceback.print_exc()
        print(f"[{self.getName()}] Error: {err}")
    
    def saveDataToDB(self, data):
        cur = self.conn.cursor()
        cur.executemany(
            """
                INSERT INTO orderbook(exchange, symbol, currency, timestamp, side, price, volume) VALUES (:exchange, :symbol, :currency, :timestamp, :side, :price, :volume)
            """, 
            data
        )
        self.conn.commit()
    
    def getDBPath(self):
        pass
    @abstractmethod
    def getName(self):
        pass
    @abstractmethod
    def getWSUrl(self):
        pass
    @abstractmethod
    def getMessage(self):
        pass
    @abstractmethod
    def handleMessage(self, message):
        pass