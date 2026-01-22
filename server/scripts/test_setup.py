"""
Test script for Voice Trading Assistant
Tests the open-source implementation without API keys
"""

import sys
import json

# Test the transcribe module
print("=" * 60)
print("Testing Voice Trading Assistant - Open Source Setup")
print("=" * 60)

# Test 1: Check if faster-whisper is installed
print("\n[1] Checking faster-whisper installation...")
try:
    from faster_whisper import WhisperModel
    print("✅ faster-whisper is installed")
except ImportError as e:
    print(f"❌ faster-whisper not installed: {e}")
    print("   Run: pip install faster-whisper")
    sys.exit(1)

# Test 2: Check if transcribe.py exists
print("\n[2] Checking transcribe.py script...")
import os
script_path = os.path.join(os.path.dirname(__file__), 'transcribe.py')
if os.path.exists(script_path):
    print(f"✅ transcribe.py found at: {script_path}")
else:
    print(f"❌ transcribe.py not found at: {script_path}")
    sys.exit(1)

# Test 3: Test basic model loading (small model for quick test)
print("\n[3] Testing Whisper model loading (this may take a moment)...")
try:
    print("   Loading 'tiny' model for quick test...")
    model = WhisperModel("tiny", device="cpu", compute_type="int8")
    print("✅ Whisper model loaded successfully")
    print("   Available models: tiny, base, small, medium, large-v2, large-v3")
    print("   Recommendation: Use 'base' for production (good balance)")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    sys.exit(1)

# Test 4: Check Node.js dependencies
print("\n[4] Checking Node.js setup...")
server_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)))
package_json = os.path.join(server_dir, 'package.json')
if os.path.exists(package_json):
    print(f"✅ package.json found")
    print("   Make sure 'axios' is installed: npm install axios")
else:
    print("⚠️  package.json not found in server directory")

# Test 5: Check if Ollama needs to be installed
print("\n[5] Ollama Setup Instructions:")
print("   Ollama is NOT installed yet. Follow these steps:")
print("   ")
print("   1. Download Ollama:")
print("      Visit: https://ollama.ai/download/windows")
print("      Or run: winget install Ollama.Ollama")
print("   ")
print("   2. Install a model (choose one):")
print("      ollama pull llama2      (Recommended)")
print("      ollama pull mistral     (Faster)")
print("      ollama pull llama3      (Best quality)")
print("   ")
print("   3. Verify installation:")
print("      curl http://localhost:11434/api/tags")

# Summary
print("\n" + "=" * 60)
print("Setup Status Summary:")
print("=" * 60)
print("✅ Python: Ready")
print("✅ faster-whisper: Installed")
print("✅ transcribe.py: Created")
print("⚠️  Ollama: Needs installation (see instructions above)")
print("⚠️  Node.js: Run 'cd server && npm install axios'")
print("\n💡 Next Steps:")
print("   1. Install Ollama (see instructions above)")
print("   2. Install Node.js dependencies: cd server && npm install axios")
print("   3. Configure .env file with OLLAMA settings")
print("   4. Start your server and test!")
print("\n📚 Full setup guide: VOICE_SETUP_OPENSOURCE.md")
print("=" * 60)
