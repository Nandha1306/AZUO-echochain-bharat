from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# farmer location
class Location(BaseModel):
    lat: float
    lng: float


# verification details
class Verification(BaseModel):
    verified: bool = False
    verifiedBy: Optional[str] = None
    verifiedAt: Optional[str] = None


# carbon credit details
class Credits(BaseModel):
    minted: bool = False
    amount: float = 0


# create activity request
class ActivityCreate(BaseModel):
    farmerId: str
    activityType: str
    acres: float
    location: Optional[Location] = None


# activity response structure
class ActivityResponse(ActivityCreate):
    txId: str
    status: str
    submittedAt: str
    verification: Verification
    credits: Credits