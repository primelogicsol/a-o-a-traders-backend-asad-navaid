from pydantic import BaseModel

class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user_role:str
    user_id:int


class GoogleUser(BaseModel):
    sub: int
    email: str
    name: str
    picture: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class GoogleLoginResponse(BaseModel):
    access_token: str
    token_type: str

class CreateUserRequest(BaseModel):
    username: str
    password: str

