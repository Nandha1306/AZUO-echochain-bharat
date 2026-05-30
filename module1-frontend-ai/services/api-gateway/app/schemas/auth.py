from pydantic import BaseModel
from pydantic import EmailStr
from pydantic import field_validator

from typing import Literal

import re

AllowedRoles = Literal[
    "farmer",
    "industry",
    "auditor"
    "admin"
]

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: AllowedRoles

    @field_validator("password")
    @classmethod
    def validate_password(cls, value):

        if len(value) < 8:
            raise ValueError(
                "Password must be at least 8 characters"
            )

        if not re.search(r"[A-Z]", value):
            raise ValueError(
                "Password must contain uppercase letter"
            )

        if not re.search(r"[0-9]", value):
            raise ValueError(
                "Password must contain number"
            )

        return value

class UserLogin(BaseModel):
    email: EmailStr
    password: str