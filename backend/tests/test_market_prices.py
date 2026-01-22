"""Test market data service to check current prices"""
import sys
sys.path.insert(0, '.')
from services.market_data_service import MultiSourceMarketDataService
import time

service = MultiSourceMarketDataService()
service.start()
time.sleep(3)  # Wait for initial price fetch

# Test get_price
btc_price = service.get_price('BTC-USD')
eth_price = service.get_price('ETH-USD')

print(f"BTC Price: ${btc_price}")
print(f"ETH Price: ${eth_price}")

# Get all prices
all_prices = service.get_all_prices()
print(f"\nAll tracked symbols: {list(all_prices.get('prices', {}).keys())}")

# Check each crypto
for symbol in ['BTC-USD', 'ETH-USD', 'LTC-USD', 'SOL-USD', 'DOGE-USD']:
    price_data = all_prices.get('prices', {}).get(symbol, {})
    price = price_data.get('price', 0)
    market_cap = price_data.get('market_cap', 0)
    print(f"{symbol}: price=${price:,.2f}, market_cap=${market_cap:,.0f}")

service.stop()
