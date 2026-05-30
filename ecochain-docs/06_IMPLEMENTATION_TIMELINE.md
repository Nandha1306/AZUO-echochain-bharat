# EcoChain Bharat — Full Implementation Plan & Timeline

---

## Master Timeline (10 Weeks)

```
Week  │ Nandha (Module 1)                    │ Indhu (Module 2)
──────┼───────────────────────────────────────┼──────────────────────────────────
 1    │ Fix all 8 bugs from review            │ Set up Fabric network locally
      │ Clean requirements.txt                │ Write Go models (activity, credit)
      │ Add retire endpoint                   │ Write ActivityContract
──────┼───────────────────────────────────────┼──────────────────────────────────
 2    │ Add pagination to GET /activities      │ Write CreditContract + AuditContract
      │ Fix marketplace projection             │ Write main.go + deploy chaincode
      │ Add status filter query param          │ Test chaincode with peer CLI
──────┼───────────────────────────────────────┼──────────────────────────────────
 3    │ Build AI Engine — anomaly detection    │ Build Fabric Gateway API (Node.js)
      │ Isolation Forest model                 │ fabric.service.js (gRPC connect)
      │ Write /ai/anomaly-check endpoint       │ activity.controller.js
──────┼───────────────────────────────────────┼──────────────────────────────────
 4    │ Build AI Engine — compliance forecast  │ Build credit.controller.js
      │ /ai/compliance-forecast endpoint       │ audit.controller.js
      │ Connect AI to activity submission      │ All 6 routes wired + tested
──────┼───────────────────────────────────────┼──────────────────────────────────
 5    │ ** INTEGRATION WEEK **                 │ ** INTEGRATION WEEK **
      │ Switch BLOCKCHAIN_URL to port 9000     │ Confirm all endpoints on port 9000
      │ End-to-end test: farmer → mint         │ Fix any JSON contract mismatches
──────┼───────────────────────────────────────┼──────────────────────────────────
 6    │ Build Next.js Login page               │ Add CouchDB indexes
      │ Build Farmer Dashboard                 │ Add Private Data Collections
      │ Build Auditor Dashboard                │ Test channel isolation
──────┼───────────────────────────────────────┼──────────────────────────────────
 7    │ Build Industry Dashboard               │ Write unit tests (activity_test.go)
      │ Build Marketplace page                 │ Write unit tests (credit_test.go)
      │ Connect web portal to API              │ Load test: 100 concurrent txns
──────┼───────────────────────────────────────┼──────────────────────────────────
 8    │ Build Admin Dashboard                  │ Write gateway tests (activity.test.js)
      │ Build Transactions history page        │ Write gateway tests (gateway.test.js)
      │ Add compliance forecast widget         │ Docker compose for Module 2
──────┼───────────────────────────────────────┼──────────────────────────────────
 9    │ Build React Native Farmer App          │ Vishvasya BaaS setup (if available)
      │ LoginScreen, SubmitActivity            │ Multi-org endorsement policies
      │ MyWallet, MyActivities                 │ Fault tolerance testing
──────┼───────────────────────────────────────┼──────────────────────────────────
 10   │ Full system Docker Compose             │ Full system Docker Compose
      │ E2E integration testing                │ E2E integration testing
      │ Fix bugs, demo prep                    │ Fix bugs, demo prep
```

---

## Shared API Contracts (fill these JSON files)

### shared/api-contracts/registerActivity.schema.json
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "RegisterActivity",
  "type": "object",
  "required": ["farmerId", "activityType", "acres"],
  "properties": {
    "farmerId": { "type": "string" },
    "activityType": {
      "type": "string",
      "enum": ["no_till", "agroforestry", "organic_farming", "soil_carbon", "efficient_irrigation"]
    },
    "acres": { "type": "number", "minimum": 0.1 },
    "location": {
      "type": "object",
      "properties": {
        "lat": { "type": "number" },
        "lng": { "type": "number" }
      }
    }
  },
  "response": {
    "txId": "string",
    "status": "pending_verification",
    "timestamp": "ISO8601"
  }
}
```

### shared/constants/activityTypes.ts
```typescript
export const ACTIVITY_TYPES = {
  NO_TILL: 'no_till',
  AGROFORESTRY: 'agroforestry',
  ORGANIC_FARMING: 'organic_farming',
  SOIL_CARBON: 'soil_carbon',
  EFFICIENT_IRRIGATION: 'efficient_irrigation',
} as const;

export const CREDIT_RATES: Record<string, number> = {
  no_till: 0.8,
  agroforestry: 1.2,
  organic_farming: 0.9,
  soil_carbon: 1.0,
  efficient_irrigation: 0.5,
};

export type ActivityType = typeof ACTIVITY_TYPES[keyof typeof ACTIVITY_TYPES];
```

### shared/constants/statuses.ts
```typescript
export const ACTIVITY_STATUSES = {
  PENDING: 'pending_verification',
  VERIFIED: 'verified',
  REJECTED: 'rejected',
  MINTED: 'credits_minted',
} as const;

export const CREDIT_STATUSES = {
  MINTED: 'minted',
  TRANSFERRED: 'transferred',
  RETIRED: 'retired',
} as const;
```

### shared/constants/roles.ts
```typescript
export const ROLES = {
  FARMER: 'farmer',
  INDUSTRY: 'industry',
  AUDITOR: 'auditor',
  ADMIN: 'admin',
  REGULATOR: 'regulator',
} as const;
```

### shared/types/activity.ts
```typescript
export interface Activity {
  activityId: string;
  farmerId: string;
  activityType: string;
  acres: number;
  location?: { lat: number; lng: number };
  status: string;
  txId: string;
  submittedAt: string;
  verification: {
    verified: boolean;
    verifiedBy: string | null;
    verifiedAt: string | null;
  };
  credits: {
    minted: boolean;
    amount: number;
  };
}
```

### shared/types/credit.ts
```typescript
export interface CarbonCredit {
  creditId: string;
  activityId: string;
  farmerId: string;
  ownerId: string;
  ownerType: 'farmer' | 'industry';
  amount: number;
  activityType: string;
  status: 'minted' | 'transferred' | 'retired';
  mintedAt: string;
  retiredAt?: string;
  retiredBy?: string;
}
```

---

## Root docker-compose.yml (Complete)

```yaml
version: '3.8'

services:
  # ── Module 1: API Gateway ──
  api-gateway:
    build:
      context: ./module1-frontend-ai/services/api-gateway
      dockerfile: Dockerfile
    container_name: ecochain-api
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URL=${MONGODB_URL}
      - DATABASE_NAME=${DATABASE_NAME}
      - SECRET_KEY=${SECRET_KEY}
      - ALGORITHM=${ALGORITHM}
      - BLOCKCHAIN_URL=http://fabric-gateway:9000
    depends_on:
      - fabric-gateway
    networks:
      - ecochain-net
    restart: unless-stopped

  # ── Module 1: Web Portal ──
  web-portal:
    build:
      context: ./module1-frontend-ai/apps/web-portal
      dockerfile: Dockerfile
    container_name: ecochain-web
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://api-gateway:8000/api/v1
    depends_on:
      - api-gateway
    networks:
      - ecochain-net
    restart: unless-stopped

  # ── Module 1: AI Engine ──
  ai-engine:
    build:
      context: ./module1-frontend-ai/services/ai-engine
      dockerfile: Dockerfile
    container_name: ecochain-ai
    ports:
      - "8001:8001"
    networks:
      - ecochain-net
    restart: unless-stopped

  # ── Module 2: Fabric Gateway API ──
  fabric-gateway:
    build:
      context: ./module2-blockchain/fabric-gateway-api
      dockerfile: Dockerfile
    container_name: ecochain-fabric-gw
    ports:
      - "9000:9000"
    environment:
      - PORT=9000
      - FABRIC_CHANNEL=carbon-channel
      - FABRIC_CHAINCODE=carbon-credit
      - FABRIC_MSP_ID=Org1MSP
      - FABRIC_PEER_ENDPOINT=peer0.org1.example.com:7051
    volumes:
      - ./module2-blockchain/fabric-network/organizations:/app/organizations:ro
    networks:
      - ecochain-net
    restart: unless-stopped

  # ── Dev only: Mock Blockchain ──
  mock-blockchain:
    build:
      context: ./module1-frontend-ai/services/api-gateway
      dockerfile: Dockerfile.mock
    container_name: ecochain-mock
    ports:
      - "9001:9001"
    profiles:
      - dev
    networks:
      - ecochain-net

networks:
  ecochain-net:
    driver: bridge
```

---

## Git Workflow

```bash
# Branch naming:
# Nandha's branches:
git checkout -b feat/nandha/retire-endpoint
git checkout -b fix/nandha/wallet-key-mismatch
git checkout -b feat/nandha/ai-anomaly-detection
git checkout -b feat/nandha/web-portal-farmer-dashboard

# Indhu's branches:
git checkout -b feat/indhu/activity-contract
git checkout -b feat/indhu/credit-contract
git checkout -b feat/indhu/fabric-gateway-api
git checkout -b feat/indhu/couchdb-indexes

# Integration branch:
git checkout -b integration/module1-module2-connect

# Never push directly to main
# PR required for all merges into main
```

---

## Code Review Checklist (before merging any PR)

**For Nandha's PRs:**
- [ ] No `.env` file committed
- [ ] No `venv/` folder committed
- [ ] All routes have auth `Depends()` guard
- [ ] HTTP status codes correct (404, 403, 400, 500)
- [ ] Wallet uses `ownerId` not `farmerId`
- [ ] ActivityType validated as Literal enum

**For Indhu's PRs:**
- [ ] Chaincode functions handle nil/not-found gracefully
- [ ] All state mutations use `PutState` after reading with `GetState`
- [ ] No sensitive data (GPS coordinates) on shared ledger — use PDC
- [ ] CouchDB indexes present for all query fields
- [ ] Gateway API returns the exact JSON schema from `shared/api-contracts/`

---

## Demo Script (for Blockchain India Challenge)

### Scene 1: Farmer registers activity
1. Open Farmer Mobile App / Web Portal as `raman@farmer.com`
2. Click "Submit New Activity"
3. Select "No-Till Farming", enter 3.2 acres, GPS auto-filled
4. Click Submit → show `{ txId: "ECBH-2026-84921", status: "pending_verification" }`
5. **Point out**: txId is from Hyperledger Fabric ledger

### Scene 2: Activity recorded on blockchain
1. Open Fabric Explorer / Raw ledger query
2. Show the block with the txId from Step 1
3. Show immutable record: farmerId, activityType, acres, GPS, timestamp
4. **Point out**: Cannot be altered — this is the Hyperledger ledger

### Scene 3: Auditor verifies
1. Open Auditor Portal as `priya@auditor.com`
2. Show pending activities list → Raman's activity appears
3. Click "Verify" → status changes to "verified"
4. Show blockchain ledger updated with verifiedBy, verifiedAt
5. **Point out**: Auditor identity recorded on-chain — full accountability

### Scene 4 (bonus): Credits minted, sold
1. Admin mints 2.56 credits → farmer wallet shows balance
2. Industry logs in → sees marketplace → buys credits
3. Show transaction on blockchain ledger

**Total demo time: ~8 minutes**
