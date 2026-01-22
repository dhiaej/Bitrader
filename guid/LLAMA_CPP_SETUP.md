# llama.cpp Setup Guide

The backend has been configured to use llama.cpp instead of Ollama/Groq for local AI processing.

## Current Configuration

The system now works in **two modes**:

### 1. **Simple Fallback Mode (Active by Default)**
- ✅ No external dependencies required
- ✅ Works immediately without any model download
- ⚠️ Provides rule-based responses (not true AI)
- Good for: Testing the platform, basic Q&A

### 2. **Full AI Mode (Optional - Requires Setup)**
- 🎯 True AI-powered responses
- 📦 Requires llama.cpp installation
- 💾 Requires model download (4-7GB)

## Quick Start (Current Status)

Your backend is **ready to run** in Simple Fallback Mode:

```powershell
cd backend
conda activate pi3
python main.py
```

The AI assistant will work with basic rule-based responses.

## Upgrade to Full AI Mode (Optional)

If you want true AI responses, follow these steps:

### Step 1: Download llama.cpp for Windows

1. Download precompiled binary:
   ```powershell
   # Option A: Download from releases
   # Visit: https://github.com/ggerganov/llama.cpp/releases
   # Download: llama-<version>-bin-win-avx2-x64.zip
   
   # Extract to C:\llama.cpp\
   ```

2. OR build from source (requires Visual Studio):
   ```powershell
   git clone https://github.com/ggerganov/llama.cpp.git C:\llama.cpp
   cd C:\llama.cpp
   cmake -B build
   cmake --build build --config Release
   ```

### Step 2: Download a Model

Download a Llama 2 model (GGUF format):

```powershell
# Create models directory
mkdir C:\llama.cpp\models

# Download Llama 2 7B Chat (Q4 quantization - ~4GB)
# Visit: https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF

# Download: llama-2-7b-chat.Q4_K_M.gguf
# Save to: C:\llama.cpp\models\
```

**Recommended Models:**
- **Llama 2 7B Q4**: 4GB, fast, good quality
- **Llama 2 7B Q5**: 5GB, slower, better quality
- **Llama 2 13B Q4**: 7GB, slower, best quality

### Step 3: Update Configuration

Edit `backend/.env` or `backend/config.py`:

```python
# AI Configuration (llama.cpp)
LLAMA_MODEL_PATH = "C:/llama.cpp/models/llama-2-7b-chat.Q4_K_M.gguf"
LLAMA_N_CTX = 2048
LLAMA_N_THREADS = 4  # Adjust based on your CPU
LLAMA_N_GPU_LAYERS = 0  # Set to > 0 if you have CUDA GPU
```

Update the executable path in `backend/services/llama_wrapper.py` if needed:
```python
# In _find_executable() method, add your path:
possible_paths = [
    "C:\\llama.cpp\\build\\bin\\Release\\main.exe",  # Your actual path
    # ... other paths
]
```

### Step 4: Test

```powershell
cd backend
conda activate pi3
python main.py
```

The AI assistant should now use the full llama.cpp model!

## Configuration Options

In `backend/config.py`:

```python
# Model file location
LLAMA_MODEL_PATH = "models/llama-2-7b-chat.gguf"

# Context window (higher = more memory, slower)
LLAMA_N_CTX = 2048  # 2048-4096 recommended

# CPU threads (match your CPU cores)
LLAMA_N_THREADS = 4  # 4-8 recommended

# GPU layers (requires CUDA build)
LLAMA_N_GPU_LAYERS = 0  # 0 = CPU only, 32+ = GPU acceleration
```

## Testing AI Endpoints

Once the backend is running:

```powershell
# Test AI assistant
curl http://localhost:8000/ai/chat -X POST -H "Content-Type: application/json" -d '{"message":"What is Bitcoin?","conversation_history":[]}'

# Test price prediction
curl http://localhost:8000/predictions/predict/BTC/24h
```

## Troubleshooting

### "llama.cpp not available"
- ✅ This is normal! The system works in Simple Mode
- To upgrade: Follow steps above to install llama.cpp + model

### "Model not found"
- Check `LLAMA_MODEL_PATH` in config
- Ensure the .gguf file exists
- Use forward slashes `/` in paths, not backslashes

### "Executable not found"
- Update `_find_executable()` in `llama_wrapper.py`
- Add your actual `main.exe` path

### Slow responses
- Reduce `LLAMA_N_CTX` (try 1024)
- Use smaller model (Q4 instead of Q5)
- Increase `LLAMA_N_THREADS`
- Consider GPU acceleration

## Performance Tips

- **CPU**: Use Q4 quantization, 4-8 threads
- **GPU (CUDA)**: Build with CUDA, set `LLAMA_N_GPU_LAYERS = 32`
- **Memory**: Q4 models use ~4GB RAM, Q5 use ~5GB

## Alternative: Keep Using Groq (Cloud)

If you prefer cloud AI (no local setup needed):

1. Keep the old Groq code (available in git history)
2. Get free API key: https://console.groq.com
3. Set `GROQ_API_KEY` in environment

## Summary

✅ **Current Status**: Backend ready with Simple AI (fallback mode)
📦 **Optional Upgrade**: Install llama.cpp + model for full AI
🚀 **Getting Started**: Just run `python main.py` - it works now!

For questions, check the logs or open an issue.
