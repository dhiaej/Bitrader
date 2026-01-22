import axios from 'axios';

interface VoiceCommand {
  transcript: string;
  action: 'buy' | 'sell' | 'cancel' | 'unknown';
  asset?: string;
  amount?: number;
  priceType?: 'market' | 'limit';
  price?: number;
  confidence: number;
}

class VoiceService {
  private apiBaseUrl: string;

  constructor() {
    this.apiBaseUrl = process.env.REACT_APP_API_URL || 'http://localhost:3001/api';
  }

  /**
   * Transcribe audio to text using Faster-Whisper (local, no API key)
   */
  async transcribeAudio(audioBlob: Blob): Promise<string> {
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'recording.webm');

      const response = await axios.post(`${this.apiBaseUrl}/voice/transcribe`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      return response.data.transcript;
    } catch (error) {
      console.error('Error transcribing audio:', error);
      throw new Error('Failed to transcribe audio');
    }
  }

  /**
   * Parse trading command using Ollama (local LLM, no API key)
   */
  async parseTradeCommand(transcript: string): Promise<VoiceCommand> {
    try {
      const response = await axios.post(`${this.apiBaseUrl}/voice/parse-command`, {
        transcript,
      });

      return response.data.command;
    } catch (error) {
      console.error('Error parsing command:', error);
      throw new Error('Failed to parse command');
    }
  }

  /**
   * Local fallback parser (basic regex-based parsing)
   */
  parseCommandLocally(transcript: string): VoiceCommand {
    const lowerTranscript = transcript.toLowerCase();
    
    // Determine action
    let action: 'buy' | 'sell' | 'cancel' | 'unknown' = 'unknown';
    if (lowerTranscript.includes('buy') || lowerTranscript.includes('purchase')) {
      action = 'buy';
    } else if (lowerTranscript.includes('sell')) {
      action = 'sell';
    } else if (lowerTranscript.includes('cancel')) {
      action = 'cancel';
    }

    // Extract asset (BTC, ETH, etc.)
    const assetMatch = lowerTranscript.match(/\b(btc|bitcoin|eth|ethereum|usdt|bnb|sol|ada|xrp|doge)\b/i);
    const asset = assetMatch ? assetMatch[1].toUpperCase() : undefined;

    // Extract amount
    const amountMatch = lowerTranscript.match(/\b(\d+\.?\d*)\s*(btc|eth|usdt|bnb|sol|ada|xrp|doge|bitcoin|ethereum)?\b/i);
    const amount = amountMatch ? parseFloat(amountMatch[1]) : undefined;

    // Determine price type
    let priceType: 'market' | 'limit' | undefined = undefined;
    if (lowerTranscript.includes('market')) {
      priceType = 'market';
    } else if (lowerTranscript.includes('limit')) {
      priceType = 'limit';
    }

    // Extract limit price if applicable
    let price: number | undefined = undefined;
    if (priceType === 'limit') {
      const priceMatch = lowerTranscript.match(/(?:at|price|limit)\s*(?:price)?\s*(\d+\.?\d*)/i);
      price = priceMatch ? parseFloat(priceMatch[1]) : undefined;
    }

    // Calculate confidence based on parsed elements
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
}

export const voiceService = new VoiceService();
