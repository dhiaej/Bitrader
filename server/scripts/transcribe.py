#!/usr/bin/env python3
"""
Faster-Whisper transcription script
Runs locally without API keys
"""

import sys
import json
from faster_whisper import WhisperModel

def transcribe_audio(audio_path):
    """Transcribe audio using Faster-Whisper"""
    # Load model (cached after first run)
    # Options: tiny, base, small, medium, large-v2, large-v3
    model_size = "base"  # Good balance of speed/accuracy
    
    # Use GPU if available, otherwise CPU
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    
    # Transcribe
    segments, info = model.transcribe(audio_path, language="en")
    
    # Combine all segments
    full_text = " ".join([segment.text for segment in segments])
    
    return {
        "text": full_text.strip(),
        "language": info.language,
        "language_probability": info.language_probability
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No audio file path provided"}))
        sys.exit(1)
    
    audio_path = sys.argv[1]
    
    try:
        result = transcribe_audio(audio_path)
        print(json.dumps(result))
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
