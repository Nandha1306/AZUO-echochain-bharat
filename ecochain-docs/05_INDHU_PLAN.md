# Module 2 — Indhu's Implementation Plan
## Hyperledger Fabric Blockchain

---

## Current Status Summary

| Component | Status |
|-----------|--------|
| Fabric network config (docker, configtx) | ✅ Structure exists |
| Chaincode contracts (Go) | 🔧 Files exist, likely empty |
| Chaincode models (Go) | 🔧 Files exist, likely empty |
| Fabric Gateway API (Node.js) | 🔧 Files exist, check content |
| CouchDB indexes | 🔧 Files exist, check content |
| Network scripts | ✅ Shell scripts exist |

---

## Setup Order (Do this first)

```bash
# 1. Install Hyperledger Fabric binaries
curl -sSL https://bit.ly/2ysbOFE | bash -s -- 2.5.0 1.5.7

# 2. Install Go 1.21+
# https://go.dev/dl/

# 3. Install Node.js 18+

# 4. Start local Fabric network
cd module2-blockchain
./scripts/start-network.sh

# 5. Verify it's running
docker ps | grep hyperledger
```

---

## Week 1–2: Chaincode (Go)

### Models first

**models/activity.go**
```go
package models

type Activity struct {
    ActivityID   string   `json:"activityId"`
    FarmerID     string   `json:"farmerId"`
    ActivityType string   `json:"activityType"`
    Acres        float64  `json:"acres"`
    Location     Location `json:"location"`
    Status       string   `json:"status"`
    TxID         string   `json:"txId"`
    SubmittedAt  string   `json:"submittedAt"`
    VerifiedBy   string   `json:"verifiedBy,omitempty"`
    VerifiedAt   string   `json:"verifiedAt,omitempty"`
}

type Location struct {
    Lat float64 `json:"lat"`
    Lng float64 `json:"lng"`
}
```

**models/credit.go**
```go
package models

type CarbonCredit struct {
    CreditID     string  `json:"creditId"`
    ActivityID   string  `json:"activityId"`
    FarmerID     string  `json:"farmerId"`
    Amount       float64 `json:"amount"`
    ActivityType string  `json:"activityType"`
    Status       string  `json:"status"` // minted, transferred, retired
    OwnerID      string  `json:"ownerId"`
    MintedAt     string  `json:"mintedAt"`
    RetiredAt    string  `json:"retiredAt,omitempty"`
    RetiredBy    string  `json:"retiredBy,omitempty"`
}
```

**models/transaction.go**
```go
package models

type Transaction struct {
    TxID          string  `json:"txId"`
    Type          string  `json:"type"` // register, verify, mint, transfer, retire
    ActivityID    string  `json:"activityId,omitempty"`
    CreditID      string  `json:"creditId,omitempty"`
    FromID        string  `json:"fromId,omitempty"`
    ToID          string  `json:"toId,omitempty"`
    Amount        float64 `json:"amount,omitempty"`
    Timestamp     string  `json:"timestamp"`
    InitiatedBy   string  `json:"initiatedBy"`
}
```

---

### ActivityContract (contract/activity_contract.go)
```go
package contract

import (
    "encoding/json"
    "fmt"
    "time"

    "github.com/hyperledger/fabric-contract-api-go/contractapi"
    "ecochain/models"
)

type ActivityContract struct {
    contractapi.Contract
}

// RegisterActivity — called when farmer submits an activity
func (c *ActivityContract) RegisterActivity(
    ctx contractapi.TransactionContextInterface,
    activityID, farmerID, activityType string,
    acres float64,
    lat, lng float64,
) (*models.Activity, error) {

    // Check if already exists
    existing, err := ctx.GetStub().GetState(activityID)
    if err != nil {
        return nil, fmt.Errorf("failed to read state: %v", err)
    }
    if existing != nil {
        return nil, fmt.Errorf("activity %s already exists", activityID)
    }

    activity := &models.Activity{
        ActivityID:   activityID,
        FarmerID:     farmerID,
        ActivityType: activityType,
        Acres:        acres,
        Location:     models.Location{Lat: lat, Lng: lng},
        Status:       "pending_verification",
        TxID:         ctx.GetStub().GetTxID(),
        SubmittedAt:  time.Now().UTC().Format(time.RFC3339),
    }

    activityJSON, err := json.Marshal(activity)
    if err != nil {
        return nil, err
    }

    err = ctx.GetStub().PutState(activityID, activityJSON)
    if err != nil {
        return nil, fmt.Errorf("failed to put state: %v", err)
    }

    return activity, nil
}

// VerifyActivity — called by auditor to approve
func (c *ActivityContract) VerifyActivity(
    ctx contractapi.TransactionContextInterface,
    activityID, auditorID string,
) (*models.Activity, error) {

    activityJSON, err := ctx.GetStub().GetState(activityID)
    if err != nil || activityJSON == nil {
        return nil, fmt.Errorf("activity %s not found", activityID)
    }

    var activity models.Activity
    json.Unmarshal(activityJSON, &activity)

    if activity.Status != "pending_verification" {
        return nil, fmt.Errorf("activity is not pending verification")
    }

    activity.Status = "verified"
    activity.VerifiedBy = auditorID
    activity.VerifiedAt = time.Now().UTC().Format(time.RFC3339)

    updatedJSON, _ := json.Marshal(activity)
    ctx.GetStub().PutState(activityID, updatedJSON)

    return &activity, nil
}

// QueryActivity — get activity by ID
func (c *ActivityContract) QueryActivity(
    ctx contractapi.TransactionContextInterface,
    activityID string,
) (*models.Activity, error) {

    activityJSON, err := ctx.GetStub().GetState(activityID)
    if err != nil || activityJSON == nil {
        return nil, fmt.Errorf("activity %s not found", activityID)
    }

    var activity models.Activity
    json.Unmarshal(activityJSON, &activity)
    return &activity, nil
}

// GetActivityHistory — full audit trail
func (c *ActivityContract) GetActivityHistory(
    ctx contractapi.TransactionContextInterface,
    activityID string,
) ([]map[string]interface{}, error) {

    resultsIterator, err := ctx.GetStub().GetHistoryForKey(activityID)
    if err != nil {
        return nil, err
    }
    defer resultsIterator.Close()

    var history []map[string]interface{}
    for resultsIterator.HasNext() {
        response, err := resultsIterator.Next()
        if err != nil {
            return nil, err
        }
        var record map[string]interface{}
        json.Unmarshal(response.Value, &record)
        record["txId"] = response.TxId
        record["timestamp"] = response.Timestamp
        history = append(history, record)
    }
    return history, nil
}
```

---

### CreditContract (contract/credit_contract.go)
```go
package contract

import (
    "encoding/json"
    "fmt"
    "time"

    "github.com/hyperledger/fabric-contract-api-go/contractapi"
    "ecochain/models"
)

type CreditContract struct {
    contractapi.Contract
}

// MintCredit — creates carbon credit tokens after activity is verified
func (c *CreditContract) MintCredit(
    ctx contractapi.TransactionContextInterface,
    creditID, activityID, farmerID, activityType string,
    amount float64,
) (*models.CarbonCredit, error) {

    existing, _ := ctx.GetStub().GetState(creditID)
    if existing != nil {
        return nil, fmt.Errorf("credit %s already exists", creditID)
    }

    credit := &models.CarbonCredit{
        CreditID:     creditID,
        ActivityID:   activityID,
        FarmerID:     farmerID,
        Amount:       amount,
        ActivityType: activityType,
        Status:       "minted",
        OwnerID:      farmerID,
        MintedAt:     time.Now().UTC().Format(time.RFC3339),
    }

    creditJSON, _ := json.Marshal(credit)
    ctx.GetStub().PutState(creditID, creditJSON)
    return credit, nil
}

// TransferCredit — moves credits from seller to buyer
func (c *CreditContract) TransferCredit(
    ctx contractapi.TransactionContextInterface,
    creditID, fromID, toID string,
    amount float64,
) (*models.CarbonCredit, error) {

    creditJSON, err := ctx.GetStub().GetState(creditID)
    if err != nil || creditJSON == nil {
        return nil, fmt.Errorf("credit %s not found", creditID)
    }

    var credit models.CarbonCredit
    json.Unmarshal(creditJSON, &credit)

    if credit.OwnerID != fromID {
        return nil, fmt.Errorf("credit not owned by %s", fromID)
    }
    if credit.Status == "retired" {
        return nil, fmt.Errorf("cannot transfer retired credit")
    }

    credit.OwnerID = toID
    credit.Status = "transferred"

    updatedJSON, _ := json.Marshal(credit)
    ctx.GetStub().PutState(creditID, updatedJSON)
    return &credit, nil
}

// RetireCredit — permanently retires credit for compliance
func (c *CreditContract) RetireCredit(
    ctx contractapi.TransactionContextInterface,
    creditID, ownerID, reason string,
) (*models.CarbonCredit, error) {

    creditJSON, err := ctx.GetStub().GetState(creditID)
    if err != nil || creditJSON == nil {
        return nil, fmt.Errorf("credit %s not found", creditID)
    }

    var credit models.CarbonCredit
    json.Unmarshal(creditJSON, &credit)

    if credit.OwnerID != ownerID {
        return nil, fmt.Errorf("credit not owned by %s", ownerID)
    }
    if credit.Status == "retired" {
        return nil, fmt.Errorf("credit already retired")
    }

    credit.Status = "retired"
    credit.RetiredAt = time.Now().UTC().Format(time.RFC3339)
    credit.RetiredBy = ownerID

    updatedJSON, _ := json.Marshal(credit)
    ctx.GetStub().PutState(creditID, updatedJSON)
    return &credit, nil
}

// QueryCredit — get credit by ID
func (c *CreditContract) QueryCredit(
    ctx contractapi.TransactionContextInterface,
    creditID string,
) (*models.CarbonCredit, error) {

    creditJSON, err := ctx.GetStub().GetState(creditID)
    if err != nil || creditJSON == nil {
        return nil, fmt.Errorf("credit %s not found", creditID)
    }

    var credit models.CarbonCredit
    json.Unmarshal(creditJSON, &credit)
    return &credit, nil
}
```

---

### main.go (chaincode entry point)
```go
package main

import (
    "log"
    "github.com/hyperledger/fabric-contract-api-go/contractapi"
    "ecochain/contract"
)

func main() {
    activityContract := new(contract.ActivityContract)
    creditContract := new(contract.CreditContract)
    auditContract := new(contract.AuditContract)

    chaincode, err := contractapi.NewChaincode(
        activityContract,
        creditContract,
        auditContract,
    )
    if err != nil {
        log.Fatalf("Error creating chaincode: %v", err)
    }

    if err := chaincode.Start(); err != nil {
        log.Fatalf("Error starting chaincode: %v", err)
    }
}
```

---

## Week 3–4: Fabric Gateway API (Node.js)

### fabric-gateway-api/src/services/fabric.service.js
```javascript
const { connect, hash } = require('@hyperledger/fabric-gateway');
const grpc = require('@grpc/grpc-js');
const { promises: fs } = require('fs');
const path = require('path');

let gateway = null;
let client = null;

async function connectToFabric() {
    const tlsCertPath = process.env.FABRIC_TLS_CERT_PATH;
    const identityCertPath = process.env.FABRIC_IDENTITY_CERT_PATH;
    const identityKeyPath = process.env.FABRIC_IDENTITY_KEY_PATH;
    const peerEndpoint = process.env.FABRIC_PEER_ENDPOINT || 'localhost:7051';
    const mspId = process.env.FABRIC_MSP_ID || 'Org1MSP';

    const tlsRootCert = await fs.readFile(tlsCertPath);
    const credentials = grpc.credentials.createSsl(tlsRootCert);
    client = new grpc.Client(peerEndpoint, credentials);

    const identity = {
        mspId,
        credentials: await fs.readFile(identityCertPath),
    };

    const signer = {
        sign: async (bytes) => {
            const key = await fs.readFile(identityKeyPath);
            // sign with private key
        }
    };

    gateway = connect({ client, identity, signer, hash: hash.sha256 });
    console.log('Connected to Fabric network');
    return gateway;
}

async function getContract() {
    if (!gateway) await connectToFabric();
    const network = gateway.getNetwork(process.env.FABRIC_CHANNEL || 'carbon-channel');
    return network.getContract(process.env.FABRIC_CHAINCODE || 'carbon-credit');
}

module.exports = { getContract, connectToFabric };
```

### fabric-gateway-api/src/controllers/activity.controller.js
```javascript
const { getContract } = require('../services/fabric.service');
const { successResponse, errorResponse } = require('../utils/response');

exports.registerActivity = async (req, res) => {
    try {
        const { farmerId, activityType, acres, location } = req.body;
        const activityId = `ACT-${farmerId}-${Date.now()}`;
        const contract = await getContract();

        await contract.submitTransaction(
            'ActivityContract:RegisterActivity',
            activityId, farmerId, activityType,
            acres.toString(),
            (location?.lat || 0).toString(),
            (location?.lng || 0).toString()
        );

        const txId = contract.txId || `ECBH-2026-${Math.floor(Math.random() * 99999)}`;

        return successResponse(res, {
            txId,
            activityId,
            status: 'pending_verification',
            timestamp: new Date().toISOString()
        });
    } catch (error) {
        return errorResponse(res, error.message, 500);
    }
};

exports.verifyActivity = async (req, res) => {
    try {
        const { txId, activityId, auditorId } = req.body;
        const contract = await getContract();

        await contract.submitTransaction(
            'ActivityContract:VerifyActivity',
            activityId, auditorId
        );

        return successResponse(res, {
            txId: `VERIFY-${Date.now()}`,
            status: 'verified',
            verifiedAt: new Date().toISOString()
        });
    } catch (error) {
        return errorResponse(res, error.message, 500);
    }
};
```

### fabric-gateway-api/src/routes/activity.routes.js
```javascript
const express = require('express');
const router = express.Router();
const controller = require('../controllers/activity.controller');

router.post('/chaincode/registerActivity', controller.registerActivity);
router.post('/chaincode/verifyActivity', controller.verifyActivity);

module.exports = router;
```

### fabric-gateway-api/src/utils/response.js
```javascript
exports.successResponse = (res, data, statusCode = 200) => {
    return res.status(statusCode).json({ success: true, data });
};

exports.errorResponse = (res, message, statusCode = 500) => {
    return res.status(statusCode).json({ success: false, error: message });
};
```

### fabric-gateway-api/src/server.js
```javascript
const app = require('./app');
const { connectToFabric } = require('./services/fabric.service');

const PORT = process.env.PORT || 9000;

async function start() {
    try {
        await connectToFabric();
        app.listen(PORT, () => {
            console.log(`Fabric Gateway API running on port ${PORT}`);
        });
    } catch (err) {
        console.error('Failed to start:', err);
        process.exit(1);
    }
}

start();
```

### fabric-gateway-api/src/app.js
```javascript
const express = require('express');
const app = express();

app.use(express.json());

const activityRoutes = require('./routes/activity.routes');
const creditRoutes = require('./routes/credit.routes');
const auditRoutes = require('./routes/audit.routes');

app.use('/', activityRoutes);
app.use('/', creditRoutes);
app.use('/', auditRoutes);

app.get('/health', (req, res) => {
    res.json({ status: 'healthy', service: 'fabric-gateway-api' });
});

module.exports = app;
```

---

## Week 5: Deploy Chaincode

```bash
# 1. Start network
cd module2-blockchain
./scripts/start-network.sh

# 2. Create channel
./fabric-network/scripts/createChannel.sh

# 3. Package chaincode
cd chaincode/carbon-credit
go mod tidy
cd ../..
./fabric-network/scripts/deployCC.sh carbon-credit chaincode/carbon-credit go 1.0

# 4. Verify chaincode is running
docker ps | grep chaincode
```

---

## Week 6–8: CouchDB Indexes + Testing

### META-INF/statedb/couchdb/indexes/activityIndex.json
```json
{
    "index": {
        "fields": ["farmerId", "status", "submittedAt"]
    },
    "ddoc": "activityIndex",
    "name": "activityIndex",
    "type": "json"
}
```

### META-INF/statedb/couchdb/indexes/creditIndex.json
```json
{
    "index": {
        "fields": ["ownerId", "status", "mintedAt"]
    },
    "ddoc": "creditIndex",
    "name": "creditIndex",
    "type": "json"
}
```

### Test chaincode directly
```bash
# Invoke registerActivity
./scripts/invoke-chaincode.sh \
  '{"function":"ActivityContract:RegisterActivity","Args":["ACT-001","FARMER-001","no_till","3.2","10.78","78.81"]}'

# Query activity
./scripts/invoke-chaincode.sh \
  '{"function":"ActivityContract:QueryActivity","Args":["ACT-001"]}'
```

---

## Indhu's Testing Checklist

```bash
# Terminal 1: Start Fabric network
cd module2-blockchain && ./scripts/start-network.sh

# Terminal 2: Start Fabric Gateway API
cd fabric-gateway-api && npm start

# Test all 5 endpoints with curl:

# 1. Register Activity
curl -X POST http://localhost:9000/chaincode/registerActivity \
  -H "Content-Type: application/json" \
  -d '{"farmerId":"FARMER-001","activityType":"no_till","acres":3.2}'

# 2. Verify Activity
curl -X POST http://localhost:9000/chaincode/verifyActivity \
  -H "Content-Type: application/json" \
  -d '{"txId":"ECBH-2026-12345","activityId":"ACT-001","auditorId":"AUD-001"}'

# 3. Mint Credit
curl -X POST http://localhost:9000/chaincode/mintCredit \
  -H "Content-Type: application/json" \
  -d '{"activityId":"ACT-001","farmerId":"FARMER-001","creditAmount":2.56,"activityType":"no_till","acres":3.2}'

# 4. Transfer Credit
curl -X POST http://localhost:9000/chaincode/transferCredit \
  -H "Content-Type: application/json" \
  -d '{"creditId":"CREDIT-001","sellerId":"FARMER-001","buyerId":"IND-001","credits":1.5}'

# 5. Retire Credit
curl -X POST http://localhost:9000/chaincode/retireCredit \
  -H "Content-Type: application/json" \
  -d '{"creditId":"CREDIT-001","ownerId":"IND-001","amount":1.5,"reason":"BEE compliance FY2026"}'
```
