from fastapi import APIRouter
from app.schemas.activity import (
    ActivityCreate,
    Verification,
    Credits
)

from app.database import database
from app.services.blockchain_service import register_activity_on_blockchain

from datetime import datetime
from bson import ObjectId
import traceback

router = APIRouter()


# create a new farmer activity
@router.post("/activities")
async def create_activity(activity: ActivityCreate):

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