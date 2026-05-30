from bson import ObjectId
from fastapi import HTTPException

def validate_object_id(id: str):

    if not ObjectId.is_valid(id):
        raise HTTPException(
            status_code=400,
            detail="Invalid object id"
        )

    return ObjectId(id)