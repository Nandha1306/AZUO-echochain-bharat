from pydantic import BaseModel
from typing import Optional

class Location(BaseModel):
    lat: float
    lng: float

class ActivityCreate(BaseModel):
    farmerId: str
    activityType: str
    acres: float
    location: Optional[Location] = None