from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta

from app.config import (
    SECRET_KEY,
    ALGORITHM
)

# password hashing setup
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

# token expiry
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# hash password
def hash_password(password: str):
    return pwd_context.hash(password)

# verify password
def verify_password(
    plain_password,
    hashed_password
):
    return pwd_context.verify(
        plain_password,
        hashed_password
    )


# create jwt token
def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.utcnow() + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({
        "exp": expire
    })

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt