from fastapi import APIRouter
from app.schemas.activity import ActivityCreate
from app.database import database
import traceback

router = APIRouter()

@router.post("/activities")
async def create_activity(activity: ActivityCreate):

    try:

        activity_data = activity.model_dump()

        print("Incoming Activity:")
        print(activity_data)

        result = await database.activities.insert_one(activity_data)

        print("Inserted Successfully")

        if "_id" in activity_data:
            activity_data["_id"] = str(activity_data["_id"])

        return {
            "message": "Activity submitted successfully",
            "activityId": str(result.inserted_id),
            "data": activity_data
        }

    except Exception as e:

        print("ERROR OCCURRED:")
        traceback.print_exc()

        return {
            "error": str(e)
        }