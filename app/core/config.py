from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str
    JWT_SECRET_KEY: str 
    MAIL_USERNAME: str = "asadnavaid34@gmail.com"
    MAIL_PASSWORD: str = "eeoc eirw ncru amhu"
    MAIL_FROM: str = "asadnavaid34@gmail.com"
    FRONTEND_URL: str = "http://localhost:3000"
    DATABASE_URL: str

    class Config:
        env_file = ".env"


settings = Settings()