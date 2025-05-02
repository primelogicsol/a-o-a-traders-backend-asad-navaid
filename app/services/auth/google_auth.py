from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from sqlalchemy.ext.asyncio import AsyncSession
import os

from app.schemas.auth.validators import GoogleUser
from app.models.user import User

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

oauth = OAuth()


# if GOOGLE_CLIENT_ID is None or GOOGLE_CLIENT_SECRET is None:
#     raise Exception('Missing env variables')

# config_data = {'GOOGLE_CLIENT_ID': GOOGLE_CLIENT_ID, 'GOOGLE_CLIENT_SECRET': GOOGLE_CLIENT_SECRET}
# starlette_config = Config(environ=config_data)

# oauth = OAuth(starlette_config)

oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    access_token_url='https://oauth2.googleapis.com/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/v2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://openidconnect.googleapis.com/v1/userinfo',
    client_kwargs={
        'scope': 'openid email profile',
    },
)


async def get_user_by_google_sub(google_sub: int, db: AsyncSession):
    return await db.query(User).filter(User.google_sub == str(google_sub)).first()


async def create_user_from_google_info(google_user: GoogleUser, db: AsyncSession):
    google_sub = google_user.sub
    email = google_user.email
    existing_user = await db.query(User).filter(User.email == email).first()
    if existing_user:
        existing_user.google_id = google_sub
        db.commit()
        return existing_user
    else:
        new_user = User(
            username=email,
            email=email,
            google_sub=google_sub,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
