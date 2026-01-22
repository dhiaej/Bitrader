const express = require('express');
const router = express.Router();
const multer = require('multer');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const axios = require('axios');

// Configure multer for audio uploads
const upload = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: 10 * 1024 * 1024 }, // 10MB limit
});

// Ollama API configuration (runs locally, no API key needed)
const OLLAMA_API_URL = process.env.OLLAMA_API_URL || 'http://localhost:11434';
const OLLAMA_MODEL = process.env.OLLAMA_MODEL || 'llama2'; // or 'mistral', 'codellama', etc.

/**
 * POST /api/voice/transcribe
 * Transcribe audio to text using Faster-Whisper (local, no API key)
 */
router.post('/transcribe', upload.single('audio'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No audio file provided' });
    }

    // Save audio file temporarily
    const tempDir = path.join(__dirname, '../temp');
    if (!fs.existsSync(tempDir)) {
      fs.mkdirSync(tempDir, { recursive: true });
    }

    const tempFilePath = path.join(tempDir, `audio_${Date.now()}.webm`);
    fs.writeFileSync(tempFilePath, req.file.buffer);

    // Transcribe using Faster-Whisper Python script
    const transcript = await transcribeWithFasterWhisper(tempFilePath);

    // Clean up temp file
    fs.unlinkSync(tempFilePath);

    res.json({ transcript });
  } catch (error) {
    console.error('Error transcribing audio:', error);
    res.status(500).json({ error: 'Failed to transcribe audio', details: error.message });
  }
});

/**
 * POST /api/voice/parse-command
 * Parse trading command using Ollama (local LLM, no API key)
 */
router.post('/parse-command', async (req, res) => {
  try {
    const { transcript } = req.body;

    if (!transcript) {
      return res.status(400).json({ error: 'No transcript provided' });
    }

    let command;

    // Try to use Ollama if available
    try {
      command = await parseCommandWithOllama(transcript);
    } catch (error) {
      console.error('Error using Ollama, falling back to regex:', error);
      command = parseCommandWithRegex(transcript);
    }

    res.json({ command });
  } catch (error) {
    console.error('Error parsing command:', error);
    res.status(500).json({ error: 'Failed to parse command', details: error.message });
  }
});

/**
 * Transcribe audio using Faster-Whisper (Python)
 */
async function transcribeWithFasterWhisper(audioFilePath) {
  return new Promise((resolve, reject) => {
    // Call Python script that uses faster-whisper
    const pythonScript = path.join(__dirname, '../scripts', 'transcribe.py');
    const python = spawn('python', [pythonScript, audioFilePath]);

    let output = '';
    let error = '';

    python.stdout.on('data', (data) => {
      output += data.toString();
    });

    python.stderr.on('data', (data) => {
      error += data.toString();
    });

    python.on('close', (code) => {
      if (code !== 0) {
        reject(new Error(`Python script failed: ${error}`));
      } else {
        try {
          const result = JSON.parse(output);
          resolve(result.text);
        } catch (e) {
          reject(new Error(`Failed to parse transcription result: ${output}`));
        }
      }
    });
  });
}

/**
 * Parse command using Ollama (local LLM)
 */
async function parseCommandWithOllama(transcript) {
  const prompt = `You are a trading command parser. Parse this voice command and return ONLY valid JSON (no other text).

Trading command: "${transcript}"

Extract these fields:
- action: "buy", "sell", "cancel", or "unknown"
- asset: coin symbol like "BTC", "ETH" (if mentioned)
- amount: numeric value (if mentioned)
- priceType: "market" or "limit" (if mentioned)
- price: numeric value for limit orders (if mentioned)
- confidence: 0.0 to 1.0 (your confidence)

Return ONLY the JSON object:`;

  try {
    const response = await axios.post(`${OLLAMA_API_URL}/api/generate`, {
      model: OLLAMA_MODEL,
      prompt: prompt,
      stream: false,
      format: 'json',
    });

    const responseText = response.data.response;
    
    // Extract JSON from response
    const jsonMatch = responseText.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      const parsed = JSON.parse(jsonMatch[0]);
      return {
        transcript,
        action: parsed.action || 'unknown',
        asset: parsed.asset,
        amount: parsed.amount,
        priceType: parsed.priceType,
        price: parsed.price,
        confidence: parsed.confidence || 0.5,
      };
    } else {
      throw new Error('Could not extract JSON from Ollama response');
    }
  } catch (error) {
    console.error('Ollama API error:', error.message);
    throw error;
  }
}

/**
 * Regex-based command parser (fallback)
 */
function parseCommandWithRegex(transcript) {
  const lowerTranscript = transcript.toLowerCase();
  
  // Determine action
  let action = 'unknown';
  if (lowerTranscript.includes('buy') || lowerTranscript.includes('purchase')) {
    action = 'buy';
  } else if (lowerTranscript.includes('sell')) {
    action = 'sell';
  } else if (lowerTranscript.includes('cancel')) {
    action = 'cancel';
  }

  // Extract asset
  const assetMatch = lowerTranscript.match(/\b(btc|bitcoin|eth|ethereum|usdt|bnb|sol|ada|xrp|doge)\b/i);
  const asset = assetMatch ? assetMatch[1].toUpperCase().replace('BITCOIN', 'BTC').replace('ETHEREUM', 'ETH') : undefined;

  // Extract amount
  const amountMatch = lowerTranscript.match(/\b(\d+\.?\d*)\s*(btc|eth|usdt|bnb|sol|ada|xrp|doge|bitcoin|ethereum)?\b/i);
  const amount = amountMatch ? parseFloat(amountMatch[1]) : undefined;

  // Determine price type
  let priceType = undefined;
  if (lowerTranscript.includes('market')) {
    priceType = 'market';
  } else if (lowerTranscript.includes('limit')) {
    priceType = 'limit';
  }

  // Extract limit price
  let price = undefined;
  if (priceType === 'limit') {
    const priceMatch = lowerTranscript.match(/(?:at|price|limit)\s*(?:price)?\s*(\d+\.?\d*)/i);
    price = priceMatch ? parseFloat(priceMatch[1]) : undefined;
  }

  // Calculate confidence
  let confidence = 0;
  if (action !== 'unknown') confidence += 0.3;
  if (asset) confidence += 0.3;
  if (amount) confidence += 0.2;
  if (priceType) confidence += 0.2;

  return {
    transcript,
    action,
    asset,
    amount,
    priceType,
    price,
    confidence,
  };
}

module.exports = router;
