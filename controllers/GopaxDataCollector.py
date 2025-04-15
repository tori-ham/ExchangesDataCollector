import os
import time
import base64
import hmac
import hashlib
import json
import threading
import sqlite3
import traceback

from urllib.parse import quote
from websocket import create_connection

from log_util import getLogger

DB_PATH = os.environ.get("DB_PATH")
GOPAX_API_KEY = os.environ.get("GOPAX_API_KEY")
GOPAX_SECRET_KEY = os.environ.get("GOPAX_SECRET_KEY")


class GopaxDataCollector:
    def __init__(self, symbol, currency):
        self.symbol = symbol.upper()
        self.currency = currency.upper()
        self.wsConnection = None
        self.wsRunning = False
        self.t = None
        self.conn = None
        self.logger = getLogger(f"[GOPAX / {symbol}-{currency}]")
    
    def _generate_signed_url(self):
        timestamp = str( int( time.time() * 1000 ) )
        msg = 't' + timestamp
        key = base64.b64decode(GOPAX_SECRET_KEY)
        signature = base64.b64encode(
            hmac.new(
                key, 
                str(msg).encode('utf-8'), 
                hashlib.sha512
            ).digest()
        ).decode()
        url = 'wss://wsapi.gopax.co.kr?apiKey={}&timestamp={}&signature={}'
        return url.format(
            quote( GOPAX_API_KEY ),
            timestamp,
            quote(signature)
        )
    
    def connect(self):
        url = self._generate_signed_url()
        self.wsConnection = create_connection( url, timeout = 10 )
        self.wsConnection.settimeout(None)
        
        reqMessage = {
            'i' : 1,
            'n' : 'SubscribeToOrderBook',
            'o' : { 'tradingPairName' : f'{self.symbol}-{self.currency}' }
        }
        self.wsConnection.send( json.dumps(reqMessage) )
        self.wsRunning = True
        self.logger.info(f"WebSocket 연결 성공 {self.symbol}-{self.currency}")
        
    def listen(self):
        while self.wsRunning:
            try:
                raw_message = self.wsConnection.recv()
                if raw_message.startswith('"primus::ping::'):
                    pong = '"primus::pong::' + raw_message[15:]
                    self.wsConnection.send(pong)
                else:
                    data = json.loads(raw_message)
                    handle_result, err_msg = self.handleMessage(data)
                    
                    if not handle_result:
                        self.logger.error(f"Error in handleMessage : {err_msg}")
            except Exception as e:
                traceback.print_exc()
                print(f"[GOPAX] Error : {e}")
                self.logger.error(f"Unexpected Error : {e}")
    
    def handleMessage(self, message):
        try:
            data = message["o"]
        
            if "ask" in data and "bid" in data:
                results = []
                
                [symbol, currency] = data["tradingPairName"].split("-")
                
                if len(data["ask"]) > 0:
                    for unit in data["ask"]:
                        timestamp = int( unit["updatedAt"] * 1000 )
                        results.append(
                            {
                                "exchange" : "GOPAX",
                                "symbol" : symbol,
                                "currency" : currency,
                                "timestamp" : timestamp,
                                "side" : "ask",
                                "price" : unit["price"],
                                "volume" : unit["volume"]
                            }
                        )
                if len(data["bid"]) > 0:
                    for unit in data["bid"]:
                        timestamp = int( unit["updatedAt"] * 1000 )
                        results.append(
                            {
                                "exchange" : "GOPAX",
                                "symbol" : symbol,
                                "currency" : currency,
                                "timestamp" : timestamp,
                                "side" : "bid",
                                "price" : unit["price"],
                                "volume" : unit["volume"]
                            }
                        )
                if len(results) > 0:
                    self.saveDataToDB(results)
        except Exception as e:
            return False, e
        return True, None
    
    def saveDataToDB(self, data):
        cur = self.conn.cursor()
        cur.executemany(
            """
                INSERT INTO orderbook(exchange, symbol, currency, timestamp, side, price, volume) VALUES (:exchange, :symbol, :currency, :timestamp, :side, :price, :volume)
            """, 
            data
        )
        self.conn.commit()
    
    def start(self):
        if not self.t or not self.t.is_alive():
            self.conn = sqlite3.connect(
                DB_PATH,
                check_same_thread = False
            )
            
            print("[GOPAX] Try to Connect ")
            self.logger.info(f"WebSocket 연결 시도")
            self.connect()
            self.t = threading.Thread(target = self.listen, daemon = True)
            self.t.start()
    def stop(self):
        if self.t:
            self.t.join()
            self.conn.close()
            self.logger.info(f"WebSocket 연결 종료")