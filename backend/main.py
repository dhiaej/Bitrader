"""
Bitrader - Main FastAPI Application
Author: Bitrader Team
Description: Advanced cryptocurrency trading platform with simulation, P2P marketplace, and AI features
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from pathlib import Path
import uvicorn
import traceback

from database import engine, Base, get_db
from routers import (
    auth,
    wallet,
    orderbook,
    p2p,
    escrow,
    dispute,
    reputation,
    user,
    market_data,
    ai_assistant,
    price_prediction,
    trading,
    indicator_insights,
    simulator,
    admin,
    forum,
    formations,
)
from services.websocket_manager import WebSocketManager
from services.orderbook_service import OrderBookService
from services.market_data_service import market_data_service
from services.price_prediction_service import price_prediction_service
from services.ad_expiration_service import ad_expiration_service
from config import settings
import logging

logger = logging.getLogger(__name__)

try:
    # Optional dependency; backend can run without scheduler if not installed
    from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore
except ImportError:
    BackgroundScheduler = None  # type: ignore
    logger.warning(
        "apscheduler is not installed. Background price history collection "
        "will be disabled. Install 'apscheduler' to enable it."
    )

# Initialize WebSocket manager and OrderBook service
ws_manager = WebSocketManager()
orderbook_service = OrderBookService(ws_manager)

# Initialize background scheduler for price history collection (if available)
scheduler = BackgroundScheduler() if BackgroundScheduler is not None else None

def collect_all_price_history():
    """Background task to collect price history every 30 minutes"""
    from database import SessionLocal
    import asyncio
    db = SessionLocal()
    try:
        for symbol in ["BTC", "ETH", "LTC", "SOL", "DOGE"]:
            asyncio.run(price_prediction_service.collect_historical_data(db, symbol))
        logger.info("Price history collection completed")
    except Exception as e:
        logger.error(f"Error in price history collection: {e}")
    finally:
        db.close()

def refresh_news_cache():
    """Background task to refresh news cache every 10 minutes"""
    from services.news_service import news_service
    try:
        # Refresh news for all tracked symbols
        symbols = ["BTC-USD", "ETH-USD", "LTC-USD", "SOL-USD", "DOGE-USD"]
        for symbol in symbols:
            try:
                # Clear cache entry to force fresh fetch
                cache_key = symbol.upper()
                if cache_key in news_service._cache:
                    del news_service._cache[cache_key]
                # This will fetch fresh news and update the cache
                news_service.get_symbol_news(symbol, limit=5)
                logger.debug(f"Refreshed news cache for {symbol}")
            except Exception as e:
                logger.error(f"Error refreshing news for {symbol}: {e}")
        logger.info("News cache refresh completed")
    except Exception as e:
        logger.error(f"Error in news cache refresh: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    print("🚀 Starting Bitrader...")
    
    # Create media directories
    Path(settings.MEDIA_ROOT).mkdir(parents=True, exist_ok=True)
    (Path(settings.MEDIA_ROOT) / "avatars").mkdir(parents=True, exist_ok=True)
    (Path(settings.MEDIA_ROOT) / "videos").mkdir(parents=True, exist_ok=True)
    (Path(settings.MEDIA_ROOT) / "certificates").mkdir(parents=True, exist_ok=True)
    print("📁 Media directories created")
    
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")
    
    # Check Face Recognition service
    try:
        from services.face_recognition_service import DEEPFACE_AVAILABLE
        if DEEPFACE_AVAILABLE:
            print("✅ Face recognition service available (DeepFace loaded)")
        else:
            print("⚠️  Face recognition service NOT available - DeepFace not loaded")
            print("   Install with: pip install deepface")
    except Exception as e:
        logger.warning(f"Could not check face recognition service: {e}")
    
    # Start market data service to fetch real-time prices
    market_data_service.start()
    print("📊 Market data service started - fetching real-time prices...")
    
    # Start ad expiration service
    await ad_expiration_service.start()
    print("⏰ Ad expiration service started - checking every 60 seconds...")
    
    # Start price history collection scheduler (if available)
    if scheduler is not None:
        scheduler.add_job(collect_all_price_history, 'interval', minutes=30)
        scheduler.add_job(refresh_news_cache, 'interval', minutes=10)
        scheduler.start()
        print("🔮 Price prediction service started - collecting historical data...")
        print("📰 News refresh service started - updating news cache every 10 minutes...")
    else:
        print("⚠️ APScheduler not installed - price history background collection is disabled.")
        print("⚠️ APScheduler not installed - news background refresh is disabled.")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Bitrader...")
    market_data_service.stop()
    print("📊 Market data service stopped")
    await ad_expiration_service.stop()
    print("⏰ Ad expiration service stopped")
    if scheduler is not None:
        scheduler.shutdown()
        print("🔮 Price prediction service stopped")

app = FastAPI(
    title="P2P Trading Simulator API",
    description="Complete trading platform with order book and P2P exchange",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - MUST be added before other middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS, # ["http://localhost:4200"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handler to ensure CORS headers are sent even on errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to ensure CORS headers are always sent"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.DEBUG else "An error occurred"
        },
        headers={
            "Access-Control-Allow-Origin": settings.CORS_ORIGINS[0] if settings.CORS_ORIGINS else "*",
            "Access-Control-Allow-Credentials": "true",
        }
    )

# Mount static files for media uploads
app.mount(
    settings.MEDIA_URL,
    StaticFiles(directory=settings.MEDIA_ROOT),
    name="uploads"
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(user.router, prefix="/api/users", tags=["Users"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(wallet.router, prefix="/api/wallet", tags=["Wallet"])
app.include_router(orderbook.router, prefix="/api/orderbook", tags=["Order Book"])
app.include_router(p2p.router, prefix="/api/p2p", tags=["P2P Trading"])
app.include_router(escrow.router, prefix="/api/escrow", tags=["Escrow"])
app.include_router(dispute.router, prefix="/api/disputes", tags=["Disputes"])
app.include_router(reputation.router, prefix="/api/reputation", tags=["Reputation"])
app.include_router(market_data.router, prefix="/api/market", tags=["Market Data"])
app.include_router(trading.router) # New trading router
app.include_router(ai_assistant.router, prefix="/api/ai", tags=["AI Assistant"])
app.include_router(indicator_insights.router)
app.include_router(price_prediction.router, tags=["Price Predictions"])
app.include_router(simulator.router)  # Trading Simulator / Backtesting Game
app.include_router(forum.router, prefix="/api", tags=["Forum"])
app.include_router(formations.router, prefix="/api/formations", tags=["Formations"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "P2P Trading Simulator API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "operational"
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "trading-api"}

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time updates"""
    await ws_manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming WebSocket messages
            await ws_manager.handle_message(client_id, data)
    except WebSocketDisconnect:
        ws_manager.disconnect(client_id)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
