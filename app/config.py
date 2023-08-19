from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings, SettingsConfigDict


# class Settings(BaseSettings):
#     DATABASE_URL:str
#     app_name: str = "Awesome API"
#     admin_email: str
#     items_per_user: int = 50
#
#     model_config = SettingsConfigDict(env_file=".env")


def setup_cors(app):
    origins = ["*"]  # Allows all origins; you may want to change this in production

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
