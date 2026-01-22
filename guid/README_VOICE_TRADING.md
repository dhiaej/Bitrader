# Voice Trading Assistant

## Overview

The Voice Trading Assistant allows users to create and manage trades using natural voice commands. This feature combines OpenAI Whisper for speech-to-text conversion with llama.cpp for intelligent command parsing.

## Features

- 🎤 **Voice-activated trading** - Create orders hands-free
- 🤖 **AI-powered parsing** - Understands natural language commands
- ✅ **Real-time feedback** - Visual and status indicators
- 🎯 **High accuracy** - Confidence scoring for parsed commands
- ♿ **Accessibility** - Enables trading for users with limited mobility

## Setup Instructions

### 1. Install Dependencies

```bash
npm install
# or
yarn install
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
LLAMA_MODEL_PATH=./models/llama-model.gguf
```

### 3. Download Llama Model (Optional but Recommended)

Download a compatible GGUF model file:

```bash
# Create models directory
mkdir -p models

# Download a recommended model (example using llama-2-7b)
# Visit https://huggingface.co/models to find GGUF models
# Or use a smaller model for faster processing:
wget https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf -O models/llama-model.gguf
```

### 4. Get OpenAI API Key

1. Visit [OpenAI Platform](https://platform.openai.com/)
2. Create an account or sign in
3. Navigate to API Keys section
4. Create a new API key
5. Add it to your `.env` file

### 5. Start the Application

```bash
# Start backend server
npm run server

# Start frontend (in another terminal)
npm start
```

## Usage

### Basic Commands

#### Market Orders

- "Buy 0.5 BTC at market price"
- "Sell 2 ETH at market"
- "Purchase 1000 USDT worth of BTC"

#### Limit Orders

- "Sell 0.5 BTC at limit price 45000"
- "Buy 10 ETH at limit 2500"
- "Create a limit order to sell 1 BTC at 50000"

#### Cancel Orders

- "Cancel all orders"
- "Cancel my open orders"
- "Stop all pending trades"

### Using the Interface

1. **Click the microphone button** to start recording
2. **Speak your command** clearly
3. **Click again to stop** recording
4. **Review the parsed command** before confirmation
5. **Confirm or cancel** the trade

### Command Structure

The AI understands commands with the following components:

- **Action**: buy, sell, cancel
- **Amount**: numeric value (e.g., 0.5, 2, 1000)
- **Asset**: BTC, ETH, USDT, BNB, SOL, ADA, XRP, DOGE
- **Price Type**: market or limit
- **Price** (for limit orders): numeric value

### Confidence Scoring

Each parsed command receives a confidence score:

- **90-100%**: High confidence - Command clearly understood
- **70-89%**: Medium confidence - Command understood with minor uncertainty
- **Below 70%**: Low confidence - Please rephrase and try again

## API Endpoints

### POST /api/voice/transcribe

Transcribe audio to text using OpenAI Whisper.

**Request:**

```
Content-Type: multipart/form-data
Body: audio file (webm, mp3, wav)
```

**Response:**

```json
{
  "transcript": "Buy 0.5 BTC at market price"
}
```

### POST /api/voice/parse-command

Parse trading command using llama.cpp.

**Request:**

```json
{
  "transcript": "Buy 0.5 BTC at market price"
}
```

**Response:**

```json
{
  "command": {
    "transcript": "Buy 0.5 BTC at market price",
    "action": "buy",
    "asset": "BTC",
    "amount": 0.5,
    "priceType": "market",
    "confidence": 0.95
  }
}
```

## Architecture

### Frontend Components

- **VoiceTradingAssistant.tsx** - Main React component with UI
- **voiceService.ts** - Service layer for API communication

### Backend Services

- **voiceRoutes.js** - Express routes for voice processing
- **OpenAI Whisper** - Speech-to-text conversion
- **llama.cpp** - Natural language command parsing

### Flow Diagram

```
User Voice → Browser AudioAPI → Backend (Whisper) → Text Transcript
  ↓
Text Transcript → llama.cpp → Structured Command
  ↓
Structured Command → Trading Engine → Order Execution
```

## Troubleshooting

### Microphone Access Denied

- Check browser permissions
- Ensure HTTPS is enabled (required for microphone access)
- Try a different browser

### Poor Transcription Quality

- Speak clearly and at a normal pace
- Reduce background noise
- Check microphone quality
- Ensure good internet connection

### Low Confidence Scores

- Use specific commands from the examples
- Include all required information (action, amount, asset)
- Avoid ambiguous phrases

### Llama Model Not Loading

- Verify `LLAMA_MODEL_PATH` is correct
- Check model file format (must be GGUF)
- Ensure sufficient RAM (4GB+ recommended)
- System will fall back to regex parsing if model fails

## Security Considerations

- Audio data is processed server-side and not stored
- Commands require user confirmation before execution
- All API calls are authenticated
- Rate limiting is enforced on voice endpoints

## Performance Tips

- Use a smaller Llama model for faster processing (Q4 quantization recommended)
- Keep commands concise and clear
- Allow 2-3 seconds for processing
- Ensure stable internet connection

## Browser Compatibility

- ✅ Chrome/Edge 80+
- ✅ Firefox 75+
- ✅ Safari 14+
- ✅ Opera 67+

## Future Enhancements

- [ ] Multi-language support
- [ ] Voice confirmation before trade execution
- [ ] Preset command shortcuts
- [ ] Voice-based portfolio queries
- [ ] Offline mode with local models

## Support

For issues or questions:

1. Check the troubleshooting section
2. Review API error messages
3. Enable debug logging in development mode
4. Contact support with voice transcript and error logs

## License

This feature is part of the main trading platform license.
