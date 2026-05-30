# Module 1 — Nandha's Implementation Plan
## Frontend + AI + API Gateway

---

## Current Status Summary

| Component | Status |
|-----------|--------|
| API Gateway (FastAPI) | ✅ ~80% done — fixes needed |
| Auth (JWT + roles) | ✅ Working |
| Activity routes | ✅ Working |
| Transaction routes | 🔧 wallet key bug |
| Wallet routes | 🔧 wallet key bug |
| Marketplace | 🔧 needs projection |
| Retire endpoint | 🔲 Not built |
| Web Portal (Next.js) | 🔧 Stub only |
| Farmer Mobile App | 🔧 Stub only |
| AI Engine | 🔲 Not started |

---

## IMMEDIATE FIXES (Do today — before anything else)

### Fix 1: Rotate MongoDB password
Your `.env` is committed with the real password. Do this now:
1. Go to MongoDB Atlas → Database Access → Edit user `Nandha`
2. Set new password
3. Update your local `.env`
4. Add `.env` to `.gitignore`

### Fix 2: Fix wallet key mismatch in transaction.py
```python
# In app/routes/transaction.py — change ALL occurrences:
# ❌ "farmerId"  →  ✅ "ownerId"

# Line ~30: seller lookup
seller_wallet = await database.wallets.find_one({"ownerId": data.sellerId})

# Line ~55: seller update
await database.wallets.update_one({"ownerId": data.sellerId}, ...)

# Line ~65: buyer lookup
buyer_wallet = await database.wallets.find_one({"ownerId": data.buyerId})

# Line ~75: buyer create — remove farmerId field:
buyer_data = {
    "ownerId": data.buyerId,
    "ownerType": "industry",
    "totalCredits": data.credits,
    "availableCredits": data.credits,
    "soldCredits": 0
}

# Line ~85: buyer update
await database.wallets.update_one({"ownerId": data.buyerId}, ...)
```

### Fix 3: Fix wallet.py key
```python
# app/routes/wallet.py
wallet = await database.wallets.find_one({"ownerId": farmer_id})
```

### Fix 4: Fix schemas/auth.py — remove duplicate UserRegister
```python
# DELETE the UserRegister class from schemas/auth.py
# It's already correctly defined in routes/auth.py
# schemas/auth.py should only contain UserLogin
```

### Fix 5: Add reject guard in activity.py
```python
@router.post("/{activity_id}/reject")
async def reject_activity(activity_id: str, user=Depends(auditor_only)):
    activity = await database.activities.find_one({"_id": ObjectId(activity_id)})
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    
    # ADD THIS GUARD:
    if activity["status"] != "pending":
        raise HTTPException(status_code=400, detail="Activity already processed")
    ...
```

### Fix 6: Add activityType validation in schemas/activity.py
```python
from typing import Literal

ActivityType = Literal[
    "no_till", "agroforestry", "organic_farming",
    "soil_carbon", "efficient_irrigation"
]

class ActivityCreate(BaseModel):
    farmerId: str
    activityType: ActivityType   # ← was just str
    acres: float
    location: Optional[Location] = None
```

### Fix 7: Clean requirements.txt
```bash
# Run from api-gateway folder:
pip install pipreqs
pipreqs app/ --force --savepath requirements.txt
```
The actual dependencies are only:
```
fastapi==0.111.0
uvicorn==0.29.0
motor==3.4.0
pymongo==4.7.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
httpx==0.27.0
python-dotenv==1.0.1
pydantic[email]==2.7.0
```

### Fix 8: Add MongoDB lifespan to main.py
```python
from contextlib import asynccontextmanager
from app.database import client

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    client.close()

app = FastAPI(title="EcoChain Bharat API Gateway", version="1.0.0", lifespan=lifespan)
```

---

## Week 1–2: Complete API Gateway

### Build retire endpoint (new file: app/routes/retire.py)
```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.database import database
from app.services.auth_dependency import industry_only
from app.services.blockchain_service import retire_credit_on_blockchain
from bson import ObjectId
from uuid import uuid4
from datetime import datetime

router = APIRouter(prefix="/credits", tags=["Credits"])

class RetireRequest(BaseModel):
    ownerId: str
    amount: float
    reason: str

@router.post("/{credit_id}/retire")
async def retire_credit(credit_id: str, data: RetireRequest, user=Depends(industry_only)):
    wallet = await database.wallets.find_one({"ownerId": data.ownerId})
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    if wallet["availableCredits"] < data.amount:
        raise HTTPException(status_code=400, detail="Insufficient credits")

    blockchain_response = await retire_credit_on_blockchain({
        "creditId": credit_id, "ownerId": data.ownerId,
        "amount": data.amount, "reason": data.reason
    })

    await database.wallets.update_one(
        {"ownerId": data.ownerId},
        {"$inc": {"availableCredits": -data.amount, "retiredCredits": data.amount}}
    )

    retirement = {
        "txId": f"RETIRE-{uuid4()}",
        "creditId": credit_id,
        "ownerId": data.ownerId,
        "amount": data.amount,
        "reason": data.reason,
        "retiredAt": datetime.utcnow().isoformat(),
        "blockchainTxId": blockchain_response.get("txId")
    }
    await database.retirements.insert_one(retirement)
    retirement["_id"] = str(retirement["_id"])

    return {"success": True, "message": "Credits retired successfully", "data": retirement}
```

### Add retire to blockchain_service.py
```python
async def retire_credit_on_blockchain(data):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BLOCKCHAIN_URL}/chaincode/retireCredit",
            json=data
        )
        return response.json()
```

### Add retire to mock-blockchain/app.py
```python
@app.post("/chaincode/retireCredit")
async def retire_credit(payload: dict):
    return {
        "txId": f"RETIRE-{random.randint(10000,99999)}",
        "status": "retired",
        "retiredAt": datetime.utcnow().isoformat()
    }
```

### Add status filter + pagination to GET /activities
```python
@router.get("")
async def get_all_activities(
    user=Depends(get_current_user),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100)
):
    query = {}
    if status:
        query["status"] = status
    skip = (page - 1) * limit
    cursor = database.activities.find(query).skip(skip).limit(limit)
    activities = []
    async for a in cursor:
        a["_id"] = str(a["_id"])
        activities.append(a)
    total = await database.activities.count_documents(query)
    return {"success": True, "data": activities, "total": total, "page": page}
```

### Add marketplace projection
```python
@router.get("")
async def get_marketplace(user=Depends(get_current_user)):
    marketplace = []
    cursor = database.wallets.find(
        {"availableCredits": {"$gt": 0}},
        {"ownerId": 1, "ownerType": 1, "availableCredits": 1, "_id": 0}
    )
    async for wallet in cursor:
        marketplace.append(wallet)
    return {"success": True, "data": marketplace}
```

---

## Week 3–4: AI Engine

Create `module1-frontend-ai/services/ai-engine/app/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="EcoChain AI Engine", version="1.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
```

### Anomaly Detection (models/anomaly_detector.py)
```python
import numpy as np
from sklearn.ensemble import IsolationForest

class AnomalyDetector:
    def __init__(self):
        self.model = IsolationForest(contamination=0.1, random_state=42)
        self._trained = False

    def train(self, data: list[dict]):
        features = [[d["acres"], d["creditAmount"]] for d in data]
        self.model.fit(features)
        self._trained = True

    def predict(self, acres: float, credit_amount: float) -> dict:
        if not self._trained:
            return {"anomaly": False, "score": 0.0, "message": "Model not trained"}
        score = self.model.score_samples([[acres, credit_amount]])[0]
        is_anomaly = score < -0.5
        return {
            "anomaly": bool(is_anomaly),
            "score": float(score),
            "message": "Suspicious activity detected" if is_anomaly else "Activity looks normal"
        }
```

### Compliance Predictor (models/compliance_predictor.py)
```python
class CompliancePredictor:
    CREDIT_RATES = {
        "no_till": 0.8, "agroforestry": 1.2,
        "organic_farming": 0.9, "soil_carbon": 1.0,
        "efficient_irrigation": 0.5
    }

    def predict_shortfall(self, target_credits: float, available_credits: float,
                          days_to_deadline: int) -> dict:
        gap = target_credits - available_credits
        urgency = "high" if days_to_deadline < 30 else "medium" if days_to_deadline < 90 else "low"
        return {
            "targetCredits": target_credits,
            "availableCredits": available_credits,
            "gap": max(0, gap),
            "shortfall": gap > 0,
            "daysToDeadline": days_to_deadline,
            "urgency": urgency,
            "recommendation": f"Buy {round(gap, 2)} credits urgently" if gap > 0 else "Compliance target met"
        }
```

### AI Routes (routes/predict.py)
```python
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/ai", tags=["AI"])

class AnomalyRequest(BaseModel):
    acres: float
    creditAmount: float

class ComplianceRequest(BaseModel):
    targetCredits: float
    availableCredits: float
    daysToDeadline: int

@router.post("/anomaly-check")
async def check_anomaly(data: AnomalyRequest):
    # call detector
    pass

@router.post("/compliance-forecast")
async def compliance_forecast(data: ComplianceRequest):
    # call predictor
    pass
```

---

## Week 5–6: Web Portal (Next.js)

### Priority pages to build:

**1. Login page** (`src/app/login/page.tsx`)
- Email + password form
- Calls `POST /api/v1/auth/login`
- Stores JWT in localStorage
- Redirects to role-based dashboard

**2. Farmer Dashboard** (`src/app/dashboard/farmer/page.tsx`)
- My Activities list (status badges)
- Submit New Activity button
- My Wallet balance card
- Credits history

**3. Auditor Dashboard** (`src/app/dashboard/auditor/page.tsx`)
- Pending Activities queue
- Verify / Reject buttons
- Activity details modal

**4. Industry Dashboard** (`src/app/dashboard/industry/page.tsx`)
- Marketplace credits table
- Buy Credits button
- My Compliance status
- Shortfall forecast widget (from AI engine)

**5. Admin Dashboard** (`src/app/dashboard/admin/page.tsx`)
- All activities with mint button
- User management

### API service layer (`src/lib/api.ts`)
```typescript
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

export async function apiFetch(path: string, options?: RequestInit) {
  const token = localStorage.getItem('token')
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options?.headers,
    },
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}
```

---

## Week 7–8: Farmer Mobile App (React Native)

### Install dependencies
```bash
cd module1-frontend-ai/apps/farmer-mobile
npx expo install @react-navigation/native @react-navigation/native-stack
npx expo install expo-location expo-camera
npx expo install axios @react-native-async-storage/async-storage
```

### Priority screens:
1. **LoginScreen** — email/password → JWT stored in AsyncStorage
2. **HomeScreen** — welcome, quick stats
3. **SubmitActivityScreen** — dropdown activity type, acres input, GPS auto-fill
4. **MyActivitiesScreen** — list with status chips
5. **MyWalletScreen** — balance + transaction history

---

## Testing Checklist for Nandha

```bash
# Start mock blockchain (terminal 1)
cd module1-frontend-ai/services/api-gateway
python -m uvicorn mock-blockchain.app:app --port 9001

# Start API gateway (terminal 2)
python -m uvicorn app.main:app --reload --port 8000

# Test with curl:
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Raman","email":"raman@test.com","password":"test123","role":"farmer"}'

curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"raman@test.com","password":"test123"}'
# Copy the token from response

curl -X POST http://localhost:8000/api/v1/activities \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"farmerId":"farmer001","activityType":"no_till","acres":3.2}'
```
