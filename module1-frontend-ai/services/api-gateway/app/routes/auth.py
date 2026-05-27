from fastapi import APIRouter
from app.database import database

from app.schemas.auth import (
    UserRegister,
    UserLogin
)

from app.services.security import (
    hash_password,
    verify_password,
    create_access_token
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

# register new user
@router.post("/auth/register")
async def register_user(user: UserRegister):
    # check existing user
    existing_user = await database.users.find_one({
        "email": user.email
    })

    if existing_user:
        return {
            "message": "User already exists"
        }

    # create user data
    user_data = {
        "name": user.name,
        "email": user.email,
        "password": hash_password(user.password),
        "role": user.role
    }

    # save user
    result = await database.users.insert_one(user_data)

    return {
        "message": "User registered successfully",
        "userId": str(result.inserted_id)
    }


# login user
@router.post("/auth/login")
async def login_user(user: UserLogin):
    # find user
    existing_user = await database.users.find_one({
        "email": user.email
    })

    # check user exists
    if not existing_user:
        return {
            "message": "Invalid email or password"
        }

    # verify password
    valid_password = verify_password(
        user.password,
        existing_user["password"]
    )

    if not valid_password:
        return {
            "message": "Invalid email or password"
        }

    # create token data
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
        "access_token": access_token,
        "token_type": "bearer",
        "role": existing_user["role"]
    }