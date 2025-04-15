import json 
from .WSController import WSController

class CoinoneController(WSController):
    def getName(self):
        return "COINONE"
    def getWSUrl(self):
        return "wss://stream.coinone.co.kr"
    
    def getMessage(self):
        return json.dumps(
            {
                "request_type" : "SUBSCRIBE",
                "channel" : "ORDERBOOK",
                "topic" : {
                    "quote_currency" : self.currency,
                    "target_currency" : self.symbol
                }
            }
        )
    
    def handleMessage(self, message):
        try:
            raw_data = json.loads(message)
            if "data" in raw_data:
                results = []
                
                data = raw_data["data"]
                
                invalid_data = "session_id" in data or not "timestamp" in data
                
                if not invalid_data:
                    exchange = self.getName()
                    currency = data["quote_currency"]
                    symbol = data["target_currency"]
                    
                    
                    timestamp = data["timestamp"]
                    
                    if "asks" in data and len(data["asks"]) > 0:
                        for ask in data["asks"]:
                            results.append(
                                {
                                    "exchange" : exchange,
                                    "symbol" : symbol,
                                    "currency" : currency,
                                    "timestamp" : timestamp,
                                    "side" : "ask",
                                    "price" : ask["price"],
                                    "volume" : ask["qty"]
                                }
                            )
                    if "bids" in data and len(data["bids"]) > 0:
                        for bid in data["bids"]:
                            results.append(
                                {
                                    "exchange" : exchange,
                                    "symbol" : symbol,
                                    "currency" : currency,
                                    "timestamp" : timestamp,
                                    "side" : "bid",
                                    "price" : bid["price"],
                                    "volume" : bid["qty"]
                                }
                            )
                    if len(results) > 0:
                        self.saveDataToDB(results)
        except Exception as e:
            return False, e
        return True, None