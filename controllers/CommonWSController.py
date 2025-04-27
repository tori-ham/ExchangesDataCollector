import os

import traceback
import sqlite3
import websocket
import threading

from utils.utils import updatePairMonitoringStatus, onlyUpdateMonitoringStatus
from log_util import getLogger

from dotenv import load_dotenv
load_dotenv()

DB_PATH = os.environ.get("DB_PATH")

class CommonWSController():
    def __init__(
        self, 
        symbol, 
        currency, 
        name,
        wsUrl,
        wsMessage,
        wsHandleMessageFunc
    ):
        self.symbol = symbol.upper()
        self.currency = currency.upper()
        self.name = name
        self.ws_url = wsUrl
        # symbol, currency 파라미터 넣어야함
        self.ws_message = wsMessage.format(
            symbol = self.symbol,
            currency = self.currency
        )
        print("self ws message", self.ws_message)
        self.handle_message_func = wsHandleMessageFunc
        
        self.wsApp = websocket.WebSocketApp(
            self.ws_url,
            on_open = self.onConnect,
            on_message = self.onMessage,
            on_close = self.onClose,
            on_error = self.onError
        )
        self.t = None
        self.conn = None
        self.is_error = False
        self.logger = getLogger(
            f"[{self.getName()} / {symbol}-{currency}]"
        )
    
    def getName(self):
        return self.name
    def getWSUrl(self):
        return self.ws_url
    def getMessage(self):
        return self.ws_message
    def handleMessage(self, message):
        return self.handle_message_func(message)
    
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
            
            if self.is_error:
                onlyUpdateMonitoringStatus(
                    self.name,
                    self.symbol,
                    self.currency,
                    "STOPPED"
                )
            else:
                self.updateControllerStatus(
                    False,
                    "STOPPED",
                    "데이터 수집 정지"
                )
    
    def onConnect(self, ws):
        print(f"[{self.name}] Connected")
        self.logger.info(f"WebSocket 연결 성공")
        msg = self.ws_message
        ws.send(msg)
        
    def onMessage(self, ws, msg):
        print("msg", msg)
        try:
            parsed_msg_result, err_msg = self.handle_message_func(self, msg)
            if parsed_msg_result:
                if self.is_error:
                    self.updateControllerStatus(False, "RUNNING", "")
                    self.is_error = False
            else:
                self.updateControllerStatus(True, "RUNNING", err_msg)
                self.logger.error(f"Error in handleMessage : {err_msg}")
        except Exception as e:
            if not self.is_error:
                self.updateControllerStatus(True, "RUNNING", e)
            self.logger.error(f"Error in handleMessage : {e}")
    def onClose(self, ws, status, msg):
        print(f"[{self.name}] Closed")
        self.logger.info(f"WebSocket 연결 종료")
    def onError(self, ws, error):
        traceback.print_exc()
        print(f"[{self.name}] Error : {error}")
        self.logger(error(f"Error in WebSocket : {error}"))
        if not self.is_error:
            self.updateControllerStatus(True, "RUNNING", error)
    
    def saveDataToDB(self, data):
        cur = self.conn.cursor()
        cur.executemany(
            """
                INSERT INTO orderbook(exchange, symbol, currency, timestamp, side, price, volume) VALUES (:exchange, :symbol, :currency, :timestamp, :side, :price, :volume)
            """, 
            data
        )
        self.conn.commit()
    def updateControllerStatus(self, isError, controllerStatus, memo):
        self.is_error = isError
        updatePairMonitoringStatus(
            self.name,
            self.symbol,
            self.currency,
            "error" if isError else "no",
            controllerStatus,
            memo
        )