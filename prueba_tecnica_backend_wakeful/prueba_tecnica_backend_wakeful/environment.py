from enum import Enum

from dotenv import load_dotenv
from pydantic import BaseSettings, Field

load_dotenv()


class Environments(Enum):
    LOCAL = "LOCAL"
    DEV = "DEV"
    PROD = "PROD"


class EnvVars(BaseSettings):
    ENV: Environments
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    ALLOWED_HOSTS: str | list[str] = Field(..., env="ALLOWED_HOSTS")
    # DB
    NAME: str = Field(..., env="NAME")
    POSTGRES_USER: str = Field(..., env="POSTGRES_USER")
    POSTGRES_PASSWORD: str = Field(..., env="POSTGRES_PASSWORD")
    HOST: str = Field(..., env="HOST")
    PORT: int = Field(default=5432, env="PORT")
    EMAIL_HOST: str = Field(..., env="EMAIL_HOST")
    EMAIL_PORT: str = Field(..., env="EMAIL_PORT")
    EMAIL_HOST_USER: str = Field(..., env="EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD: str = Field(..., env="EMAIL_HOST_PASSWORD")
    CSRF_TRUSTED_ORIGINS: str | list[str] = Field(..., env="CSRF_TRUSTED_ORIGINS")

    class Config:
        env_prefix = ""
        case_sentive = False
        env_file = ".env.sample", ".env"
        env_file_encoding = "utf-8"


env_vars = EnvVars()
