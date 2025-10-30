from typing import List, Optional

from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.database import Database
from pymongo.errors import PyMongoError


from config.settings import SettingsError, get_settings

try:
    settings = get_settings()
except SettingsError as exc:
    raise RuntimeError("Failed to load database configuration") from exc

try:
    mongo_client = AsyncIOMotorClient(settings.mongodb_uri)
except Exception as exc:  # pragma: no cover - Motor raises on invalid URI at runtime
    raise RuntimeError("Unable to create MongoDB client") from exc


def get_database() -> Database:
    return mongo_client[settings.mongodb_db]

def _get_collection(name: str):
    return get_database()[name]


db = get_database()

users_collection = _get_collection("Users")
post_collection = _get_collection("Posts")
interactions_collection = _get_collection("Interactions")
lyrics_collection = _get_collection("Lyrics")
follows_collection = _get_collection("Follows")
genres_collection = _get_collection("Genres")
moods_collection = _get_collection("Moods")
instruments_collection = _get_collection("Instruments")
mail_code_collection = _get_collection("MailCode")
password_reset_collection = _get_collection("PasswordReset")

async def handle_database_error(exception: PyMongoError):
    raise HTTPException(status_code=500, detail="Database error")

def parse_list(value: Optional[str]) -> Optional[List[str]]:
    if value:
        return value.split(",")
    return None