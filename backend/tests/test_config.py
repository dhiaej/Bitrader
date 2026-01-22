"""Test config loading"""
from config import settings
import os

print("=" * 60)
print("Config Test")
print("=" * 60)

print(f"\nFrom settings object:")
print(f"OPENAI_API_KEY length: {len(settings.OPENAI_API_KEY)}")
print(f"OPENAI_API_KEY value: {settings.OPENAI_API_KEY[:30]}..." if settings.OPENAI_API_KEY else "EMPTY")
print(f"OPENAI_API_KEY bool: {bool(settings.OPENAI_API_KEY)}")

print(f"\nFrom os.getenv:")
print(f"OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY', 'NOT FOUND')[:30]}..." if os.getenv('OPENAI_API_KEY') else "NOT FOUND")

print(f"\nDirect from .env file:")
try:
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('OPENAI_API_KEY'):
                print(f"Raw line: {line.strip()[:60]}...")
                break
except Exception as e:
    print(f"Error reading .env: {e}")

print("\n" + "=" * 60)
