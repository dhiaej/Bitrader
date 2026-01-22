"""
Script to file a test dispute on an existing P2P trade
"""
import requests

# Login as buyer (alice_trader - user ID 8)
print("🔐 Logging in as alice_trader...")
login_response = requests.post('http://localhost:8000/api/auth/login', 
    json={'username': 'alice_trader', 'password': 'password123'})

if login_response.status_code == 200:
    token = login_response.json()['access_token']
    print("✅ Login successful!")
    
    # File dispute on trade ID 1
    print("\n📋 Filing dispute on Trade ID 1...")
    dispute_response = requests.post(
        'http://localhost:8000/api/disputes/',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'trade_id': 1,
            'reason': 'I sent the payment via bank transfer 2 days ago but the seller has not released the Bitcoin. I have provided proof of payment including transaction receipt and bank statement showing the funds were debited from my account.',
            'evidence': 'Bank transfer receipt #TXN123456, Amount: $992.43, Date: 2025-12-02 10:30 AM'
        }
    )
    
    if dispute_response.status_code == 201:
        dispute = dispute_response.json()
        print('\n✅ Dispute filed successfully!')
        print(f'   Dispute ID: {dispute["id"]}')
        print(f'   Trade ID: {dispute["trade_id"]}')
        print(f'   Status: {dispute["status"]}')
        print(f'   Filed by: {dispute["filed_by_username"]}')
        print(f'\n📍 Next steps:')
        print(f'   1. Login as admin: ayoubb or admin')
        print(f'   2. Go to: http://localhost:4200/admin')
        print(f'   3. Click on "Disputes" tab')
        print(f'   4. View and resolve the dispute')
    else:
        print(f'\n❌ Error filing dispute: {dispute_response.status_code}')
        print(dispute_response.text)
else:
    print(f'❌ Login failed: {login_response.status_code}')
    print(login_response.text)
    print('\nMake sure the backend server is running:')
    print('cd backend')
    print('python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload')
