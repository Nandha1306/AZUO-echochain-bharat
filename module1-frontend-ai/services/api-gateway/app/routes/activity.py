from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from datetime import datetime

from bson import ObjectId

from app.database import database

from app.schemas.activity import (
    ActivityCreate,
    Verification,
    Credits
)

from app.services.blockchain_service import (
    register_activity_on_blockchain,
    verify_activity_on_blockchain,
    mint_credit_on_blockchain
)

from app.services.auth_dependency import (
    farmer_only,
    auditor_only,
    admin_only,
    get_current_user
)

from app.utils.objectid import (
    validate_object_id
)

from typing import Optional
from fastapi import Query

import traceback

router = APIRouter(
    prefix="/activities",
    tags=["Activities"]
)

# activity based carbon credit rates
CREDIT_RATES = {
    "no_till": 0.8,
    "agroforestry": 1.2,
    "organic_farming": 0.9,
    "soil_carbon": 1.0,
    "efficient_irrigation": 0.5
}

# create a new farmer activity
@router.post("")
async def create_activity(
    activity: ActivityCreate,
    user=Depends(farmer_only)
):

    try:
        activity_data = activity.model_dump()

        # register activity on blockchain
        blockchain_response = await register_activity_on_blockchain(
            activity_data
        )

        # add blockchain details
        activity_data["txId"] = blockchain_response["txId"]
        activity_data["status"] = blockchain_response["status"]

        # add timestamp
        activity_data["submittedAt"] = (
            datetime.utcnow().isoformat()
        )

        # add verification details
        activity_data["verification"] = (
            Verification().model_dump()
        )

        # add credit details
        activity_data["credits"] = (
            Credits().model_dump()
        )

        # save to mongodb
        result = await database.activities.insert_one(
            activity_data
        )

        return {
            "success": True,
            "message": "Activity submitted successfully",
            "data": {
                "activityId": str(result.inserted_id),
                "txId": activity_data["txId"],
                "status": activity_data["status"]
            }
        }

    except Exception as e:
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# get all activities
@router.get("")
async def get_all_activities(
    user=Depends(get_current_user),
    status: Optional[str] = Query(None)
):

    try:
        activities = []

        query = {}

        if status:
            query["status"] = status

        cursor = database.activities.find(query)

        async for activity in cursor:
            activity["_id"] = str(activity["_id"])
            activities.append(activity)

        return {
            "success": True,
            "data": activities
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
    
# get pending activities for auditors
@router.get("/pending")
async def get_pending_activities(
    user=Depends(auditor_only)
):

    try:
        activities = []

        cursor = database.activities.find({
            "status": "pending"
        })

        async for activity in cursor:
            activity["_id"] = str(
                activity["_id"]
            )
            activities.append(activity)

        return {
            "success": True,
            "data": activities
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# get activity by id
@router.get("/{activity_id}")
async def get_activity(
    activity_id: str,
    user=Depends(get_current_user)
):

    try:
        activity = await database.activities.find_one({
            "_id": validate_object_id(activity_id)
        })

        if not activity:
            raise HTTPException(
                status_code=404,
                detail="Activity not found"
            )

        activity["_id"] = str(activity["_id"])

        return {
            "success": True,
            "data": activity
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# get activities by farmer id
@router.get("/farmer/{farmer_id}")
async def get_farmer_activities(
    farmer_id: str,
    user=Depends(get_current_user)
):

    try:
        activities = []

        cursor = database.activities.find({
            "farmerId": farmer_id
        })

        async for activity in cursor:
            activity["_id"] = str(activity["_id"])
            activities.append(activity)

        return {
            "success": True,
            "data": activities
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# verify farmer activity
@router.post("/{activity_id}/verify")
async def verify_activity(
    activity_id: str,
    user=Depends(auditor_only)
):

    try:
        activity = await database.activities.find_one({
            "_id": validate_object_id(activity_id)
        })

        if not activity:
            raise HTTPException(
                status_code=404,
                detail="Activity not found"
            )

        if activity["status"] != "pending":
            raise HTTPException(
                status_code=400,
                detail="Activity already processed"
            )

        activity["_id"] = str(activity["_id"])

        blockchain_response = (
            await verify_activity_on_blockchain(activity)
        )

        update_data = {
            "status": "verified",
            "verification.verified": True,
            "verification.verifiedBy": user["userId"],
            "verification.verifiedAt":
                blockchain_response["verifiedAt"]
        }

        await database.activities.update_one(
            {"_id": validate_object_id(activity_id)},
            {"$set": update_data}
        )

        return {
            "success": True,
            "message": "Activity verified successfully",
            "data": {
                "activityId": activity_id,
                "status": "verified"
            }
        }

    except HTTPException:
        raise

    except Exception as e:
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# reject farmer activity
@router.post("/{activity_id}/reject")
async def reject_activity(
    activity_id: str,
    user=Depends(auditor_only)
):
    try:
        activity = await database.activities.find_one({
            "_id": validate_object_id(activity_id)
        })

        # activity not found
        if not activity:
            raise HTTPException(
                status_code=404,
                detail="Activity not found"
            )

        # allow rejection only for pending activities
        if activity["status"] != "pending":
            raise HTTPException(
                status_code=400,
                detail="Activity already processed"
            )

        # update rejection details
        update_data = {
            "status": "rejected",
            "verification.verified": False,
            "verification.verifiedBy":
                user["userId"],
            "verification.verifiedAt":
                datetime.utcnow().isoformat()
        }

        # update activity
        await database.activities.update_one(
            {
                "_id": validate_object_id(activity_id)
            },
            {
                "$set": update_data
            }
        )

        return {
            "success": True,
            "message":
                "Activity rejected successfully",
            "data": {
                "activityId": activity_id,
                "status": "rejected"
            }
        }

    except HTTPException:
        raise

    except Exception as e:
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# mint carbon credits
@router.post("/{activity_id}/mint")
async def mint_credits(
    activity_id: str,
    user=Depends(admin_only)
):

    try:
        activity = await database.activities.find_one({
            "_id": validate_object_id(activity_id)
        })

        if not activity:
            raise HTTPException(
                status_code=404,
                detail="Activity not found"
            )

        if activity["status"] != "verified":

            raise HTTPException(
                status_code=400,
                detail="Activity must be verified before minting"
            )

        activity["_id"] = str(activity["_id"])

        blockchain_response = (
            await mint_credit_on_blockchain(activity)
        )

        # activity-based credit calculation
        rate = CREDIT_RATES.get(
            activity["activityType"],
            0.8
        )

        credit_amount = round(
            activity["acres"] * rate,
            2
        )

        update_data = {
            "status": "credits_minted",
            "credits.minted": True,
            "credits.amount": credit_amount
        }

        await database.activities.update_one(
            {"_id": validate_object_id(activity_id)},
            {"$set": update_data}
        )

        # check farmer wallet
        wallet = await database.wallets.find_one({
            "ownerId": activity["farmerId"]
        })

        # create wallet if not exists
        if not wallet:
            wallet_data = {
                "ownerId": activity["farmerId"],
                "ownerType": "farmer",
                "totalCredits": credit_amount,
                "availableCredits": credit_amount,
                "soldCredits": 0
            }

            await database.wallets.insert_one(
                wallet_data
            )

        # update existing wallet
        else:
            await database.wallets.update_one(
                {
                    "ownerId": activity["farmerId"]
                },
                {
                    "$inc": {
                        "totalCredits": credit_amount,
                        "availableCredits": credit_amount
                    }
                }
            )

        return {
            "success": True,
            "message": "Carbon credits minted successfully",
            "data": {
                "activityId": activity_id,
                "credits": credit_amount,
                "status": "credits_minted",
                "mintedAt":
                    blockchain_response["mintedAt"]
            }
        }

    except HTTPException:
        raise

    except Exception as e:
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )