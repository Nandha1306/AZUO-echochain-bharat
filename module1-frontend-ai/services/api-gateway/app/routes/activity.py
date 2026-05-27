from fastapi import APIRouter
from app.schemas.activity import (
    ActivityCreate,
    Verification,
    Credits
)

from app.database import database
from app.services.blockchain_service import (
    register_activity_on_blockchain,
    verify_activity_on_blockchain,
    mint_credit_on_blockchain
)

from fastapi import Depends

from app.services.auth_dependency import (
    farmer_only,
    auditor_only,
    admin_only
)

from datetime import datetime
from bson import ObjectId
import traceback

router = APIRouter(
    prefix="/activities",
    tags=["Activities"]
)

# create a new farmer activity
@router.post("/activities")
async def create_activity(
    activity: ActivityCreate,
    user=Depends(farmer_only)
):

    try:

        activity_data = activity.model_dump()

        # register activity on blockchain
        blockchain_response = await register_activity_on_blockchain(activity_data)

        # add blockchain details
        activity_data["txId"] = blockchain_response["txId"]
        activity_data["status"] = blockchain_response["status"]

        # add timestamp
        activity_data["submittedAt"] = datetime.utcnow().isoformat()

        # add verification details
        activity_data["verification"] = Verification().model_dump()

        # add credit details
        activity_data["credits"] = Credits().model_dump()

        # save to mongodb
        result = await database.activities.insert_one(activity_data)

        return {
            "message": "Activity submitted successfully",
            "activityId": str(result.inserted_id),
            "txId": activity_data["txId"],
            "status": activity_data["status"],
            "submittedAt": activity_data["submittedAt"]
        }

    except Exception as e:

        print("ERROR OCCURRED:")
        traceback.print_exc()

        return {
            "error": str(e)
        }


# get all activities
@router.get("/activities")
async def get_all_activities():

    activities = []

    cursor = database.activities.find()

    async for activity in cursor:

        activity["_id"] = str(activity["_id"])

        activities.append(activity)

    return activities


# get activity by id
@router.get("/activities/{activity_id}")
async def get_activity(activity_id: str):

    activity = await database.activities.find_one({
        "_id": ObjectId(activity_id)
    })

    if not activity:

        return {
            "message": "Activity not found"
        }

    activity["_id"] = str(activity["_id"])

    return activity


# get activities by farmer id
@router.get("/activities/farmer/{farmer_id}")
async def get_farmer_activities(farmer_id: str):

    activities = []

    cursor = database.activities.find({
        "farmerId": farmer_id
    })

    async for activity in cursor:

        activity["_id"] = str(activity["_id"])

        activities.append(activity)

    return activities

# verify farmer activity
@router.post("/activities/{activity_id}/verify")
async def verify_activity(
    activity_id: str,
    user=Depends(auditor_only)
):

    try:

        # get activity from mongodb
        activity = await database.activities.find_one({
            "_id": ObjectId(activity_id)
        })

        # check activity exists
        if not activity:

            return {
                "message": "Activity not found"
            }

        # remove mongodb object id
        activity["_id"] = str(activity["_id"])  

        # verify on blockchain
        blockchain_response = await verify_activity_on_blockchain(activity)

        # update verification details
        update_data = {

            "status": "verified",

            "verification.verified": True,

            "verification.verifiedBy": "AUDITOR-001",

            "verification.verifiedAt":
                blockchain_response["verifiedAt"]
        }

        # update mongodb
        await database.activities.update_one(
            {"_id": ObjectId(activity_id)},
            {"$set": update_data}
        )

        return {
            "message": "Activity verified successfully",
            "activityId": activity_id,
            "status": "verified",
            "verifiedAt": blockchain_response["verifiedAt"]
        }

    except Exception as e:

        print("ERROR OCCURRED:")
        traceback.print_exc()

        return {
            "error": str(e)
        }
    
    # reject farmer activity
@router.post("/activities/{activity_id}/reject")
async def reject_activity(activity_id: str):
    try:
        # check activity exists
        activity = await database.activities.find_one({
            "_id": ObjectId(activity_id)
        })

        if not activity:

            return {
                "message": "Activity not found"
            }

        # update rejection details
        update_data = {
            "status": "rejected",
            "verification.verified": False,
            "verification.verifiedBy": "AUDITOR-001",
            "verification.verifiedAt":
            datetime.utcnow().isoformat()
        }

        # update mongodb
        await database.activities.update_one(
            {"_id": ObjectId(activity_id)},
            {"$set": update_data}
        )

        return {
            "message": "Activity rejected successfully",
            "activityId": activity_id,
            "status": "rejected"
        }

    except Exception as e:
        print("ERROR OCCURRED:")
        traceback.print_exc()

        return {
            "error": str(e)
        }
    
# mint carbon credits
@router.post("/activities/{activity_id}/mint")
async def mint_credits(
    activity_id: str,
    user=Depends(admin_only)
):
    
    try:
        # get activity from mongodb
        activity = await database.activities.find_one({
            "_id": ObjectId(activity_id)
        })

        # check activity exists
        if not activity:
            return {
                "message": "Activity not found"
            }

        # allow only verified activities
        if activity["status"] != "verified":
            return {
                "message": "Activity must be verified before minting"
            }

        # remove mongodb object id
        activity["_id"] = str(activity["_id"])

        # mint credits on blockchain
        blockchain_response = await mint_credit_on_blockchain(activity)

        # simple carbon credit calculation
        credit_amount = round(activity["acres"] * 0.8, 2)

        # update credit details
        update_data = {
            "status": "credits_minted",
            "credits.minted": True,
            "credits.amount": credit_amount
        }

        # update activity in mongodb
        await database.activities.update_one(
            {"_id": ObjectId(activity_id)},
            {"$set": update_data}
        )

        # check farmer wallet exists
        wallet = await database.wallets.find_one({
            "farmerId": activity["farmerId"]
        })

        # create wallet if not exists
        if not wallet:
            wallet_data = {
                "farmerId": activity["farmerId"],
                "totalCredits": credit_amount,
                "availableCredits": credit_amount,
                "soldCredits": 0
            }
            await database.wallets.insert_one(wallet_data)

        # update existing wallet
        else:
            await database.wallets.update_one(
                {
                    "farmerId": activity["farmerId"]
                },
                {
                    "$inc": {
                        "totalCredits": credit_amount,
                        "availableCredits": credit_amount
                    }
                }
            )
        return {
            "message": "Carbon credits minted successfully",
            "activityId": activity_id,
            "credits": credit_amount,
            "status": "credits_minted",
            "mintedAt": blockchain_response["mintedAt"]
        }

    except Exception as e:

        print("ERROR OCCURRED:")
        traceback.print_exc()

        return {
            "error": str(e)
        }