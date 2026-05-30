# EcoChain Bharat — Complete File Structure

> Current state (✅ exists | 🔧 exists but needs fix | 🔲 not built yet)

---

## Root
```
ecochain-bharat/
├── .env.example                    ✅
├── .gitignore                      🔧 (must exclude venv/, __pycache__/, .env)
├── .prettierrc                     ✅
├── docker-compose.yml              🔧 (empty — needs content)
├── package.json                    ✅
├── README.md                       ✅
├── repository-structure.md         ✅
├── scripts/
│   ├── start-dev.sh                ✅
│   ├── stop-dev.sh                 ✅
│   └── reset-network.sh            ✅
├── shared/                         (integration contracts between modules)
├── module1-frontend-ai/
└── module2-blockchain/
```

---

## Shared (Integration Contract Layer)
```
shared/
├── api-contracts/
│   ├── registerActivity.schema.json    🔧 (empty — fill with JSON schema)
│   ├── verifyActivity.schema.json      🔧 (empty)
│   ├── mintCredit.schema.json          🔧 (empty)
│   ├── transferCredit.schema.json      🔧 (empty)
│   ├── retireCredit.schema.json        🔧 (empty)
│   ├── audit.schema.json               🔧 (empty)
│   └── marketplace.schema.json         🔧 (empty)
├── constants/
│   ├── activityTypes.ts                🔧 (empty — fill with enum)
│   ├── blockchain.ts                   🔧 (empty)
│   ├── roles.ts                        🔧 (empty)
│   └── statuses.ts                     🔧 (empty)
└── types/
    ├── activity.ts                     🔧 (empty)
    ├── audit.ts                        🔧 (empty)
    ├── credit.ts                       🔧 (empty)
    ├── farmer.ts                       🔧 (empty)
    └── transaction.ts                  🔧 (empty)
```

---

## Module 1 — Frontend + AI (Nandha)
```
module1-frontend-ai/
├── README.md                           ✅
│
├── apps/
│   ├── farmer-mobile/                  (React Native / Expo)
│   │   ├── app.json                    🔧 (empty)
│   │   ├── babel.config.js             🔧 (empty)
│   │   ├── package.json                🔧 (empty — needs deps)
│   │   └── src/
│   │       ├── App.tsx                 🔧 (stub only)
│   │       ├── screens/
│   │       │   ├── LoginScreen.tsx     🔲
│   │       │   ├── HomeScreen.tsx      🔲
│   │       │   ├── SubmitActivity.tsx  🔲
│   │       │   ├── MyActivities.tsx    🔲
│   │       │   └── MyWallet.tsx        🔲
│   │       ├── components/
│   │       │   ├── ActivityForm.tsx    🔲
│   │       │   └── WalletCard.tsx      🔲
│   │       └── services/
│   │           └── api.ts              🔲
│   │
│   └── web-portal/                     (Next.js 14)
│       ├── .env.local.example          ✅
│       ├── .eslintrc.js                🔧 (empty)
│       ├── next.config.js              🔧 (empty)
│       ├── package.json                🔧 (empty — needs deps)
│       ├── tailwind.config.js          🔧 (empty)
│       ├── Dockerfile                  ✅
│       └── src/app/
│           ├── page.tsx                🔧 (stub only)
│           ├── login/page.tsx          🔲
│           ├── dashboard/
│           │   ├── farmer/page.tsx     🔲
│           │   ├── industry/page.tsx   🔲
│           │   ├── auditor/page.tsx    🔲
│           │   └── admin/page.tsx      🔲
│           ├── marketplace/page.tsx    🔲
│           └── transactions/page.tsx   🔲
│
└── services/
    ├── ai-engine/
    │   ├── requirements.txt            🔧 (empty — needs deps)
    │   └── app/
    │       ├── main.py                 🔲
    │       ├── models/
    │       │   ├── anomaly_detector.py 🔲
    │       │   └── compliance_predictor.py 🔲
    │       └── routes/
    │           └── predict.py          🔲
    │
    └── api-gateway/
        ├── .env                        🔧 (EXISTS — rotate MongoDB password NOW)
        ├── .gitignore                  ✅ (verify venv/ is excluded)
        ├── requirements.txt            🔧 (bloated — needs cleanup)
        ├── Dockerfile                  ✅
        ├── mock-blockchain/
        │   └── app.py                  ✅ (working mock)
        └── app/
            ├── __init__.py             ✅
            ├── main.py                 ✅ CORS configured
            ├── config.py               ✅ env-based config
            ├── database.py             🔧 (needs lifespan pattern)
            ├── utils/
            │   └── objectId.py         🔲 (file exists but check content)
            ├── schemas/
            │   ├── activity.py         🔧 (activityType needs Literal enum)
            │   ├── auth.py             🔧 (has old UserRegister with role:str)
            │   ├── transaction.py      ✅
            │   └── wallet.py           🔧 (uses farmerId key — change to ownerId)
            ├── routes/
            │   ├── __init__.py         ✅
            │   ├── auth.py             ✅ (has correct Literal roles inline)
            │   ├── activity.py         ✅ CREDIT_RATES, auth guards all correct
            │   ├── transaction.py      🔧 wallet queries use farmerId — fix to ownerId
            │   ├── wallet.py           🔧 queries farmerId — fix to ownerId
            │   ├── history.py          ✅
            │   └── marketplace.py      🔧 (needs field projection)
            └── services/
                ├── auth_dependency.py  ✅ all roles implemented
                ├── blockchain_service.py ✅ reads BLOCKCHAIN_URL from config
                ├── security.py         ✅ bcrypt + JWT
                └── requirements.txt    🔧 (duplicate — use root requirements.txt)
```

---

## Module 2 — Blockchain (Indhu)
```
module2-blockchain/
├── README.md                           ✅
├── .env                                ✅
├── .gitignore                          ✅
├── docker-compose.yml                  ✅
│
├── chaincode/carbon-credit/            (Go chaincode)
│   ├── main.go                         🔧 (check content)
│   ├── go.mod                          ✅
│   ├── go.sum                          ✅
│   ├── cmd/main.go                     🔧
│   ├── META-INF/statedb/couchdb/
│   │   └── indexes/
│   │       ├── activityIndex.json      🔧 (check content)
│   │       └── creditIndex.json        🔧 (check content)
│   ├── contract/
│   │   ├── activity_contract.go        🔧 (file exists, check if empty)
│   │   ├── credit_contract.go          🔧 (file exists, check if empty)
│   │   └── audit_contract.go           🔧 (file exists, check if empty)
│   ├── models/
│   │   ├── activity.go                 🔧 (check content)
│   │   ├── credit.go                   🔧 (check content)
│   │   └── transaction.go              🔧 (check content)
│   ├── utils/
│   │   ├── helpers.go                  🔧
│   │   └── validation.go               🔧
│   └── tests/
│       ├── activity_test.go            🔧
│       └── credit_test.go              🔧
│
├── fabric-gateway-api/                 (Node.js Express — Port 9000)
│   ├── .env                            ✅
│   ├── Dockerfile                      ✅
│   ├── package.json                    🔧 (check content)
│   └── src/
│       ├── server.js                   🔧 (check content)
│       ├── app.js                      🔧 (check content)
│       ├── config/
│       │   ├── fabric.config.js        🔧
│       │   └── wallet.config.js        🔧
│       ├── controllers/
│       │   ├── activity.controller.js  🔧
│       │   ├── audit.controller.js     🔧
│       │   └── credit.controller.js    🔧
│       ├── middleware/
│       │   ├── auth.middleware.js      🔧
│       │   └── error.middleware.js     🔧
│       ├── routes/
│       │   ├── activity.routes.js      🔧
│       │   ├── audit.routes.js         🔧
│       │   └── credit.routes.js        🔧
│       ├── services/
│       │   ├── fabric.service.js       🔧 (core Fabric Gateway connection)
│       │   ├── activity.service.js     🔧
│       │   └── wallet.service.js       🔧
│       └── utils/
│           └── response.js             🔧
│
├── fabric-network/
│   ├── network.sh                      ✅
│   ├── setOrgEnv.sh                    ✅
│   ├── configtx/
│   │   ├── configtx.yaml               ✅
│   │   └── core.yaml                   ✅
│   ├── channel-artifacts/
│   │   ├── genesis.block               ✅
│   │   ├── channel.tx                  ✅
│   │   └── anchor-peers.tx             ✅
│   ├── docker/
│   │   ├── docker-compose-test-net.yaml ✅
│   │   ├── docker-compose-ca.yaml      ✅
│   │   └── docker-compose-couch.yaml   ✅
│   └── scripts/
│       ├── networkUp.sh                ✅
│       ├── createChannel.sh            ✅
│       ├── deployCC.sh                 ✅
│       └── envVar.sh                   ✅
│
├── scripts/
│   ├── start-network.sh                ✅
│   ├── stop-network.sh                 ✅
│   ├── deploy-chaincode.sh             ✅
│   ├── invoke-chaincode.sh             ✅
│   └── reset-network.sh                ✅
│
└── docs/
    ├── chaincode-api.md                ✅
    ├── deployment.md                   ✅
    ├── fabric-network.md               ✅
    ├── gateway-api.md                  ✅
    └── setup.md                        ✅
```

---

## Files to add to .gitignore immediately
```
# Python
venv/
__pycache__/
*.pyc
.env

# Node
node_modules/
.env.local

# Fabric artifacts (generated)
module2-blockchain/fabric-network/channel-artifacts/*.block
module2-blockchain/fabric-network/channel-artifacts/*.tx
module2-blockchain/fabric-network/organizations/

# OS
.DS_Store
Thumbs.db
```
