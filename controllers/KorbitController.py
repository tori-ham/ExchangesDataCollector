import traceback
import json 
from .WSController import WSController

class KorbitController(WSController):
    def getName(self):
        return "KORBIT"
    def getWSUrl(self):
        return "wss://ws-api.korbit.co.kr/v2/public"
    
    def getMessage(self):
        return json.dumps(
            [
                {
                    "method" : "subscribe",
                    "type" : "orderbook",
                    "symbols" : [ f"{self.symbol.lower()}_{self.currency.lower()}" ]
                }
            ]
        )
    
    def handleMessage(self, message):
        try:
            data = json.loads(message)
            
            results = []
            name = self.getName()
            [symbol, currency] = data["symbol"].split("_")
            timestamp = data["timestamp"]
            
            units = data["data"]
            
            if "asks" in units:
                for ask in units["asks"]:
                    results.append(
                        {
                            "exchange" : name,
                            "symbol" : symbol,
                            "currency" : currency,
                            "timestamp" :  timestamp,
                            "side" : "ask",
                            "price" : ask["price"],
                            "volume" : ask["qty"]
                        }
                    )
            if "bids" in units:
                for bid in units["bids"]:
                    results.append(
                        {
                            "exchange" : name,
                            "symbol" : symbol,
                            "currency" : currency,
                            "timestamp" :  timestamp,
                            "side" : "bid",
                            "price" : bid["price"],
                            "volume" : bid["qty"]
                        }
                    )
            if len(results) > 0:
                self.saveDataToDB(results)
        except Exception as err:
            traceback.print_exc()
            print(f"[{self.getName()}] Error : {err}")
            return False, err
        return True, None