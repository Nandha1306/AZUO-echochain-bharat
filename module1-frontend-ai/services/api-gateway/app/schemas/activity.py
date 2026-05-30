from pydantic import BaseModel
from pydantic import field_validator

from typing import Optional
from typing import Literal

# allowed activity types
ActivityType = Literal[
    "no_till",
    "agroforestry",
    "organic_farming",
    "soil_carbon",
    "efficient_irrigation"
]

# farmer location
class Location(BaseModel):
    lat: float
    lng: float

    # validate latitude
    @field_validator("lat")
    @classmethod
    def validate_latitude(cls, value):
        if value < -90 or value > 90:
            raise ValueError(
                "Latitude must be between -90 and 90"
            )
        return value

    # validate longitude
    @field_validator("lng")
    @classmethod
    def validate_longitude(cls, value):
        if value < -180 or value > 180:
            raise ValueError(
                "Longitude must be between -180 and 180"
            )

        return value


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
    activityType: ActivityType
    acres: float
    location: Optional[Location] = None

    # validate farmer id
    @field_validator("farmerId")
    @classmethod
    def validate_farmer_id(cls, value):
        if not value.strip():
            raise ValueError(
                "Farmer ID cannot be empty"
            )

        return value


    # validate acres
    @field_validator("acres")
    @classmethod
    def validate_acres(cls, value):
        if value <= 0:
            raise ValueError(
                "Acres must be greater than 0"
            )

        return value


# activity response structure
class ActivityResponse(ActivityCreate):
    txId: str
    status: str
    submittedAt: str
    verification: Verification
    credits: Credits