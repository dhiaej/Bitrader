# 🧪 API Testing Guide - P2P Trading Simulator

## 📝 Overview

This guide provides complete test scenarios to verify all backend functionality.

---

## 🔑 Authentication Tests

### 1. Register New User

**Endpoint:** `POST /api/auth/register`

**Request:**

```json
{
  "username": "testuser",
  "email": "testuser@example.com",
  "password": "Test123456",
  "full_name": "Test User"
}
```

**Expected Response:** `201 Created`

```json
{
  "id": 4,
  "username": "testuser",
  "email": "testuser@example.com",
  "full_name": "Test User",
  "is_active": true,
  "is_verified": false,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Verify:**

- ✅ User created in database
- ✅ 4 wallets created (USD, BTC, ETH, USDT)
- ✅ Initial balances: $10,000 USD, 0.5 BTC, 5 ETH, $5,000 USDT
- ✅ Reputation record created

---

### 2. Login

**Endpoint:** `POST /api/auth/login`

**Request:** (Form Data)

```
username: testuser
password: Test123456
```

**Expected Response:** `200 OK`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": 4,
  "username": "testuser"
}
```

**Save the token for subsequent requests!**

---

### 3. Get Current User

**Endpoint:** `GET /api/auth/me`

**Headers:**

```
Authorization: Bearer <your_access_token>
```

**Expected Response:** `200 OK`

```json
{
  "id": 4,
  "username": "testuser",
  "email": "testuser@example.com",
  "full_name": "Test User",
  "is_active": true,
  "is_verified": false,
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

## 💰 Wallet Tests

### 4. Get All Balances

**Endpoint:** `GET /api/wallet/balances`

**Headers:**

```
Authorization: Bearer <token>
```

**Expected Response:** `200 OK`

```json
[
  {
    "id": 13,
    "user_id": 4,
    "currency": "USD",
    "available_balance": "10000.00000000",
    "locked_balance": "0.00000000",
    "created_at": "2024-01-15T10:30:00Z"
  },
  {
    "id": 14,
    "user_id": 4,
    "currency": "BTC",
    "available_balance": "0.50000000",
    "locked_balance": "0.00000000",
    "created_at": "2024-01-15T10:30:00Z"
  },
  ...
]
```

---

### 5. Deposit Funds

**Endpoint:** `POST /api/wallet/deposit?currency=USD&amount=500`

**Expected Response:** `200 OK`

```json
{
  "id": 1,
  "wallet_id": 13,
  "type": "DEPOSIT",
  "amount": "500.00000000",
  "currency": "USD",
  "status": "COMPLETED",
  "description": "Virtual deposit of 500.0 USD",
  "created_at": "2024-01-15T11:00:00Z"
}
```

**Verify:**

- ✅ Balance increased by $500
- ✅ Transaction recorded

---

### 6. Transfer to Another User

**Endpoint:** `POST /api/wallet/transfer`

**Request:**

```json
{
  "recipient_username": "alice_trader",
  "currency": "USD",
  "amount": 100
}
```

**Expected Response:** `200 OK`

```json
{
  "message": "Transfer successful",
  "amount": 100,
  "currency": "USD",
  "recipient": "alice_trader"
}
```

**Verify:**

- ✅ Sender balance decreased by $100
- ✅ Recipient balance increased by $100
- ✅ 2 transactions created (outgoing & incoming)

---

## 📊 Order Book Tests

### 7. Place Limit Sell Order

**Endpoint:** `POST /api/orderbook/orders`

**Request:**

```json
{
  "instrument": "BTC/USD",
  "order_type": "SELL",
  "order_subtype": "LIMIT",
  "price": 45000,
  "quantity": 0.1
}
```

**Expected Response:** `201 Created`

```json
{
  "id": 1,
  "user_id": 4,
  "instrument": "BTC/USD",
  "order_type": "SELL",
  "order_subtype": "LIMIT",
  "price": "45000.00000000",
  "quantity": "0.10000000",
  "remaining_quantity": "0.10000000",
  "status": "PENDING",
  "created_at": "2024-01-15T12:00:00Z"
}
```

**Verify:**

- ✅ Order created
- ✅ 0.1 BTC locked in wallet
- ✅ Available BTC balance decreased

---

### 8. Place Limit Buy Order (Different User - Will Match!)

**Login as:** alice_trader

**Endpoint:** `POST /api/orderbook/orders`

**Request:**

```json
{
  "instrument": "BTC/USD",
  "order_type": "BUY",
  "order_subtype": "LIMIT",
  "price": 45000,
  "quantity": 0.1
}
```

**Expected:** Orders automatically match!

**Verify:**

- ✅ Both orders status = "FILLED"
- ✅ Trade created
- ✅ Buyer received 0.1 BTC (minus fee)
- ✅ Seller received $4,500 (minus fee)
- ✅ Balances updated
- ✅ Locked funds released

---

### 9. View Order Book

**Endpoint:** `GET /api/orderbook/orderbook/BTC/USD?depth=20`

**Expected Response:**

```json
{
  "instrument": "BTC/USD",
  "bids": [
    { "price": 44900, "quantity": 0.5, "count": 2 },
    { "price": 44800, "quantity": 1.2, "count": 3 }
  ],
  "asks": [
    { "price": 45100, "quantity": 0.3, "count": 1 },
    { "price": 45200, "quantity": 0.8, "count": 2 }
  ],
  "last_price": "45000.00000000",
  "timestamp": "2024-01-15T12:05:00Z"
}
```

---

### 10. Get Trade History

**Endpoint:** `GET /api/orderbook/trades`

**Expected:** List of executed trades

---

### 11. Cancel Order

**Endpoint:** `DELETE /api/orderbook/orders/5`

**Expected Response:**

```json
{
  "message": "Order cancelled successfully"
}
```

**Verify:**

- ✅ Order status = "CANCELLED"
- ✅ Locked funds released

---

## 🤝 P2P Trading Tests

### 12. Create P2P Advertisement

**Endpoint:** `POST /api/p2p/advertisements`

**Request:**

```json
{
  "ad_type": "SELL",
  "currency": "BTC",
  "fiat_currency": "USD",
  "price": 45000,
  "min_limit": 100,
  "max_limit": 5000,
  "available_amount": 0.2,
  "payment_methods": ["Bank Transfer", "PayPal"],
  "payment_time_limit": 30,
  "terms_conditions": "Fast and reliable seller"
}
```

**Expected Response:** `201 Created`

**Verify:**

- ✅ Advertisement created
- ✅ Seller has sufficient BTC balance

---

### 13. Browse P2P Advertisements

**Endpoint:** `GET /api/p2p/advertisements?currency=BTC&ad_type=SELL`

**Expected:** List of matching advertisements

---

### 14. Initiate P2P Trade

**Login as different user!**

**Endpoint:** `POST /api/p2p/trades`

**Request:**

```json
{
  "advertisement_id": 1,
  "amount": 0.1,
  "payment_method": "Bank Transfer"
}
```

**Expected Response:** `201 Created`

```json
{
  "id": 1,
  "advertisement_id": 1,
  "buyer_id": 4,
  "seller_id": 1,
  "amount": "0.10000000",
  "price": "45000.00000000",
  "total_fiat": "4500.00000000",
  "currency": "BTC",
  "fiat_currency": "USD",
  "status": "PENDING",
  "payment_deadline": "2024-01-15T12:35:00Z",
  "created_at": "2024-01-15T12:05:00Z"
}
```

**Verify:**

- ✅ Escrow created
- ✅ Seller's 0.1 BTC locked
- ✅ Trade status = "PENDING"

---

### 15. Mark Payment Sent (Buyer Action)

**Login as buyer**

**Endpoint:** `POST /api/p2p/trades/1/payment-sent`

**Expected Response:**

```json
{
  "message": "Payment marked as sent"
}
```

**Verify:**

- ✅ Trade status = "PAYMENT_SENT"

---

### 16. Confirm Payment (Seller Action)

**Login as seller**

**Endpoint:** `POST /api/p2p/trades/1/confirm-payment`

**Expected Response:**

```json
{
  "message": "Trade completed successfully"
}
```

**Verify:**

- ✅ Trade status = "COMPLETED"
- ✅ Escrow released
- ✅ Buyer received 0.1 BTC
- ✅ Seller's BTC unlocked and transferred
- ✅ Both balances updated

---

### 17. Cancel P2P Trade

**Endpoint:** `POST /api/p2p/trades/2/cancel`

**Expected Response:**

```json
{
  "message": "Trade cancelled successfully"
}
```

**Verify:**

- ✅ Trade status = "CANCELLED"
- ✅ Escrow refunded
- ✅ Seller's funds unlocked
- ✅ Advertisement amount restored

---

## 🧪 Advanced Test Scenarios

### Scenario 1: Complete Trading Flow

1. User A registers → Gets $10k USD
2. User B registers → Gets 0.5 BTC
3. User A places BUY 0.1 BTC @ $45k
4. User B places SELL 0.1 BTC @ $45k
5. ✅ Orders match automatically
6. ✅ User A has 0.1 BTC, $5.5k USD
7. ✅ User B has 0.4 BTC, $14.5k USD

---

### Scenario 2: P2P Complete Flow

1. User A creates SELL BTC ad
2. User B initiates trade
3. Escrow locks User A's BTC
4. User B marks payment sent
5. User A confirms payment
6. ✅ Escrow releases BTC to User B
7. ✅ Both reputations updated

---

### Scenario 3: Partial Order Fill

1. User A: SELL 1.0 BTC @ $45k
2. User B: BUY 0.5 BTC @ $45k
3. ✅ 0.5 BTC traded
4. ✅ User A's order: 0.5 BTC remaining
5. ✅ User A's order status = "PARTIALLY_FILLED"

---

### Scenario 4: Market Order

1. User A: SELL 1.0 BTC @ $45k (LIMIT)
2. User B: BUY 1.0 BTC (MARKET - no price)
3. ✅ Instant match at $45k

---

## 📊 Expected Database State After Tests

**Users Table:**

- 3-4 users created

**Wallets Table:**

- 12-16 wallet records (4 currencies × users)

**Transactions Table:**

- Multiple transaction records

**OrderBook_Orders Table:**

- Some pending, some filled orders

**Trades Table:**

- Executed trades

**P2P_Advertisements Table:**

- Active and inactive ads

**P2P_Trades Table:**

- Completed, pending, cancelled trades

**Escrow Table:**

- Locked and released escrows

**Reputation Table:**

- Reputation records updated

---

## ✅ Verification Checklist

After running all tests, verify:

- [ ] Users can register and login
- [ ] Initial fake money ($10k) received
- [ ] Wallet balances displayed correctly
- [ ] Deposits/withdrawals work
- [ ] Transfers between users work
- [ ] Orders placed successfully
- [ ] Orders match automatically
- [ ] Partial fills work
- [ ] Market orders execute instantly
- [ ] Balances update after trades
- [ ] P2P ads created
- [ ] P2P trades initiated
- [ ] Escrow locks funds
- [ ] Escrow releases on confirmation
- [ ] Trades can be cancelled
- [ ] All transactions logged
- [ ] No balance inconsistencies

---

## 🐛 Common Issues & Solutions

**Issue:** "Insufficient balance"

- Check locked vs available balance
- Ensure order/trade didn't already lock funds

**Issue:** "Order not matching"

- Check prices align (buy >= sell for match)
- Verify order is PENDING
- Check remaining quantity > 0

**Issue:** "Can't confirm P2P payment"

- Ensure buyer marked "payment sent" first
- Login as correct user (seller)

**Issue:** "Escrow not releasing"

- Check trade status progression
- Verify confirmation endpoint called

---

## 💡 Testing Tips

1. **Use Multiple Browser Sessions** - Test with different users simultaneously
2. **Check Database Directly** - Use MySQL Workbench to verify data
3. **Monitor Console Logs** - Backend shows detailed logs
4. **Use API Docs** - Test at `/docs` for interactive testing
5. **Save Access Tokens** - Keep tokens for quick testing
6. **Test Edge Cases** - Negative amounts, wrong currencies, etc.

---

## 🚀 Ready to Test!

Start the backend and test away:

```powershell
cd backend
start_backend.bat
```

Open API Docs: http://localhost:8000/docs

Happy Testing! 🧪✅
