# 🚀 Bitrader - Advanced Trading Platform

A comprehensive full-stack cryptocurrency trading platform with simulation capabilities, P2P marketplace, AI-powered features, and real-time market data. Built with **Python FastAPI** backend and **Angular** frontend.

## ✨ Features

### Core Trading Features
- 📊 **Order Book Engine** - Automatic matching with price-time priority
- 💱 **P2P Marketplace** - Binance-style peer-to-peer trading
- 💰 **Multi-currency Wallet** - Support for USD, BTC, ETH, USDT, and more
- 🔒 **Escrow System** - Secure trade execution with dispute resolution
- ⭐ **Reputation System** - User ratings and reviews
- 📈 **Trading Simulator** - Practice trading with virtual funds

### Advanced Features
- 🤖 **AI Trading Assistant** - Get trading insights and recommendations
- 📊 **Price Predictions** - AI-powered price forecasting
- 📰 **Market News** - Real-time cryptocurrency news aggregation
- 📈 **Technical Indicators** - Advanced chart analysis tools
- 🎓 **Educational Content** - Trading courses and formations
- 💬 **Community Forum** - Discuss trading strategies
- 🎤 **Voice Trading** - Voice-activated trading commands (optional)

## 🏗️ Architecture

```
Bitrader/
├── backend/          # FastAPI Python backend
│   ├── models/       # SQLAlchemy database models
│   ├── routers/      # API route handlers
│   ├── services/     # Business logic services
│   ├── scripts/      # Utility and setup scripts
│   └── tests/        # Test files
├── frontend/         # Angular TypeScript frontend
├── server/           # Node.js voice server (optional)
└── guid/            # Documentation and guides
```

## 📋 Prerequisites

- **Python 3.10+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** and npm - [Download](https://nodejs.org/)
- **MySQL 8.0+** (or SQLite for development) - [Download](https://dev.mysql.com/downloads/)
- **Angular CLI** - `npm install -g @angular/cli`
- **Git** - [Download](https://git-scm.com/)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/bitrader.git
cd bitrader
```

### 2. Backend Setup

```powershell
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment (create .env file)
# Copy .env.example to .env and update with your settings

# Initialize database
python init_db.py

# (Optional) Seed with test data
python scripts/seed_db.py

# Start backend server
python main.py
# Or use: uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`  
API Documentation: `http://localhost:8000/docs`

### 3. Frontend Setup

```powershell
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Configure API endpoint in src/environments/environment.ts
# Set apiUrl: "http://localhost:8000/api"

# Start development server
ng serve
```

Frontend will be available at: `http://localhost:4200`

## ⚙️ Configuration

### Backend Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=trading_simulator

# Security
SECRET_KEY=your-secret-key-change-this-in-production

# API Keys (Optional - for advanced features)
GEMINI_API_KEY=your-gemini-api-key
OPENAI_API_KEY=your-openai-api-key
GROQ_API_KEY=your-groq-api-key
```

### Frontend Environment

Edit `frontend/src/environments/environment.ts`:

```typescript
export const environment = {
  production: false,
  apiUrl: "http://localhost:8000/api",
  wsUrl: "ws://localhost:8000/ws",
};
```

## 📚 Documentation

Comprehensive documentation is available in the `guid/` directory:

- **[QUICKSTART.md](guid/QUICKSTART.md)** - Quick setup guide
- **[ARCHITECTURE.md](guid/ARCHITECTURE.md)** - System architecture
- **[API_TESTING_GUIDE.md](guid/API_TESTING_GUIDE.md)** - API testing instructions
- **[P2P_MARKETPLACE_GUIDE.md](guid/P2P_MARKETPLACE_GUIDE.md)** - P2P trading guide
- **[AI_ASSISTANT_SETUP_GUIDE.md](guid/AI_ASSISTANT_SETUP_GUIDE.md)** - AI features setup
- **[VOICE_SETUP_OPENSOURCE.md](guid/VOICE_SETUP_OPENSOURCE.md)** - Voice trading setup

## 🎮 First Time Usage

### Create an Account

1. Open `http://localhost:4200`
2. Click "Register"
3. Fill in username, email, and password
4. Submit registration

### Initial Balance

After registration, you'll automatically receive:
- **$10,000 USD** (virtual money for simulation)
- **0.5 BTC**
- **5.0 ETH**
- **5,000 USDT**

### Start Trading

**Order Book Trading:**
1. Navigate to "Trading" or "Order Book"
2. Select instrument (BTC/USD, ETH/USD, etc.)
3. Place buy/sell orders
4. Watch automatic matching!

**P2P Trading:**
1. Go to "P2P Marketplace"
2. Browse or create advertisements
3. Initiate trades with escrow protection
4. Complete transactions securely

## 🛠️ Development

### Running Tests

```bash
# Backend tests
cd backend
pytest tests/

# Frontend tests
cd frontend
ng test
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

### Code Structure

- **Backend**: Follows FastAPI best practices with routers, services, and models
- **Frontend**: Angular modular architecture with feature modules
- **Services**: Business logic separated into service classes
- **Models**: SQLAlchemy ORM models for database operations

## 📊 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user

### Wallet
- `GET /api/wallet/balances` - Get all balances
- `POST /api/wallet/deposit` - Deposit funds
- `POST /api/wallet/withdraw` - Withdraw funds
- `POST /api/wallet/transfer` - Transfer to user
- `GET /api/wallet/transactions` - Transaction history

### Trading
- `POST /api/orderbook/orders` - Place order
- `GET /api/orderbook/orders` - Get user orders
- `DELETE /api/orderbook/orders/{id}` - Cancel order
- `GET /api/orderbook/orderbook/{instrument}` - Get order book
- `GET /api/orderbook/trades` - Get trade history

### P2P Marketplace
- `POST /api/p2p/advertisements` - Create ad
- `GET /api/p2p/advertisements` - Browse ads
- `POST /api/p2p/trades` - Initiate trade
- `POST /api/p2p/trades/{id}/payment-sent` - Mark payment sent
- `POST /api/p2p/trades/{id}/confirm-payment` - Confirm payment

### AI Features
- `POST /api/ai-assistant/chat` - Chat with AI assistant
- `GET /api/price-prediction/predictions` - Get price predictions
- `GET /api/indicator-insights/insights` - Get technical insights

See full API documentation at `http://localhost:8000/docs` when the backend is running.

## 🔒 Security

- JWT-based authentication
- Password hashing with bcrypt
- SQL injection protection (SQLAlchemy ORM)
- CORS configuration
- Input validation with Pydantic
- Escrow system for secure P2P trades

## 🐛 Troubleshooting

### MySQL Connection Error
- Ensure MySQL service is running
- Check credentials in `.env`
- Verify database exists: `SHOW DATABASES;`

### Port Already in Use
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID)
taskkill /PID <PID> /F
```

### Python Module Not Found
```powershell
# Ensure virtual environment is activated
.\venv\Scripts\Activate.ps1

# Reinstall requirements
pip install -r requirements.txt
```

### Angular Build Errors
```powershell
# Clear node modules and reinstall
Remove-Item -Recurse -Force node_modules
Remove-Item package-lock.json
npm install
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Frontend powered by [Angular](https://angular.io/)
- Market data from [CoinGecko](https://www.coingecko.com/) and [Binance](https://www.binance.com/)
- AI features powered by Google Gemini, OpenAI, and Groq

## 📞 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check the documentation in `guid/` directory
- Review API documentation at `/docs` endpoint

---

**Happy Trading! 🚀💰**
