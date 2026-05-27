from fastapi import Depends
from fastapi import HTTPException

from fastapi.security import HTTPBearer
from fastapi.security import HTTPAuthorizationCredentials

from jose import jwt, JWTError

from app.services.security import (
    SECRET_KEY,
    ALGORITHM
)

# token reader
security = HTTPBearer()

# get current logged user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    try:
        token = credentials.credentials

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        return payload

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )


# allow only farmer
async def farmer_only(
    user=Depends(get_current_user)
):

    if user["role"] != "farmer":

        raise HTTPException(
            status_code=403,
            detail="Farmer access only"
        )

    return user


# allow only auditor
async def auditor_only(
    user=Depends(get_current_user)
):

    if user["role"] != "auditor":

        raise HTTPException(
            status_code=403,
            detail="Auditor access only"
        )

    return user


# allow only admin
async def admin_only(
    user=Depends(get_current_user)
):

    if user["role"] != "admin":

        raise HTTPException(
            status_code=403,
            detail="Admin access only"
        )

    return user


# allow only industry
async def industry_only(
    user=Depends(get_current_user)
):

    if user["role"] != "industry":

        raise HTTPException(
            status_code=403,
            detail="Industry access only"
        )

    return user 