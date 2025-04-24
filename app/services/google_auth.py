from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from sqlalchemy.ext.asyncio import AsyncSession
import os

from app.schemas.validators import GoogleUser
from app.models.user import User

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID') or None
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET') or None

if GOOGLE_CLIENT_ID is None or GOOGLE_CLIENT_SECRET is None:
    raise Exception('Missing env variables')

config_data = {'GOOGLE_CLIENT_ID': GOOGLE_CLIENT_ID, 'GOOGLE_CLIENT_SECRET': GOOGLE_CLIENT_SECRET}
starlette_config = Config(environ=config_data)

oauth = OAuth(starlette_config)

oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
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
