"""Application configuration management using environment variables."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

from pydantic import Field, ValidationError, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class SettingsError(RuntimeError):
    """Raised when the application settings could not be loaded."""


class Settings(BaseSettings):
    """Application settings loaded from environment variables or an .env file."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    mongodb_uri: str = Field(..., alias="MONGODB_URI", description="MongoDB connection string")
    mongodb_db: str = Field("BeatNow", alias="MONGODB_DB", description="MongoDB database name")

    jwt_secret_key: str = Field(..., alias="JWT_SECRET_KEY", description="Secret key for JWT tokens")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM", description="JWT signing algorithm")
    access_token_expire_minutes: int = Field(
        8000,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
        description="Minutes before access tokens expire",
    )

    ssh_host: str = Field(..., alias="SSH_HOST", description="SSH host for file management")
    ssh_username: str = Field(..., alias="SSH_USERNAME", description="SSH username")
    ssh_password: str | None = Field(None, alias="SSH_PASSWORD", description="SSH password")
    ssh_private_key_path: str | None = Field(
        None,
        alias="SSH_PRIVATE_KEY_PATH",
        description="Path to SSH private key file",
    )

    email_sender: str | None = Field(None, alias="EMAIL_SENDER", description="Email sender address")
    email_password: str | None = Field(None, alias="EMAIL_PASSWORD", description="Email sender password or app key")

    prometheus_port: int = Field(8000, alias="PROMETHEUS_PORT", description="Port for Prometheus metrics server")
    app_host: str = Field("0.0.0.0", alias="APP_HOST", description="Host for FastAPI application")
    app_port: int = Field(8001, alias="APP_PORT", description="Port for FastAPI application")

    @model_validator(mode="after")
    def _validate_ssh_credentials(self) -> "Settings":
        if not self.ssh_password and not self.ssh_private_key_path:
            raise ValueError("Either SSH_PASSWORD or SSH_PRIVATE_KEY_PATH must be provided.")
        if self.ssh_private_key_path:
            key_path = Path(self.ssh_private_key_path)
            if not key_path.expanduser().exists():
                raise ValueError(f"SSH private key not found at {key_path}.")
        return self

    def ssh_connection_kwargs(self) -> Dict[str, Any]:
        """Return authentication arguments for Paramiko based on available credentials."""
        if self.ssh_password:
            return {"password": self.ssh_password}
        if self.ssh_private_key_path:
            return {"key_filename": str(Path(self.ssh_private_key_path).expanduser())}
        raise SettingsError("SSH credentials are not configured correctly.")


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings, raising :class:`SettingsError` on failure."""
    try:
        return Settings()
    except ValidationError as exc:
        raise SettingsError("Invalid application configuration") from exc


__all__ = ["Settings", "SettingsError", "get_settings"]