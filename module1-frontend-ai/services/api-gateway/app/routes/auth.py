from fastapi import APIRouter
from fastapi import HTTPException

from typing import Literal

from app.database import database

from app.schemas.auth import (
    UserLogin,
    UserRegister
)

from pydantic import BaseModel
from pydantic import EmailStr

from app.services.security import (
    hash_password,
    verify_password,
    create_access_token
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# allowed registration roles
AllowedRoles = Literal[
    "farmer",
    "industry",
    "auditor",
    "admin"
]

# register schema
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: AllowedRoles


# register new user
@router.post("/register")
async def register_user(
    user: UserRegister
):

    try:
        # check existing user
        existing_user = await database.users.find_one({
            "email": user.email
        })

        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="User already exists"
            )

        # create user data
        user_data = {
            "name": user.name,
            "email": user.email,
            "password": hash_password(
                user.password
            ),
            "role": user.role
        }

        # save user
        result = await database.users.insert_one(
            user_data
        )

        return {
            "success": True,
            "message": "User registered successfully",
            "data": {
                "userId": str(result.inserted_id)
            }
        }
    
    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# login user
@router.post("/login")
async def login_user(
    user: UserLogin
):

    try:

        # find user
        existing_user = await database.users.find_one({
            "email": user.email
        })

        # user not found
        if not existing_user:

            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        # verify password
        valid_password = verify_password(
            user.password,
            existing_user["password"]
        )

        # invalid password
        if not valid_password:

            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        # token payload
        token_data = {

            "userId": str(existing_user["_id"]),

            "email": existing_user["email"],

            "role": existing_user["role"]
        }

        # generate jwt token
        access_token = create_access_token(
            token_data
        )

        return {
            "success": True,
            "message": "Login successful",
            "data": {
                "access_token": access_token,
                "token_type": "bearer",
                "role": existing_user["role"]
            }
        }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )