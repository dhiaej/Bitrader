# 🚀 AI Trading Assistant - Quick Start

## ⚡ Get Started in 3 Steps

### Step 1: Get OpenAI API Key (2 minutes)
1. Visit https://platform.openai.com/api-keys
2. Sign up or login
3. Click "Create new secret key"
4. Copy the key (starts with `sk-...`)

### Step 2: Add API Key (30 seconds)
Open `backend/.env` and replace:
```env
OPENAI_API_KEY=sk-your-openai-api-key-here
```
With your actual key:
```env
OPENAI_API_KEY=sk-proj-abc123xyz...
```

### Step 3: Start Servers (1 minute)

**Terminal 1 - Backend:**
```powershell
cd backend
python main.py
```

**Terminal 2 - Frontend:**
```powershell
cd frontend
npm start
```

---

## ✅ Test It Out!

1. Open http://localhost:4200
2. Login (testuser / password123)
3. Look for the 💬 button in bottom-right
4. Click it and type: "Hello!"
5. Wait 3-10 seconds for response

---

## 💬 Try These Questions:

- "What's my BTC balance?"
- "Analyze the current market"
- "Should I buy or sell ETH?"
- "Give me a trading tip"
- "What are the risks in my portfolio?"
- "How do I use P2P trading?"

---

## 🎯 Features:
- ✅ Knows your wallet balances
- ✅ Real-time crypto prices
- ✅ Context-aware advice
- ✅ Conversation memory
- ✅ Beautiful UI
- ✅ Quick suggestions

---

## 🆘 Having Issues?

**Widget doesn't appear?**
- Make sure frontend is running
- Hard refresh browser (Ctrl+Shift+R)

**"API key not configured" error?**
- Check your .env file
- Restart the backend

**Slow responses?**
- Normal! GPT-4o takes 3-10 seconds
- Check your internet connection

---

## 💰 Free Tier Info:
- New OpenAI accounts get $5 free credit
- Each message costs ~$0.01
- You get approximately 250-500 free messages
- Monitor usage: https://platform.openai.com/usage

---

**That's it! You're ready to use the AI Trading Assistant! 🎉**

For detailed docs, see `AI_ASSISTANT_SETUP_GUIDE.md`
