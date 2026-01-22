# Open Source Voice Trading Setup (No API Keys!)

This guide will help you set up the Voice Trading Assistant using 100% open-source tools that run locally on your machine. No API keys, no costs, complete privacy!

## 🎯 What You'll Install

1. **Faster-Whisper** - Speech-to-text (replaces OpenAI Whisper API)
2. **Ollama** - Local LLM for command parsing (replaces OpenAI)
3. **Python Dependencies** - For audio transcription
4. **Node.js Dependencies** - For backend integration

---

## 📦 Step 1: Install Faster-Whisper

Faster-Whisper is an optimized implementation of Whisper that runs locally.

```powershell
# Install Python dependencies
pip install faster-whisper

# The model will download automatically on first use
# Model sizes available: tiny, base, small, medium, large-v2, large-v3
# Default: "base" (good balance of speed/accuracy)
```

### Model Sizes:

- **tiny** (39M params): Fastest, less accurate - good for testing
- **base** (74M params): ⭐ **Recommended** - Good balance
- **small** (244M params): Better accuracy, slower
- **medium** (769M params): High accuracy, needs more RAM
- **large-v3** (1550M params): Best accuracy, very slow

---

## 🦙 Step 2: Install Ollama

Ollama lets you run large language models locally.

### Download & Install:

```powershell
# Option 1: Download from website
# Visit: https://ollama.ai/download/windows
# Download and run the installer

# Option 2: Use winget
winget install Ollama.Ollama
```

### Pull a Model:

```powershell
# Choose ONE of these models (or try multiple):

# Llama 2 (7B) - Good general purpose ⭐ Recommended
ollama pull llama2

# Mistral (7B) - Faster, great accuracy
ollama pull mistral

# Llama 3 (8B) - Latest and best quality
ollama pull llama3

# Code Llama (7B) - Better for structured parsing
ollama pull codellama
```

### Verify Ollama is Running:

```powershell
# Test Ollama API
curl http://localhost:11434/api/generate -d '{
  "model": "llama2",
  "prompt": "Say hello",
  "stream": false
}'
```

---

## 🔧 Step 3: Install Node.js Dependencies

```powershell
# Navigate to server directory
cd server

# Install axios (only dependency needed now!)
npm install axios

# Optional: Remove old dependencies
npm uninstall openai node-llama-cpp
```

---

## 🐍 Step 4: Verify Python Script

The transcription script should already be created at:
`server/scripts/transcribe.py`

Test it manually:

```powershell
# Test transcription (create a test audio file first)
python server\scripts\transcribe.py path\to\test-audio.webm
```

---

## ⚙️ Step 5: Configure Environment Variables

Create or update your `.env` file in the `server/` directory:

```env
# Ollama Configuration (local, no API key needed!)
OLLAMA_API_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Remove these (not needed anymore):
# OPENAI_API_KEY=...
# LLAMA_MODEL_PATH=...
```

---

## 🚀 Step 6: Start Your Application

```powershell
# Start the backend server
cd server
npm start

# In another terminal, start the frontend
cd ..
npm start
```

---

## 🧪 Testing the Voice Assistant

### Test 1: Check Ollama is Running

```powershell
curl http://localhost:11434/api/tags
# Should return list of installed models
```

### Test 2: Test Transcription Endpoint

```powershell
# Record a short audio clip and test
curl -X POST http://localhost:3001/api/voice/transcribe `
  -F "audio=@recording.webm"
```

### Test 3: Test Command Parsing

```powershell
curl -X POST http://localhost:3001/api/voice/parse-command `
  -H "Content-Type: application/json" `
  -d '{"transcript":"buy 0.5 BTC at market price"}'
```

### Test 4: Use the UI

1. Open your app in the browser
2. Click the microphone button
3. Say: "Buy 0.5 Bitcoin at market price"
4. Watch it transcribe and parse!

---

## 📊 Performance Comparison

| Component       | API Version    | Open Source     | Speed   | Privacy  |
| --------------- | -------------- | --------------- | ------- | -------- |
| Speech-to-Text  | OpenAI Whisper | Faster-Whisper  | ✅ Fast | ✅ Local |
| Command Parsing | OpenAI GPT-4   | Ollama (Llama2) | ✅ Fast | ✅ Local |
| Cost            | $$$ per call   | FREE            | ∞       | 100%     |
| Internet        | Required       | Optional        | -       | ✅       |

---

## 🎯 Example Voice Commands

Try these commands to test the system:

```
✅ "Buy 0.5 Bitcoin at market price"
✅ "Sell 2 Ethereum at market price"
✅ "Create a buy order for 100 USDT"
✅ "Sell 1 BTC at limit price 50000"
✅ "Cancel all open orders"
✅ "Purchase 0.1 ETH at market"
```

---

## 🐛 Troubleshooting

### Issue: Python script fails

```powershell
# Check Python version
python --version  # Should be 3.8+

# Reinstall faster-whisper
pip install --upgrade faster-whisper
```

### Issue: Ollama connection refused

```powershell
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Restart Ollama
# Close and reopen Ollama app, or:
ollama serve
```

### Issue: Model not found

```powershell
# List installed models
ollama list

# Pull the model
ollama pull llama2
```

### Issue: Transcription is slow

Change model size in `server/scripts/transcribe.py`:

```python
# Line 17: Change from "base" to "tiny" for faster speed
model_size = "tiny"  # Faster but less accurate
```

---

## 🔥 Advanced Configuration

### Use GPU for Faster Transcription

If you have an NVIDIA GPU:

```python
# In transcribe.py, change line 20:
model = WhisperModel(model_size, device="cuda", compute_type="float16")
```

### Switch Ollama Models Dynamically

Update `.env`:

```env
# Use different models for different tasks
OLLAMA_MODEL=mistral  # Faster
# or
OLLAMA_MODEL=llama3   # More accurate
```

### Fine-tune Command Parsing

Edit the prompt in `server/routes/voiceRoutes.js` (line ~90) to customize parsing behavior.

---

## ✅ Advantages of This Setup

✅ **100% Open Source** - No proprietary APIs
✅ **Complete Privacy** - All processing happens locally
✅ **Zero Cost** - No API fees ever
✅ **Offline Capable** - Works without internet (after initial model download)
✅ **Fast** - No network latency
✅ **Customizable** - Full control over models and behavior
✅ **Unlimited Usage** - No rate limits or quotas

---

## 📚 Additional Resources

- **Faster-Whisper**: https://github.com/guillaumekln/faster-whisper
- **Ollama**: https://ollama.ai/
- **Ollama Models**: https://ollama.ai/library
- **Whisper Models**: https://huggingface.co/guillaumekln/faster-whisper-large-v2

---

## 🎉 You're All Set!

Your Voice Trading Assistant is now running completely open-source with:

- ✅ Local speech recognition
- ✅ Local AI command parsing
- ✅ No API keys
- ✅ Complete privacy
- ✅ Zero costs

Happy voice trading! 🎤📈
