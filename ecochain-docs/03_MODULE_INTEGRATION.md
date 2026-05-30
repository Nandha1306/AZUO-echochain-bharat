# EcoChain Bharat — Module Integration Plan

> How Module 1 (Nandha) and Module 2 (Indhu) connect

---

## Integration Overview

The two modules communicate through a single HTTP boundary. Module 1's `blockchain_service.py` calls Module 2's Fabric Gateway API over HTTP. Neither module imports code from the other — they are completely independent services that talk over JSON REST.

```
Module 1 (FastAPI)                    Module 2 (Fabric Gateway API)
─────────────────────                 ─────────────────────────────
blockchain_service.py  ──── HTTP ───▶  /chaincode/registerActivity
                       ◀─── JSON ────  { txId, status, timestamp }
```

The contract between them lives in `shared/api-contracts/` — both sides must honour the exact JSON schema.

---

## The 5 Integration Endpoints

These are the **only** endpoints Module 1 calls on Module 2. Both sides implement exactly this interface.

### 1. Register Activity
```
POST /chaincode/registerActivity

Request (Module 1 sends):
{
  "farmerId": "TN-FRM-00142",
  "activityType": "no_till",
  "acres": 3.2,
  "location": { "lat": 10.78, "lng": 78.81 }
}

Response (Module 2 returns):
{
  "txId": "ECBH-2026-84921",
  "status": "pending_verification",
  "timestamp": "2026-05-28T10:22:00Z"
}
```

### 2. Verify Activity
```
POST /chaincode/verifyActivity

Request:
{
  "txId": "ECBH-2026-84921",
  "activityId": "664abc123...",
  "farmerId": "TN-FRM-00142",
  "auditorId": "AUD-007"
}

Response:
{
  "txId": "VERIFY-2026-55512",
  "status": "verified",
  "verifiedAt": "2026-05-28T11:00:00Z"
}
```

### 3. Mint Credit
```
POST /chaincode/mintCredit

Request:
{
  "activityId": "664abc123...",
  "farmerId": "TN-FRM-00142",
  "creditAmount": 2.56,
  "activityType": "no_till",
  "acres": 3.2
}

Response:
{
  "txId": "MINT-2026-77234",
  "creditId": "CREDIT-TN-FRM-00142-001",
  "status": "credits_minted",
  "mintedAt": "2026-05-28T11:30:00Z"
}
```

### 4. Transfer Credit
```
POST /chaincode/transferCredit

Request:
{
  "creditId": "CREDIT-TN-FRM-00142-001",
  "sellerId": "TN-FRM-00142",
  "buyerId": "IND-CBE-009",
  "credits": 1.5
}

Response:
{
  "txId": "TRANSFER-2026-99012",
  "status": "transferred",
  "transferredAt": "2026-05-28T12:00:00Z"
}
```

### 5. Retire Credit
```
POST /chaincode/retireCredit

Request:
{
  "creditId": "CREDIT-TN-FRM-00142-001",
  "ownerId": "IND-CBE-009",
  "amount": 1.5,
  "reason": "BEE compliance FY2026"
}

Response:
{
  "txId": "RETIRE-2026-44231",
  "status": "retired",
  "retiredAt": "2026-05-28T12:30:00Z"
}
```

### 6. Query (bonus — for audit trail)
```
GET /chaincode/queryActivity/:txId
GET /chaincode/queryCredit/:creditId

Response:
{
  "txId": "...",
  "history": [ ... ],
  "currentState": { ... }
}
```

---

## Development Phases

### Phase 1 — Parallel Development (Weeks 1–4)
Both developers work **independently** using the mock/stub approach.

**Nandha uses** `mock-blockchain/app.py` (already built) which perfectly mimics Module 2's endpoints. Set `BLOCKCHAIN_URL=http://127.0.0.1:9001` to hit the mock.

**Indhu uses** a simple Python test script to call her Fabric Gateway API directly without Module 1 being ready.

### Phase 2 — Integration (Week 5–6)
1. Indhu confirms all 6 endpoints are live on port 9000
2. Nandha changes `.env`: `BLOCKCHAIN_URL=http://127.0.0.1:9000`
3. Run end-to-end test: farmer submit → auditor verify → mint → transfer
4. Fix any JSON field mismatches

### Phase 3 — Full System Test (Week 7–8)
- Docker Compose brings up both modules together
- Integration test suite runs all lifecycle flows
- Load test: simulate 50 concurrent farmers submitting activities

---

## Environment Variables for Integration

### Module 1 `.env`
```env
MONGODB_URL=mongodb+srv://...         # rotate this password NOW
DATABASE_NAME=ecobharat
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
ALGORITHM=HS256

# Switch between mock and real:
# BLOCKCHAIN_URL=http://127.0.0.1:9001   ← mock (during dev)
BLOCKCHAIN_URL=http://127.0.0.1:9000     ← real (after Indhu's module is up)
```

### Module 2 `.env`
```env
PORT=9000
FABRIC_CHANNEL=carbon-channel
FABRIC_CHAINCODE=carbon-credit
FABRIC_MSP_ID=BEEOrg
FABRIC_PEER_ENDPOINT=localhost:7051
FABRIC_TLS_CERT_PATH=./fabric-network/organizations/...
FABRIC_IDENTITY_CERT_PATH=...
FABRIC_IDENTITY_KEY_PATH=...
```

---

## Docker Compose (Root Level) — Both Modules Together

```yaml
version: '3.8'

services:
  # Module 1 — API Gateway
  api-gateway:
    build: ./module1-frontend-ai/services/api-gateway
    ports:
      - "8000:8000"
    environment:
      - BLOCKCHAIN_URL=http://fabric-gateway:9000
    depends_on:
      - fabric-gateway
    networks:
      - ecochain-net

  # Module 1 — Mock Blockchain (dev only)
  mock-blockchain:
    build:
      context: ./module1-frontend-ai/services/api-gateway
      dockerfile: Dockerfile.mock
    ports:
      - "9001:9001"
    networks:
      - ecochain-net

  # Module 2 — Fabric Gateway API
  fabric-gateway:
    build: ./module2-blockchain/fabric-gateway-api
    ports:
      - "9000:9000"
    networks:
      - ecochain-net

  # Module 1 — Web Portal
  web-portal:
    build: ./module1-frontend-ai/apps/web-portal
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://api-gateway:8000
    depends_on:
      - api-gateway
    networks:
      - ecochain-net

networks:
  ecochain-net:
    driver: bridge
```

---

## Integration Test Checklist

Before declaring integration complete, verify all of these:

- [ ] `POST /api/v1/auth/register` creates farmer user
- [ ] `POST /api/v1/auth/login` returns JWT with role
- [ ] `POST /api/v1/activities` calls blockchain, saves to MongoDB
- [ ] `GET /api/v1/activities/pending` returns pending list for auditor
- [ ] `POST /api/v1/activities/{id}/verify` updates status and calls blockchain
- [ ] `POST /api/v1/activities/{id}/reject` updates status with auditorId
- [ ] `POST /api/v1/activities/{id}/mint` calculates credits by activityType, updates wallet
- [ ] `GET /api/v1/marketplace` returns farmers with available credits
- [ ] `POST /api/v1/credits/transfer` moves credits, creates transaction record
- [ ] `GET /api/v1/wallet/{ownerId}` returns correct balance
- [ ] `GET /api/v1/transactions/farmer/{id}` returns buy/sell history
- [ ] All above with wrong role returns 403
- [ ] All above with no token returns 401
- [ ] Blockchain txId in MongoDB matches what Fabric Gateway returned
