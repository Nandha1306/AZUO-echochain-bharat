from pydantic import BaseModel, EmailStr


# register request
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str


# login request
class UserLogin(BaseModel):
    email: EmailStr
    password: str