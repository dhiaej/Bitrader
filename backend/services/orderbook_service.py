"""OrderBook Service - Background matching engine"""

class OrderBookService:
    def __init__(self, ws_manager):
        self.ws_manager = ws_manager
    
    async def start_matching_engine(self):
        """Start background order matching"""
        pass
