import json
from .WSController import WSController

class UpbitController(WSController):
    def getName(self):
        return "UPBIT"
    def getWSUrl(self):
        return "wss://api.upbit.com/websocket/v1"
    
    def getMessage(self):
        return json.dumps(
            [
                { "ticket" : "tori_test" },
                {
                    "type" : "orderbook",
                    "codes" : [ f"{self.currency}-{self.symbol}" ]
                }
            ]
        )
    
    def handleMessage(self, message):
        try:
            data = json.loads(message.decode('utf-8'))
            results = []
            
            name = self.getName()
            [ currency, symbol ] = data["code"].split("-")
            timestamp = data["timestamp"]
            for unit in data["orderbook_units"]:
                results.append(
                    {
                        "exchange" : name,
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
                        "exchange" : name,
                        "symbol" : symbol,
                        "currency" : currency,
                        "timestamp" : timestamp,
                        "side" : "bid",
                        "price" : unit["bid_price"],
                        "volume" : unit["bid_size"]
                    }
                )
            
            if len(results) > 0:
                self.saveDataToDB(results)
        except Exception as e:
            print(f"[{self.getName()}] Error : {e}")
            return False, e
        return True, None