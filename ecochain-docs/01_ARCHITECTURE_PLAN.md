# EcoChain Bharat — Full System Architecture Plan

> Team AZUO | Version 1.0 | May 2026

---

## 1. Overview

EcoChain Bharat is a **production-grade permissioned blockchain platform** for India's Carbon Credit Trading Scheme (CCTS). It connects smallholder farmers, industries, auditors, and regulators on a single trusted system built on Hyperledger Fabric (Vishvasya BaaS).

The system is split into two independently developed modules that integrate via a clean REST API contract:

| Module | Owner | Core Responsibility |
|--------|-------|---------------------|
| Module 1 — Frontend + AI | Nandha | User-facing apps, API Gateway, AI engine |
| Module 2 — Blockchain | Indhu | Hyperledger Fabric network, chaincode, Fabric Gateway API |

---

## 2. System Architecture — All Layers

```
┌─────────────────────────────────────────────────────────────────────┐
│  USER LAYER                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  ┌───────────┐  │
│  │ Farmer App   │  │ Industry     │  │ Auditor  │  │ Regulator │  │
│  │ React Native │  │ Next.js Web  │  │ Web      │  │ Web       │  │
│  │ Mobile       │  │ Portal       │  │ Portal   │  │ Dashboard │  │
│  └──────┬───────┘  └──────┬───────┘  └────┬─────┘  └─────┬─────┘  │
└─────────┼─────────────────┼───────────────┼──────────────┼─────────┘
          │                 │               │              │
          ▼                 ▼               ▼              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  MODULE 1 — API GATEWAY (FastAPI, Port 8000)                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  JWT Auth + Role-Based Access Control (farmer/industry/        │ │
│  │  auditor/admin) — HTTPBearer + python-jose                     │ │
│  ├────────────────────────────────────────────────────────────────┤ │
│  │  Routes:                                                       │ │
│  │  /api/v1/auth          → register, login                      │ │
│  │  /api/v1/activities    → CRUD, verify, reject, mint           │ │
│  │  /api/v1/credits       → transfer                             │ │
│  │  /api/v1/wallet        → balance lookup                       │ │
│  │  /api/v1/transactions  → history, by-farmer                   │ │
│  │  /api/v1/marketplace   → available credits listing            │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              │                                      │
│         ┌────────────────────┼────────────────────┐                │
│         ▼                    ▼                    ▼                │
│  ┌─────────────┐   ┌──────────────────┐   ┌───────────────┐       │
│  │  MongoDB    │   │  Blockchain      │   │  AI Engine    │       │
│  │  (Motor     │   │  Service         │   │  (FastAPI,    │       │
│  │  async)     │   │  (httpx calls    │   │  scikit-learn)│       │
│  │  Activities │   │  to Module 2)    │   │  Anomaly +    │       │
│  │  Users      │   │                  │   │  Forecasting  │       │
│  │  Wallets    │   │  POST /chaincode/ │   │               │       │
│  │  Txns       │   │  registerActivity│   │               │       │
│  └─────────────┘   │  verifyActivity  │   └───────────────┘       │
│                    │  mintCredit      │                            │
│                    │  transferCredit  │                            │
│                    │  retireCredit    │                            │
│                    └────────┬─────────┘                            │
└─────────────────────────────┼───────────────────────────────────── ┘
                              │  HTTP (JSON)
                              │  BLOCKCHAIN_URL=http://localhost:9000
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  MODULE 2 — FABRIC GATEWAY API (Node.js/Express, Port 9000)        │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Routes:                                                       │ │
│  │  POST /chaincode/registerActivity                              │ │
│  │  POST /chaincode/verifyActivity                                │ │
│  │  POST /chaincode/mintCredit                                    │ │
│  │  POST /chaincode/transferCredit                                │ │
│  │  POST /chaincode/retireCredit                                  │ │
│  │  GET  /chaincode/queryActivity/:id                             │ │
│  │  GET  /chaincode/queryCredit/:id                               │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              │                                      │
│                              ▼                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  Fabric SDK (fabric-gateway npm)                               │ │
│  │  Connects to peers via gRPC + TLS using X.509 certs            │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────┬───────────────────────────────────── ┘
                              │  gRPC
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  HYPERLEDGER FABRIC NETWORK (Vishvasya BaaS / Local Docker)        │
│                                                                     │
│  Orderer (Raft)                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  Peer — BEE  │  │ Peer — CPCB  │  │ Peer —       │             │
│  │  Org         │  │ Org          │  │ Farmer Org   │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│                                                                     │
│  Channels:                                                          │
│  ├── carbon-channel     (farmer + BEE + auditor peers)             │
│  └── compliance-channel (industry + regulator peers)               │
│                                                                     │
│  Chaincode: carbon-credit (Go)                                      │
│  ├── ActivityContract   → RegisterActivity, VerifyActivity         │
│  ├── CreditContract     → MintCredit, TransferCredit, RetireCredit │
│  └── AuditContract      → GetAuditTrail, QueryByFarmer             │
│                                                                     │
│  State DB: CouchDB (indexed queries)                                │
│  Private Data Collections: farmer GPS, sequestration metrics        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Data Flow — Full Carbon Credit Lifecycle

### Step 1: Farmer registers an activity
```
Farmer App → POST /api/v1/activities
  → API Gateway validates JWT (farmer_only)
  → Calls mock-blockchain / Fabric Gateway → registerActivity chaincode
  → Saves to MongoDB (status: "pending_verification")
  → Returns { activityId, txId, status }
```

### Step 2: Auditor verifies
```
Auditor Portal → GET /api/v1/activities/pending
  → Lists all pending activities
  → POST /api/v1/activities/{id}/verify
  → API Gateway validates JWT (auditor_only)
  → Calls Fabric Gateway → verifyActivity chaincode
  → MongoDB updated (status: "verified", verifiedBy: auditorId)
```

### Step 3: Admin mints credits
```
Admin → POST /api/v1/activities/{id}/mint
  → API Gateway validates JWT (admin_only)
  → Calculates credit_amount = acres × CREDIT_RATES[activityType]
  → Calls Fabric Gateway → mintCredit chaincode
  → MongoDB: activity status → "credits_minted"
  → MongoDB: farmer wallet updated (availableCredits += amount)
```

### Step 4: Industry buys credits (marketplace)
```
Industry Portal → GET /api/v1/marketplace
  → Lists all wallets with availableCredits > 0
  → POST /api/v1/credits/transfer { sellerId, buyerId, credits }
  → API Gateway validates JWT (industry_only)
  → Fabric Gateway → transferCredit chaincode
  → MongoDB: seller wallet decremented, buyer wallet incremented
  → Transaction record saved
```

### Step 5: Credits retired (compliance)
```
Industry → POST /api/v1/credits/retire { creditId, amount }
  → Fabric Gateway → retireCredit chaincode
  → Credits marked as retired on-chain
  → Audit trail recorded for BEE/CPCB
```

---

## 4. Technology Stack

### Module 1 (Nandha)
| Layer | Technology |
|-------|-----------|
| API Gateway | Python 3.10, FastAPI, Uvicorn |
| Auth | JWT (python-jose), bcrypt (passlib) |
| Database | MongoDB Atlas, Motor (async) |
| HTTP Client | httpx (async) |
| AI Engine | Python, scikit-learn, FastAPI |
| Web Portal | Next.js 14, TypeScript, Tailwind CSS |
| Mobile App | React Native, Expo |
| Containerisation | Docker, docker-compose |

### Module 2 (Indhu)
| Layer | Technology |
|-------|-----------|
| Blockchain | Hyperledger Fabric 2.5 |
| Chaincode | Go 1.21 |
| Fabric Gateway API | Node.js, Express.js, fabric-gateway npm |
| State DB | CouchDB |
| Network | Docker Compose (local), Vishvasya BaaS (prod) |
| Crypto | X.509 certificates via Fabric CA |

---

## 5. Security Model

| Concern | Solution |
|---------|----------|
| API authentication | JWT Bearer tokens, 60-min expiry |
| Role enforcement | `farmer_only`, `auditor_only`, `industry_only`, `admin_only` FastAPI dependencies |
| Blockchain identity | X.509 MSP certificates per org/peer |
| Sensitive data | Fabric Private Data Collections (PDCs) for farmer GPS, sequestration metrics |
| Channel isolation | carbon-channel (farmers/auditors) vs compliance-channel (industries/regulators) |
| Secret management | `.env` files (never committed), rotate MongoDB password immediately |

---

## 6. Deployment Architecture

### Development
```
localhost:8000  → Module 1 API Gateway (uvicorn)
localhost:3000  → Module 1 Web Portal (next dev)
localhost:9000  → Module 2 Fabric Gateway API (node)
localhost:9001  → Mock Blockchain (during dev, before Fabric is ready)
localhost:27017 → MongoDB (local or Atlas)
localhost:5984  → CouchDB (Fabric state DB)
```

### Production (Vishvasya BaaS)
```
NIC DC Bhubaneswar  → Fabric Org1 peers
NIC DC Pune         → Fabric Org2 peers  
NIC DC Hyderabad    → Orderer + Fabric Org3 peers
MongoDB Atlas       → Off-chain data (India region)
```
