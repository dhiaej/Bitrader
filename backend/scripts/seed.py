"""
Comprehensive Database Seeding Script
Populates the database with realistic mock data for development/testing
"""

import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
import random
import json
from typing import List

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from faker import Faker
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
from models import (
    User, Wallet, Reputation, ForumCategory, ForumPost, ForumComment, 
    ForumVote, SimulatorResult
)
from utils.auth import get_password_hash
from config import settings

# Initialize Faker
fake = Faker()
Faker.seed(42)  # For reproducible results
random.seed(42)

# Trading pairs for simulator
TRADING_PAIRS = ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "ADA-USD", "DOGE-USD", "DOT-USD"]

# Forum topics
FORUM_TOPICS = [
    {
        "title": "Bitcoin price prediction 2025",
        "content": "What are your thoughts on Bitcoin's price trajectory for 2025? With the halving behind us and institutional adoption increasing, I'm bullish on BTC reaching new ATHs. What's your take?",
        "tags": ["bitcoin", "price-prediction", "2025", "analysis"]
    },
    {
        "title": "Best strategy for scalping",
        "content": "I've been trying to improve my scalping strategy. Currently using 1-minute charts with RSI and MACD indicators. Anyone have tips on entry/exit points? What timeframes work best for you?",
        "tags": ["scalping", "strategy", "trading", "tips"]
    },
    {
        "title": "ETH vs SOL - Which has better fundamentals?",
        "content": "Both Ethereum and Solana have strong ecosystems, but which do you think has better long-term fundamentals? ETH has the network effect, but SOL has faster transactions and lower fees. What's your analysis?",
        "tags": ["ethereum", "solana", "comparison", "fundamentals"]
    },
    {
        "title": "How to manage risk in volatile markets?",
        "content": "The market has been extremely volatile lately. How do you manage risk when prices swing 10-20% in a day? Stop losses? Position sizing? Would love to hear your strategies.",
        "tags": ["risk-management", "volatility", "trading", "strategy"]
    },
    {
        "title": "DeFi yield farming opportunities",
        "content": "Looking for current DeFi yield farming opportunities with reasonable APY and low risk. Any recommendations? I'm particularly interested in stablecoin pools.",
        "tags": ["defi", "yield-farming", "stablecoins", "opportunities"]
    },
    {
        "title": "Technical analysis: Head and Shoulders pattern",
        "content": "I think I spotted a head and shoulders pattern forming on BTC/USD. Can someone confirm? This could be a bearish signal. What's your interpretation?",
        "tags": ["technical-analysis", "bitcoin", "chart-patterns", "bearish"]
    },
    {
        "title": "Best time to buy altcoins?",
        "content": "When do you think is the best time to enter altcoin positions? Should I wait for BTC to stabilize first, or is now a good entry point?",
        "tags": ["altcoins", "entry-timing", "market-timing", "strategy"]
    },
    {
        "title": "Staking vs Trading - Which is better?",
        "content": "I'm debating between staking my crypto for passive income or actively trading. What are the pros and cons of each approach? What's your experience?",
        "tags": ["staking", "trading", "passive-income", "comparison"]
    },
    {
        "title": "Market manipulation - How to spot it?",
        "content": "I've noticed some suspicious price movements that look like manipulation. What are the telltale signs of market manipulation? How can retail traders protect themselves?",
        "tags": ["market-manipulation", "trading", "education", "safety"]
    },
    {
        "title": "Tax implications of crypto trading",
        "content": "How do you handle taxes for crypto trading? Do you use any tools to track your trades? I'm looking for recommendations on tax software for traders.",
        "tags": ["taxes", "crypto-tax", "trading", "compliance"]
    },
    {
        "title": "Best indicators for swing trading",
        "content": "I'm new to swing trading and want to know which indicators work best for 4-hour and daily timeframes. Currently using EMA crossovers. Any suggestions?",
        "tags": ["swing-trading", "indicators", "technical-analysis", "education"]
    },
    {
        "title": "NFT market crash - Your thoughts?",
        "content": "The NFT market has crashed significantly from its peak. Do you think this is a temporary correction or the end of the NFT hype? What's your outlook?",
        "tags": ["nft", "market-analysis", "crypto", "discussion"]
    },
    {
        "title": "Layer 2 solutions comparison",
        "content": "With so many L2 solutions (Arbitrum, Optimism, Polygon, Base), which one do you think will dominate? What are the key differences in terms of fees, security, and adoption?",
        "tags": ["layer-2", "ethereum", "scaling", "comparison"]
    },
    {
        "title": "How to read order book effectively?",
        "content": "I'm trying to learn how to read order books to improve my trading. What should I look for? Support/resistance levels? Large orders? Any resources or tips?",
        "tags": ["order-book", "trading", "education", "market-analysis"]
    },
    {
        "title": "Crypto portfolio diversification",
        "content": "How do you diversify your crypto portfolio? What percentage in BTC, ETH, altcoins, and stablecoins? I'm trying to balance risk and potential returns.",
        "tags": ["portfolio", "diversification", "risk-management", "strategy"]
    }
]

# Forum comment templates
COMMENT_TEMPLATES = [
    "Great analysis! I agree with your points, especially regarding {topic}.",
    "I have a different perspective. In my experience, {topic} works better when {condition}.",
    "Thanks for sharing! This is really helpful. I'll try implementing this strategy.",
    "I've been trading for {years} years and I can confirm this approach works well.",
    "Interesting take! Have you considered {alternative}? It might be worth exploring.",
    "This is exactly what I needed! Can you elaborate more on {detail}?",
    "I disagree with this approach. Based on my research, {counterpoint}.",
    "Great post! I've bookmarked this for future reference.",
    "Has anyone tried this with {variation}? I'm curious about the results.",
    "This aligns with what I've been seeing in the market lately. Good insights!"
]


def create_users(db: Session, count: int = 25) -> List[User]:
    """Create realistic users with wallets and reputation"""
    print(f"\n👥 Creating {count} users...")
    users = []
    
    for i in range(count):
        # Generate unique username and email
        username = fake.user_name() + str(random.randint(100, 999))
        email = fake.email()
        
        # Check if user already exists
        existing = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing:
            continue
        
        # Create user
        user = User(
            username=username,
            email=email,
            hashed_password=get_password_hash("password123"),  # Default password
            full_name=fake.name(),
            avatar_url=f"https://i.pravatar.cc/150?u={username}",
            is_active=True,
            is_verified=random.choice([True, True, True, False]),  # 75% verified
            is_admin=(i == 0),  # First user is admin
            created_at=fake.date_time_between(start_date="-1y", end_date="now"),
            last_login=fake.date_time_between(start_date="-30d", end_date="now") if random.random() > 0.3 else None
        )
        db.add(user)
        db.flush()
        
        # Create wallets
        currencies = ["USD", "BTC", "ETH", "BNB", "XRP", "ADA", "SOL", "DOGE", "DOT", "MATIC", "AVAX", "LINK", "UNI", "ATOM", "LTC", "SHIB", "TRX", "ARB", "OP", "USDT"]
        for currency in currencies:
            if currency == "USD":
                available = Decimal(str(random.uniform(1000, 50000)))
            elif currency == "BTC":
                available = Decimal(str(random.uniform(0.01, 2.0)))
            elif currency == "ETH":
                available = Decimal(str(random.uniform(0.1, 10.0)))
            elif currency == "BNB":
                available = Decimal(str(random.uniform(0.5, 20.0)))
            elif currency == "XRP":
                available = Decimal(str(random.uniform(100, 5000)))
            elif currency == "ADA":
                available = Decimal(str(random.uniform(200, 8000)))
            elif currency == "SOL":
                available = Decimal(str(random.uniform(1, 50)))
            elif currency == "DOGE":
                available = Decimal(str(random.uniform(1000, 50000)))
            elif currency == "DOT":
                available = Decimal(str(random.uniform(10, 500)))
            elif currency == "MATIC":
                available = Decimal(str(random.uniform(100, 5000)))
            elif currency == "AVAX":
                available = Decimal(str(random.uniform(2, 100)))
            elif currency == "LINK":
                available = Decimal(str(random.uniform(5, 200)))
            elif currency == "UNI":
                available = Decimal(str(random.uniform(10, 500)))
            elif currency == "ATOM":
                available = Decimal(str(random.uniform(10, 400)))
            elif currency == "LTC":
                available = Decimal(str(random.uniform(1, 50)))
            elif currency == "SHIB":
                available = Decimal(str(random.uniform(1000000, 50000000)))
            elif currency == "TRX":
                available = Decimal(str(random.uniform(1000, 40000)))
            elif currency == "ARB":
                available = Decimal(str(random.uniform(50, 2000)))
            elif currency == "OP":
                available = Decimal(str(random.uniform(20, 1000)))
            else:  # USDT
                available = Decimal(str(random.uniform(500, 20000)))
            
            locked = Decimal(str(random.uniform(0, float(available) * 0.2)))
            
            wallet = Wallet(
                user_id=user.id,
                currency=currency,
                available_balance=available,
                locked_balance=locked
            )
            db.add(wallet)
        
        # Create reputation
        reputation_score = random.randint(50, 2000)
        total_trades = random.randint(0, 150)
        completed_trades = int(total_trades * random.uniform(0.7, 0.95))
        completion_rate = (completed_trades / total_trades * 100) if total_trades > 0 else 0.0
        
        reputation = Reputation(
            user_id=user.id,
            score=reputation_score,
            total_trades=total_trades,
            completed_trades=completed_trades,
            completion_rate=completion_rate
        )
        db.add(reputation)
        
        users.append(user)
        print(f"  ✅ Created user: {username} (Admin: {user.is_admin})")
    
    db.commit()
    print(f"✅ Created {len(users)} users successfully!")
    return users


def create_forum_categories(db: Session) -> List[ForumCategory]:
    """Create forum categories if they don't exist"""
    print("\n📁 Setting up forum categories...")
    
    categories_data = [
        {"name": "General Discussion", "description": "General trading discussions", "icon": "💬", "min_reputation": 0},
        {"name": "Trading Strategies", "description": "Share and discuss trading strategies", "icon": "📊", "min_reputation": 0},
        {"name": "Market Analysis", "description": "Technical and fundamental analysis", "icon": "📈", "min_reputation": 0},
        {"name": "Beginners", "description": "Questions and tips for new traders", "icon": "🎓", "min_reputation": 0},
        {"name": "Advanced Trading", "description": "Advanced trading techniques (Pro level)", "icon": "⚡", "min_reputation": 500},
        {"name": "Expert Strategies", "description": "Expert-level trading discussions", "icon": "🏆", "min_reputation": 1000},
    ]
    
    categories = []
    for cat_data in categories_data:
        existing = db.query(ForumCategory).filter(ForumCategory.name == cat_data["name"]).first()
        if existing:
            categories.append(existing)
            print(f"  ⏭️  Category '{cat_data['name']}' already exists")
        else:
            category = ForumCategory(
                name=cat_data["name"],
                description=cat_data["description"],
                icon=cat_data["icon"],
                min_reputation_required=cat_data["min_reputation"],
                is_active=True,
                sort_order=len(categories)
            )
            db.add(category)
            db.flush()
            categories.append(category)
            print(f"  ✅ Created category: {cat_data['name']}")
    
    db.commit()
    return categories


def create_forum_posts(db: Session, users: List[User], categories: List[ForumCategory], count: int = 25) -> List[ForumPost]:
    """Create forum posts with comments"""
    print(f"\n📝 Creating {count} forum posts...")
    
    posts = []
    normal_categories = [c for c in categories if c.min_reputation_required == 0]
    
    for i in range(count):
        # Select random user and category
        author = random.choice(users)
        category = random.choice(normal_categories)  # Use normal categories for seed data
        
        # Get topic (cycle through if needed)
        topic = FORUM_TOPICS[i % len(FORUM_TOPICS)]
        
        # Create post
        post = ForumPost(
            title=topic["title"],
            content=topic["content"],
            author_id=author.id,
            category_id=category.id,
            tags=json.dumps(topic["tags"]),
            upvotes=random.randint(0, 50),
            downvotes=random.randint(0, 10),
            view_count=random.randint(10, 500),
            is_pinned=(i < 2),  # First 2 posts are pinned
            is_locked=False,
            created_at=fake.date_time_between(start_date="-60d", end_date="now"),
            last_activity_at=fake.date_time_between(start_date="-7d", end_date="now")
        )
        db.add(post)
        db.flush()
        
        # Create comments (3-5 per post)
        num_comments = random.randint(3, 5)
        comment_count = 0
        
        for j in range(num_comments):
            comment_author = random.choice(users)
            comment_content = fake.text(max_nb_chars=200)
            
            # Sometimes use template
            if random.random() > 0.5:
                template = random.choice(COMMENT_TEMPLATES)
                # Prepare all possible format values
                format_values = {
                    "topic": random.choice(["technical analysis", "risk management", "entry points"]),
                    "condition": random.choice(["market is trending", "volatility is low"]),
                    "years": random.randint(1, 5),
                    "alternative": random.choice(["DCA strategy", "grid trading"]),
                    "detail": random.choice(["position sizing", "stop loss placement"]),
                    "counterpoint": random.choice(["momentum indicators work better", "fundamental analysis is more reliable"]),
                    "variation": random.choice(["different timeframes", "alternative indicators", "various market conditions"])
                }
                try:
                    comment_content = template.format(**format_values)
                except KeyError as e:
                    # If template has placeholders we didn't account for, just use fake text
                    comment_content = fake.text(max_nb_chars=200)
            
            comment = ForumComment(
                post_id=post.id,
                author_id=comment_author.id,
                content=comment_content,
                upvotes=random.randint(0, 20),
                downvotes=random.randint(0, 3),
                is_solution=(j == 0 and random.random() > 0.7),  # 30% chance first comment is solution
                created_at=fake.date_time_between(start_date=post.created_at, end_date="now")
            )
            db.add(comment)
            comment_count += 1
            
            # Sometimes add a reply to the comment
            if random.random() > 0.6:
                reply_author = random.choice([u for u in users if u.id != comment_author.id])
                reply = ForumComment(
                    post_id=post.id,
                    author_id=reply_author.id,
                    content=fake.text(max_nb_chars=150),
                    parent_comment_id=comment.id,
                    upvotes=random.randint(0, 10),
                    downvotes=random.randint(0, 2),
                    created_at=fake.date_time_between(start_date=comment.created_at, end_date="now")
                )
                db.add(reply)
                comment_count += 1
        
        # Update post comment count
        post.comment_count = comment_count
        
        # Add some votes
        voters = random.sample(users, min(random.randint(5, 15), len(users)))
        for voter in voters:
            vote_type = random.choice(["UP", "DOWN"])
            if vote_type == "UP":
                post.upvotes += 1
            else:
                post.downvotes += 1
            
            vote = ForumVote(
                user_id=voter.id,
                post_id=post.id,
                vote_type=vote_type
            )
            db.add(vote)
        
        posts.append(post)
        print(f"  ✅ Created post: '{post.title[:50]}...' with {comment_count} comments")
    
    db.commit()
    print(f"✅ Created {len(posts)} forum posts successfully!")
    return posts


def create_simulator_results(db: Session, users: List[User], count: int = 50) -> List[SimulatorResult]:
    """Create simulator results for leaderboard"""
    print(f"\n🎮 Creating {count} simulator results...")
    
    results = []
    base_date = datetime.now() - timedelta(days=90)
    
    for i in range(count):
        user = random.choice(users)
        pair = random.choice(TRADING_PAIRS)
        
        # Generate realistic dates
        start_date = fake.date_time_between(start_date=base_date, end_date="now")
        end_date = start_date + timedelta(days=random.randint(1, 30))
        
        # Generate realistic prices based on pair
        if "BTC" in pair:
            base_price = random.uniform(30000, 70000)
        elif "ETH" in pair:
            base_price = random.uniform(2000, 4000)
        elif "SOL" in pair:
            base_price = random.uniform(50, 200)
        else:
            base_price = random.uniform(0.5, 5.0)
        
        entry_price = base_price
        stop_loss = entry_price * random.uniform(0.85, 0.95)  # 5-15% below entry
        take_profit = entry_price * random.uniform(1.05, 1.50)  # 5-50% above entry
        
        # Determine outcome
        pnl_percent = random.uniform(-20, 500)  # -20% to +500%
        
        if pnl_percent > 0:
            # Win - hit take profit
            exit_price = entry_price * (1 + pnl_percent / 100)
            is_win = True
            hit_type = "TP"
        else:
            # Loss - hit stop loss
            exit_price = entry_price * (1 + pnl_percent / 100)
            is_win = False
            hit_type = "SL"
        
        result = SimulatorResult(
            user_id=user.id,
            username=user.username,
            pair=pair,
            start_date=start_date,
            end_date=end_date,
            entry_price=round(entry_price, 2),
            stop_loss=round(stop_loss, 2),
            take_profit=round(take_profit, 2),
            exit_price=round(exit_price, 2),
            pnl_percent=round(pnl_percent, 2),
            is_win=is_win,
            hit_type=hit_type,
            created_at=fake.date_time_between(start_date=end_date, end_date="now")
        )
        db.add(result)
        results.append(result)
        
        if (i + 1) % 10 == 0:
            print(f"  ✅ Created {i + 1}/{count} results...")
    
    db.commit()
    print(f"✅ Created {len(results)} simulator results successfully!")
    return results


def clear_database(db: Session):
    """Clear all data from database (optional)"""
    print("\n🗑️  Clearing existing data...")
    
    # Delete in reverse order of dependencies
    db.query(ForumVote).delete()
    db.query(ForumComment).delete()
    db.query(ForumPost).delete()
    db.query(SimulatorResult).delete()
    # Keep categories, users, wallets, reputation
    
    db.commit()
    print("✅ Database cleared!")


def main():
    """Main seeding function"""
    print("=" * 80)
    print("🌱 Database Seeding Script")
    print("=" * 80)
    
    # Ask for confirmation
    response = input("\n⚠️  This will add mock data to your database. Continue? (yes/no): ").strip().lower()
    if response not in ['yes', 'y']:
        print("❌ Seeding cancelled.")
        return
    
    # Ask about clearing
    clear_response = input("\n🗑️  Clear existing forum posts and simulator results? (yes/no): ").strip().lower()
    should_clear = clear_response in ['yes', 'y']
    
    db = SessionLocal()
    
    try:
        if should_clear:
            clear_database(db)
        
        # Create users
        users = create_users(db, count=25)
        
        if not users:
            print("❌ No users created. Exiting.")
            return
        
        # Create forum categories
        categories = create_forum_categories(db)
        
        # Create forum posts
        posts = create_forum_posts(db, users, categories, count=25)
        
        # Create simulator results
        results = create_simulator_results(db, users, count=50)
        
        print("\n" + "=" * 80)
        print("✅ Seeding completed successfully!")
        print("=" * 80)
        print(f"\n📊 Summary:")
        print(f"  • Users: {len(users)}")
        print(f"  • Forum Categories: {len(categories)}")
        print(f"  • Forum Posts: {len(posts)}")
        print(f"  • Simulator Results: {len(results)}")
        print(f"\n🔑 Default password for all users: password123")
        print(f"👤 Admin user: {users[0].username if users else 'N/A'}")
        print("\n" + "=" * 80)
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

