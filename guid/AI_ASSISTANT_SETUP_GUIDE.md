# 🤖 AI Trading Assistant - Setup Guide

## Overview
The AI Trading Assistant is a GPT-4o powered chatbot integrated into your P2P trading platform. It provides context-aware trading advice, market analysis, and platform guidance.

## ✅ What's Already Completed

### Backend (100% Complete)
- ✅ AI Assistant Service (`backend/services/ai_assistant_service.py`)
  - OpenAI GPT-4o integration
  - Context-aware responses using user wallet data and market prices
  - Conversation history management
  - Quick suggestion system
  
- ✅ ChatMessage Database Model (`backend/models/chat_message.py`)
  - Stores conversation history
  - Indexed for fast retrieval
  - Linked to User model

- ✅ AI Assistant Router (`backend/routers/ai_assistant.py`)
  - POST `/api/ai/chat` - Send messages
  - GET `/api/ai/chat/history` - Retrieve conversation
  - DELETE `/api/ai/chat/history` - Clear history
  - GET `/api/ai/suggestions/{type}` - Quick suggestions

- ✅ Dependencies Updated (`backend/requirements.txt`)
  - openai==1.12.0
  - yfinance==0.2.36
  - requests==2.31.0

- ✅ Configuration (`backend/config.py`)
  - OPENAI_API_KEY setting added

- ✅ Main Application (`backend/main.py`)
  - AI router included in app

### Frontend (100% Complete)
- ✅ AI Assistant Service (`frontend/src/app/core/services/ai-assistant.service.ts`)
  - HTTP methods for chat API
  - TypeScript interfaces for type safety

- ✅ Chat Widget Component (`frontend/src/app/shared/components/ai-chat-widget/`)
  - Beautiful floating chat button
  - Expandable chat window
  - Message history with auto-scroll
  - Typing indicators
  - Quick suggestion buttons
  - Responsive design

- ✅ Dashboard Integration
  - Chat widget added to dashboard

## 🚀 Setup Instructions

### Step 1: Install Python Dependencies
```powershell
cd backend
pip install -r requirements.txt
```

### Step 2: Get OpenAI API Key
1. Go to https://platform.openai.com/
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key (it starts with `sk-...`)

### Step 3: Configure Environment Variable
Create or update `.env` file in the `backend/` directory:

```env
# Existing settings...
DATABASE_URL=sqlite:///./trading.db
SECRET_KEY=your-secret-key-here

# Add this line for AI Assistant
OPENAI_API_KEY=sk-your-actual-api-key-here
```

**Important:** Replace `sk-your-actual-api-key-here` with your actual OpenAI API key.

### Step 4: Initialize Database
The ChatMessage table will be created automatically when you start the backend:

```powershell
cd backend
python main.py
```

You should see:
```
🚀 Starting P2P Trading Simulator...
✅ Database tables created
📊 Market data service started - fetching real-time prices...
```

### Step 5: Start Frontend
```powershell
cd frontend
npm start
```

## 🎯 How to Use

### For Users
1. Open the dashboard
2. Click the floating chat button (💬) in the bottom-right corner
3. Use quick suggestions or type your own questions:
   - "What's the current BTC price trend?"
   - "Should I buy or sell ETH right now?"
   - "Analyze my portfolio"
   - "What are the risks of P2P trading?"
   - "How do I create a P2P advertisement?"

### Quick Suggestions
- **📊 Market Analysis** - Get current market trends
- **💡 Trading Tip** - Receive personalized trading advice
- **⚠️ Risk Assessment** - Understand your portfolio risks

### Features
- **Context-Aware:** AI knows your wallet balances and current market prices
- **Conversation Memory:** Maintains chat history for continuity
- **Real-time Data:** Always uses latest market information
- **Secure:** All chats are stored per-user and authenticated

## 🔧 Troubleshooting

### Issue: "OpenAI API key not configured"
**Solution:** Make sure you've added `OPENAI_API_KEY` to your `.env` file and restarted the backend.

### Issue: Chat widget doesn't appear
**Solution:** 
1. Check browser console for errors
2. Make sure frontend is running: `npm start`
3. Verify the component is imported in dashboard.component.ts

### Issue: AI responses are slow
**Solution:** This is normal - GPT-4o can take 3-10 seconds to respond depending on context complexity.

### Issue: "Rate limit exceeded"
**Solution:** OpenAI has usage limits. Check your OpenAI dashboard for rate limits and billing.

## 💰 OpenAI API Costs

### Pricing (as of 2024)
- GPT-4o: $0.005 per 1K input tokens, $0.015 per 1K output tokens
- Average chat message: ~500-1000 tokens (input + output)
- Estimated cost per message: $0.01 - $0.02

### Free Tier
- New OpenAI accounts get $5 free credit
- Approximately 250-500 chat messages with your setup

### Tips to Reduce Costs
1. Use shorter questions
2. Clear chat history periodically
3. Monitor usage in OpenAI dashboard
4. Set spending limits in OpenAI account settings

## 🧪 Testing

### Test the AI Assistant
1. Start both backend and frontend
2. Login to your account
3. Open dashboard
4. Click chat widget
5. Try these test messages:
   - "Hello!"
   - "What's my BTC balance?"
   - "Analyze the current market"
   - "Give me a trading tip"

### Expected Behavior
- AI should respond within 3-10 seconds
- Responses should mention your actual wallet balances
- Market data should reflect current prices
- Conversation history should persist between page reloads

## 📊 AI Capabilities

The AI assistant can help with:
- **Market Analysis:** Current trends, price predictions, technical indicators
- **Portfolio Advice:** Balance recommendations, diversification tips
- **Risk Management:** Risk assessment, stop-loss suggestions
- **Platform Help:** How to use P2P, order book, wallet features
- **Trading Education:** Explain crypto concepts, trading strategies
- **Real-time Data:** Current prices, 24h changes, market cap info

## 🎨 Customization

### Change AI Personality
Edit `backend/services/ai_assistant_service.py`:
```python
def _get_system_prompt(self) -> str:
    return """You are a [your custom personality here]..."""
```

### Adjust Response Length
Edit `backend/services/ai_assistant_service.py`:
```python
response = self.client.chat.completions.create(
    model="gpt-4o",
    max_tokens=500,  # Change this number (100-2000)
    temperature=0.7,  # Change this (0.0-2.0, lower = more focused)
    messages=messages
)
```

### Change Widget Position
Edit `frontend/src/app/shared/components/ai-chat-widget/ai-chat-widget.component.scss`:
```scss
.ai-chat-widget {
  position: fixed;
  bottom: 20px;  // Change vertical position
  right: 20px;   // Change horizontal position
}
```

## 🔐 Security Notes

- ✅ All API calls are authenticated (requires login)
- ✅ Each user has isolated chat history
- ✅ OpenAI API key is server-side only (never exposed to frontend)
- ✅ Chat messages are stored in database with user_id
- ⚠️ Don't share your OpenAI API key
- ⚠️ Monitor your OpenAI usage dashboard regularly

## 📝 Next Steps

### Optional Enhancements
1. **Voice Input:** Add speech-to-text for voice queries
2. **Export Chat:** Add button to download chat history
3. **Suggested Questions:** Display common questions to new users
4. **Typing Preview:** Show AI writing in real-time
5. **Multi-language:** Add language selection
6. **Advanced Charts:** Integrate price charts in responses
7. **Push Notifications:** Alert users when AI has important market insights

## 🆘 Support

If you encounter issues:
1. Check backend console for errors
2. Check frontend browser console
3. Verify OpenAI API key is correct
4. Check OpenAI account has credits
5. Restart both backend and frontend

## 📚 Documentation Links

- [OpenAI API Docs](https://platform.openai.com/docs)
- [GPT-4o Model Info](https://platform.openai.com/docs/models/gpt-4o)
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [Angular HTTP Client](https://angular.io/guide/http)

---

## ✨ You're All Set!

The AI Trading Assistant is fully implemented and ready to use. Just add your OpenAI API key and start chatting!

**Default Test Account:**
- Username: `testuser`
- Password: `password123`

Happy Trading! 🚀📈
