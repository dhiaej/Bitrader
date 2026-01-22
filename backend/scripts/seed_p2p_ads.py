"""
Seed P2P Marketplace with Many Advertisements
Creates diverse P2P advertisements for testing and demonstration
"""

from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import User, P2PAdvertisement, OrderType
from decimal import Decimal
import json
import random

def seed_p2p_advertisements():
    """Create many P2P advertisements with various options"""
    
    print("🌱 Seeding P2P marketplace with advertisements...")
    
    db = SessionLocal()
    
    try:
        # Get existing users
        users = db.query(User).all()
        
        if len(users) < 3:
            print("❌ Not enough users in database. Please run seed_db.py first.")
            return False
        
        # Define various payment methods
        payment_methods_options = [
            ["Bank Transfer", "PayPal"],
            ["Bank Transfer", "Wise", "Revolut"],
            ["PayPal", "Venmo"],
            ["Bank Transfer"],
            ["Wise", "PayPal", "Zelle"],
            ["Cash App", "Venmo"],
            ["Bank Transfer", "PayPal", "Wise"],
            ["Western Union", "MoneyGram"],
            ["Bank Transfer", "Crypto Transfer"],
            ["PayPal"],
            ["Wise"],
            ["Revolut", "N26"]
        ]
        
        # Define terms and conditions templates
        terms_templates = [
            "Fast and reliable trader. Online most of the time.",
            "Professional trader with 100+ completed trades.",
            "Quick response. Payment within minutes.",
            "Trusted seller. Will release immediately after payment confirmation.",
            "New trader but committed to excellent service!",
            "Available 24/7. Instant crypto release.",
            "Verified trader. No delays guaranteed.",
            "Looking for serious buyers/sellers only.",
            "Flexible payment options. Let's trade!",
            "Experienced P2P trader. Safe and secure transactions.",
            "Fast transactions. No time wasters please.",
            "Premium service. VIP treatment for all traders."
        ]
        
        advertisements = []
        
        # BTC SELL Advertisements (USD)
        btc_usd_prices = [44500, 44800, 45000, 45200, 45500, 45800, 46000]
        for i, price in enumerate(btc_usd_prices):
            user = users[i % len(users)]
            ad = {
                "user_id": user.id,
                "ad_type": OrderType.SELL,
                "currency": "BTC",
                "fiat_currency": "USD",
                "price": Decimal(str(price)),
                "min_limit": Decimal(str(random.choice([50, 100, 200, 500]))),
                "max_limit": Decimal(str(random.choice([2000, 5000, 10000, 20000]))),
                "available_amount": Decimal(str(random.uniform(0.1, 2.0))),
                "payment_methods": json.dumps(random.choice(payment_methods_options)),
                "payment_time_limit": random.choice([15, 20, 30, 45, 60]),
                "terms_conditions": random.choice(terms_templates)
            }
            advertisements.append(ad)
        
        # BTC BUY Advertisements (USD)
        btc_usd_buy_prices = [44000, 44300, 44700, 45000, 45300]
        for i, price in enumerate(btc_usd_buy_prices):
            user = users[i % len(users)]
            ad = {
                "user_id": user.id,
                "ad_type": OrderType.BUY,
                "currency": "BTC",
                "fiat_currency": "USD",
                "price": Decimal(str(price)),
                "min_limit": Decimal(str(random.choice([100, 200, 500]))),
                "max_limit": Decimal(str(random.choice([5000, 10000, 15000]))),
                "available_amount": Decimal(str(random.uniform(0.5, 3.0))),
                "payment_methods": json.dumps(random.choice(payment_methods_options)),
                "payment_time_limit": random.choice([20, 30, 45]),
                "terms_conditions": random.choice(terms_templates)
            }
            advertisements.append(ad)
        
        # BTC EUR Advertisements
        btc_eur_sell_prices = [40500, 40800, 41000, 41300, 41500]
        for i, price in enumerate(btc_eur_sell_prices):
            user = users[i % len(users)]
            ad = {
                "user_id": user.id,
                "ad_type": OrderType.SELL,
                "currency": "BTC",
                "fiat_currency": "EUR",
                "price": Decimal(str(price)),
                "min_limit": Decimal(str(random.choice([50, 100, 200]))),
                "max_limit": Decimal(str(random.choice([2000, 5000, 8000]))),
                "available_amount": Decimal(str(random.uniform(0.1, 1.5))),
                "payment_methods": json.dumps(random.choice(payment_methods_options)),
                "payment_time_limit": random.choice([15, 30, 45]),
                "terms_conditions": random.choice(terms_templates)
            }
            advertisements.append(ad)
        
        btc_eur_buy_prices = [40000, 40300, 40700, 41000]
        for i, price in enumerate(btc_eur_buy_prices):
            user = users[i % len(users)]
            ad = {
                "user_id": user.id,
                "ad_type": OrderType.BUY,
                "currency": "BTC",
                "fiat_currency": "EUR",
                "price": Decimal(str(price)),
                "min_limit": Decimal(str(random.choice([100, 200]))),
                "max_limit": Decimal(str(random.choice([3000, 5000, 10000]))),
                "available_amount": Decimal(str(random.uniform(0.3, 2.0))),
                "payment_methods": json.dumps(random.choice(payment_methods_options)),
                "payment_time_limit": random.choice([20, 30]),
                "terms_conditions": random.choice(terms_templates)
            }
            advertisements.append(ad)
        
        # BTC GBP Advertisements
        btc_gbp_prices = [35000, 35300, 35500, 35800, 36000]
        for i, price in enumerate(btc_gbp_prices):
            user = users[i % len(users)]
            ad_type = OrderType.SELL if i % 2 == 0 else OrderType.BUY
            ad = {
                "user_id": user.id,
                "ad_type": ad_type,
                "currency": "BTC",
                "fiat_currency": "GBP",
                "price": Decimal(str(price)),
                "min_limit": Decimal(str(random.choice([50, 100, 200]))),
                "max_limit": Decimal(str(random.choice([2000, 4000, 6000]))),
                "available_amount": Decimal(str(random.uniform(0.2, 1.5))),
                "payment_methods": json.dumps(random.choice(payment_methods_options)),
                "payment_time_limit": random.choice([15, 30, 45]),
                "terms_conditions": random.choice(terms_templates)
            }
            advertisements.append(ad)
        
        # ETH SELL Advertisements (USD)
        eth_usd_prices = [2900, 2950, 3000, 3050, 3100, 3150, 3200]
        for i, price in enumerate(eth_usd_prices):
            user = users[i % len(users)]
            ad = {
                "user_id": user.id,
                "ad_type": OrderType.SELL,
                "currency": "ETH",
                "fiat_currency": "USD",
                "price": Decimal(str(price)),
                "min_limit": Decimal(str(random.choice([50, 100, 200]))),
                "max_limit": Decimal(str(random.choice([1000, 3000, 5000, 8000]))),
                "available_amount": Decimal(str(random.uniform(1.0, 10.0))),
                "payment_methods": json.dumps(random.choice(payment_methods_options)),
                "payment_time_limit": random.choice([15, 20, 30, 45]),
                "terms_conditions": random.choice(terms_templates)
            }
            advertisements.append(ad)
        
        # ETH BUY Advertisements (USD)
        eth_usd_buy_prices = [2850, 2900, 2950, 3000, 3050]
        for i, price in enumerate(eth_usd_buy_prices):
            user = users[i % len(users)]
            ad = {
                "user_id": user.id,
                "ad_type": OrderType.BUY,
                "currency": "ETH",
                "fiat_currency": "USD",
                "price": Decimal(str(price)),
                "min_limit": Decimal(str(random.choice([50, 100, 200]))),
                "max_limit": Decimal(str(random.choice([2000, 5000, 10000]))),
                "available_amount": Decimal(str(random.uniform(2.0, 15.0))),
                "payment_methods": json.dumps(random.choice(payment_methods_options)),
                "payment_time_limit": random.choice([20, 30, 45]),
                "terms_conditions": random.choice(terms_templates)
            }
            advertisements.append(ad)
        
        # ETH EUR Advertisements
        eth_eur_prices = [2600, 2650, 2700, 2750, 2800, 2850]
        for i, price in enumerate(eth_eur_prices):
            user = users[i % len(users)]
            ad_type = OrderType.SELL if i % 2 == 0 else OrderType.BUY
            ad = {
                "user_id": user.id,
                "ad_type": ad_type,
                "currency": "ETH",
                "fiat_currency": "EUR",
                "price": Decimal(str(price)),
                "min_limit": Decimal(str(random.choice([50, 100, 200]))),
                "max_limit": Decimal(str(random.choice([2000, 4000, 6000]))),
                "available_amount": Decimal(str(random.uniform(1.0, 8.0))),
                "payment_methods": json.dumps(random.choice(payment_methods_options)),
                "payment_time_limit": random.choice([15, 30, 45]),
                "terms_conditions": random.choice(terms_templates)
            }
            advertisements.append(ad)
        
        # ETH GBP Advertisements
        eth_gbp_prices = [2300, 2350, 2400, 2450, 2500]
        for i, price in enumerate(eth_gbp_prices):
            user = users[i % len(users)]
            ad_type = OrderType.SELL if i % 2 == 0 else OrderType.BUY
            ad = {
                "user_id": user.id,
                "ad_type": ad_type,
                "currency": "ETH",
                "fiat_currency": "GBP",
                "price": Decimal(str(price)),
                "min_limit": Decimal(str(random.choice([50, 100, 200]))),
                "max_limit": Decimal(str(random.choice([2000, 4000, 5000]))),
                "available_amount": Decimal(str(random.uniform(1.0, 7.0))),
                "payment_methods": json.dumps(random.choice(payment_methods_options)),
                "payment_time_limit": random.choice([15, 30]),
                "terms_conditions": random.choice(terms_templates)
            }
            advertisements.append(ad)
        
        # USDT SELL Advertisements (USD)
        usdt_usd_prices = [0.998, 0.999, 1.000, 1.001, 1.002, 1.003]
        for i, price in enumerate(usdt_usd_prices):
            user = users[i % len(users)]
            ad = {
                "user_id": user.id,
                "ad_type": OrderType.SELL,
                "currency": "USDT",
                "fiat_currency": "USD",
                "price": Decimal(str(price)),
                "min_limit": Decimal(str(random.choice([20, 50, 100]))),
                "max_limit": Decimal(str(random.choice([500, 1000, 2000, 5000]))),
                "available_amount": Decimal(str(random.uniform(500, 10000))),
                "payment_methods": json.dumps(random.choice(payment_methods_options)),
                "payment_time_limit": random.choice([10, 15, 20, 30]),
                "terms_conditions": random.choice(terms_templates)
            }
            advertisements.append(ad)
        
        # USDT BUY Advertisements (USD)
        usdt_usd_buy_prices = [0.997, 0.998, 0.999, 1.000, 1.001]
        for i, price in enumerate(usdt_usd_buy_prices):
            user = users[i % len(users)]
            ad = {
                "user_id": user.id,
                "ad_type": OrderType.BUY,
                "currency": "USDT",
                "fiat_currency": "USD",
                "price": Decimal(str(price)),
                "min_limit": Decimal(str(random.choice([20, 50, 100]))),
                "max_limit": Decimal(str(random.choice([1000, 2000, 5000]))),
                "available_amount": Decimal(str(random.uniform(1000, 15000))),
                "payment_methods": json.dumps(random.choice(payment_methods_options)),
                "payment_time_limit": random.choice([10, 15, 20]),
                "terms_conditions": random.choice(terms_templates)
            }
            advertisements.append(ad)
        
        # USDT EUR Advertisements
        usdt_eur_prices = [0.90, 0.91, 0.92, 0.93, 0.94]
        for i, price in enumerate(usdt_eur_prices):
            user = users[i % len(users)]
            ad_type = OrderType.SELL if i % 2 == 0 else OrderType.BUY
            ad = {
                "user_id": user.id,
                "ad_type": ad_type,
                "currency": "USDT",
                "fiat_currency": "EUR",
                "price": Decimal(str(price)),
                "min_limit": Decimal(str(random.choice([20, 50, 100]))),
                "max_limit": Decimal(str(random.choice([500, 1000, 3000]))),
                "available_amount": Decimal(str(random.uniform(500, 8000))),
                "payment_methods": json.dumps(random.choice(payment_methods_options)),
                "payment_time_limit": random.choice([10, 15, 20, 30]),
                "terms_conditions": random.choice(terms_templates)
            }
            advertisements.append(ad)
        
        # USDT GBP Advertisements
        usdt_gbp_prices = [0.78, 0.79, 0.80, 0.81, 0.82]
        for i, price in enumerate(usdt_gbp_prices):
            user = users[i % len(users)]
            ad_type = OrderType.SELL if i % 2 == 0 else OrderType.BUY
            ad = {
                "user_id": user.id,
                "ad_type": ad_type,
                "currency": "USDT",
                "fiat_currency": "GBP",
                "price": Decimal(str(price)),
                "min_limit": Decimal(str(random.choice([20, 50, 100]))),
                "max_limit": Decimal(str(random.choice([500, 1000, 2000]))),
                "available_amount": Decimal(str(random.uniform(500, 7000))),
                "payment_methods": json.dumps(random.choice(payment_methods_options)),
                "payment_time_limit": random.choice([10, 15, 20]),
                "terms_conditions": random.choice(terms_templates)
            }
            advertisements.append(ad)
        
        # Add all advertisements to database
        for ad_data in advertisements:
            ad = P2PAdvertisement(**ad_data)
            db.add(ad)
        
        db.commit()
        
        print(f"\n✅ Successfully created {len(advertisements)} P2P advertisements!")
        print("\n📊 Advertisement Breakdown:")
        
        # Count by currency and type
        btc_sell = len([a for a in advertisements if a['currency'] == 'BTC' and a['ad_type'] == OrderType.SELL])
        btc_buy = len([a for a in advertisements if a['currency'] == 'BTC' and a['ad_type'] == OrderType.BUY])
        eth_sell = len([a for a in advertisements if a['currency'] == 'ETH' and a['ad_type'] == OrderType.SELL])
        eth_buy = len([a for a in advertisements if a['currency'] == 'ETH' and a['ad_type'] == OrderType.BUY])
        usdt_sell = len([a for a in advertisements if a['currency'] == 'USDT' and a['ad_type'] == OrderType.SELL])
        usdt_buy = len([a for a in advertisements if a['currency'] == 'USDT' and a['ad_type'] == OrderType.BUY])
        
        print(f"  BTC: {btc_sell} SELL, {btc_buy} BUY")
        print(f"  ETH: {eth_sell} SELL, {eth_buy} BUY")
        print(f"  USDT: {usdt_sell} SELL, {usdt_buy} BUY")
        
        # Count by fiat currency
        usd_ads = len([a for a in advertisements if a['fiat_currency'] == 'USD'])
        eur_ads = len([a for a in advertisements if a['fiat_currency'] == 'EUR'])
        gbp_ads = len([a for a in advertisements if a['fiat_currency'] == 'GBP'])
        
        print(f"\n  Fiat Currencies:")
        print(f"  USD: {usd_ads} ads")
        print(f"  EUR: {eur_ads} ads")
        print(f"  GBP: {gbp_ads} ads")
        
        print(f"\n🎉 P2P Marketplace is now fully populated!")
        print(f"🚀 Start the server to explore all advertisements!")
        
    except Exception as e:
        print(f"\n❌ Error seeding P2P advertisements: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()
    
    return True

if __name__ == "__main__":
    # Ensure tables exist first
    print("📋 Ensuring database tables exist...")
    Base.metadata.create_all(bind=engine)
    
    # Seed P2P advertisements
    seed_p2p_advertisements()
