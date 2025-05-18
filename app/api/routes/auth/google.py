from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from app.services.auth.google_auth import oauth, get_user_by_google_sub, create_user_from_google_info
from app.schemas.auth.validators import GoogleUser
from app.services.auth.jwt import create_access_token, create_refresh_token
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from authlib.oauth2.rfc6749 import OAuth2Token
from authlib.integrations.base_client.errors import OAuthError
import os
from datetime import timedelta

router = APIRouter()

GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
FRONTEND_URL = os.getenv("FRONTEND_URL")

@router.get("/google")
async def login_google(request: Request):
    return await oauth.google.authorize_redirect(request, GOOGLE_REDIRECT_URI)

from authlib.integrations.base_client.errors import OAuthError
import traceback

@router.get("/callback/google")
async def auth_google(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        token: OAuth2Token = await oauth.google.authorize_access_token(request)
        print("Token:", token)
        user_info = await oauth.google.parse_id_token(request, token)
        print("User Info:", user_info)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=401, detail="Could not validate credentials")

    google_user = GoogleUser(**user_info)
    existing_user = await get_user_by_google_sub(google_user.sub, db)

    if existing_user:
        user = existing_user
    else:
        user = await create_user_from_google_info(google_user, db)

    access_token = create_access_token(user.username, user.id, timedelta(days=7))
    refresh_token = create_refresh_token(user.username, user.id, timedelta(days=14))

    return RedirectResponse(f"{FRONTEND_URL}/auth?access_token={access_token}&refresh_token={refresh_token}")
