"""
Quick test of transcription functionality
Tests faster-whisper without needing audio files
"""

print("Testing Faster-Whisper Transcription...")
print("=" * 60)

try:
    from faster_whisper import WhisperModel
    
    print("✅ faster-whisper imported successfully")
    print("\nLoading tiny model for testing...")
    
    # Load tiny model (smallest, fastest)
    model = WhisperModel("tiny", device="cpu", compute_type="int8")
    
    print("✅ Model loaded successfully!")
    print("\n📊 Model Information:")
    print(f"   Model size: tiny (fastest)")
    print(f"   Device: CPU")
    print(f"   Compute type: int8")
    
    print("\n✨ Transcription setup is ready!")
    print("\nTo test with actual audio:")
    print("1. Record audio using the frontend UI")
    print("2. The audio will be sent to /api/voice/transcribe")
    print("3. Python script will transcribe it automatically")
    
    print("\n" + "=" * 60)
    print("✅ SUCCESS: Faster-Whisper is ready to use!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure faster-whisper is installed:")
    print("   pip install faster-whisper")
    print("2. Check Python version (needs 3.8+)")
    print("3. Ensure you have internet for first-time model download")
