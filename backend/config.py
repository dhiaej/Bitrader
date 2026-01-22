from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Application Settings
    APP_NAME: str = "Bitrader"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database - SQLite (for easy testing, change to MySQL for production)
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "password"
    DB_NAME: str = "trading_simulator"
    
    # Media / uploads
    MEDIA_ROOT: str = "uploads"
    MEDIA_URL: str = "/uploads"
    
    @property
    def DATABASE_URL(self) -> str:
        # Use SQLite for easy testing
        return "sqlite:///./trading_simulator.db"
        # For MySQL, uncomment below:
        # return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-this-in-production-2024"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:4200", "http://localhost:8000"]
    
    # Initial Balances (Fake Money for Game)
    INITIAL_USD_BALANCE: float = 10000.00
    INITIAL_BTC_BALANCE: float = 0.5
    INITIAL_ETH_BALANCE: float = 5.0
    INITIAL_USDT_BALANCE: float = 5000.00
    
    # Trading Fees
    TRADING_FEE_PERCENTAGE: float = 0.1  # 0.1%
    P2P_FEE_PERCENTAGE: float = 0.0  # No fee for P2P
    
    # Order Book Settings
    MAX_ORDERS_PER_USER: int = 100
    ORDER_EXPIRY_HOURS: int = 24
    
    # P2P Settings
    MIN_TRADE_AMOUNT: float = 10.00
    MAX_TRADE_AMOUNT: float = 50000.00
    PAYMENT_TIMEOUT_MINUTES: int = 30
    ESCROW_RELEASE_DELAY_SECONDS: int = 5
    
    # Reputation Settings
    INITIAL_REPUTATION_SCORE: int = 100
    MAX_REPUTATION_SCORE: int = 1000
    REPUTATION_TRADE_SUCCESS_POINTS: int = 5
    REPUTATION_TRADE_CANCEL_PENALTY: int = 3
    REPUTATION_DISPUTE_PENALTY: int = 10
    REPUTATION_REVIEW_WEIGHT: int = 2
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30
    
    # AI / External APIs
    OPENAI_API_KEY: str = ""  # OpenAI API key for course generation (primary)
    GROQ_API_KEY: str = ""
    GEMINI_API_KEY: str = ""  # Google Gemini API key for formations and chat
    FINNHUB_API_KEY: str = ""
    COINDESK_API_KEY: str = ""  # Optional, for news in AI indicator insights (11k/month limit)
    
    # Suspicious Detection / ML
    SUSPICIOUS_MODEL_PATH: str = "models/suspicious_isoforest.pkl"
    SUSPICIOUS_FEATURES_PATH: str = "models/suspicious_features.json"
    SUSPICIOUS_ALERT_THRESHOLD: float = 40.0
    SUSPICIOUS_RULE_WEIGHT: float = 0.4
    SUSPICIOUS_ML_WEIGHT: float = 0.6
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()