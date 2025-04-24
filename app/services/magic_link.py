from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from .jwt import create_access_token
from app.core.config import settings

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
    token = create_access_token({"sub": str(user.id), "role": user.role})
    link = f"{settings.FRONTEND_URL}/magic-login?token={token}"
    message = MessageSchema(
        subject="Your AOATraders Magic Login Link",
        recipients=[user.email],
        body=f"Click to login: {link}",
        subtype="html"
    )
    fm = FastMail(conf)
    await fm.send_message(message)