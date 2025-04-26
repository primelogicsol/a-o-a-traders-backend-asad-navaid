from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.services.jwt import create_access_token
from app.core.config import settings
from datetime import timedelta

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_FROM_NAME="AOATraders",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True
)

async def send_magic_link(user):
    expires_delta = timedelta(minutes=15)

    username = user.email
    user_id = user.id
    role = user.role.value if hasattr(user.role, "value") else user.role

    token = create_access_token(
        username=username,
        user_id=user_id,
        role=role,
        expires_delta=expires_delta
    )

    link = f"{settings.FRONTEND_URL}/magic-login?token={token}"

    message = MessageSchema(
        subject="Your AOATraders Magic Login Link",
        recipients=[user.email],
        body=f"Click to login: <a href='{link}'>{link}</a>",
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)
