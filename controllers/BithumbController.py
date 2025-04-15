import os
import traceback
from dotenv import load_dotenv
import threading
import time
import requests
import sqlite3

from log_util import getLogger

load_dotenv()

DB_PATH = os.environ.get("DB_PATH")

class BithumbController:
    def __init__(self, symbol, currency):
        self.symbol = symbol
        self.currency = currency
        self.endpoint = f"https://api.bithumb.com/v1/orderbook?markets={currency.upper()}-{symbol.upper()}"
        self.running = False
        self.interval = 0.1
        self.session = requests.Session()
        self.t = None
        self.conn = None
        self.logger = getLogger(f"[BITHUMB / {symbol}-{currency}]")
    
    def handleMessage(self, message):
        try:
            total_results = []
            for dataItem in message:
                results = []
                
                if not "market" in dataItem:
                    continue
                [ currency, symbol ] = dataItem["market"].split("-")
                timestamp = dataItem["timestamp"]
                for unit in dataItem["orderbook_units"]:
                    results.append(
                        {
                            "exchange" : "BITHUMB",
                            "symbol" : symbol,
                            "currency" : currency,
                            "timestamp" : timestamp,
                            "side" : "ask",
                            "price" : unit["ask_price"],
                            "volume" : unit["ask_size"]
                        }
                    )
                    results.append(
                        {
                            "exchange" : "BITHUMB",
                            "symbol" : symbol,
                            "currency" : currency,
                            "timestamp" : timestamp,
                            "side" : "bid",
                            "price" : unit["bid_price"],
                            "volume" : unit["bid_size"]
                        }
                    )
                total_results.extend(results)
            if len(total_results) > 0:
                self.saveDataToDB(total_results)
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
    
    def getOrderbookData(self):
        try:
            response = self.session.get( self.endpoint )
            if response.status_code == 200:
                data = response.json()
                handle_result, err_msg = self.handleMessage(data)
                if not handle_result:
                    self.logger.error(f"Error in handleMessage {self.symbol}-{self.currency} : {err_msg}")
            else:
                print(f"[BITHUMB] API Error : {response.status_code}")
        except Exception as err:
            traceback.print_exc()
            print(f"[BITHUMB] Error : {err}")
            self.logger.error(f"Error from API : {err}")
    
    def loop(self):
        while self.running:
            self.getOrderbookData()
            time.sleep(self.interval)
    
    def start(self):
        if not self.t or not self.t.is_alive():
            self.conn = sqlite3.connect(
                DB_PATH,
                check_same_thread = False
            )
            
            print("[BITHUMB] Rest API Polling Start ... ")
            self.logger.info(f"데이터 수집 시작 : { self.symbol }-{ self.currency }")
            self.running = True
            self.t = threading.Thread(
                target = self.loop,
                daemon = True
            )
            self.t.start()
    def stop(self):
        if self.t:
            self.t.join()
            self.conn.close()
            self.logger.info(f"데이터 수집 종료 : { self.symbol }-{ self.currency }")
    