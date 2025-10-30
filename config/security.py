from typing import Annotated, Optional
import logging
from datetime import datetime, timedelta
import jwt
from bson import ObjectId
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt import PyJWTError
from passlib.context import CryptContext
from prometheus_client import Counter
from config.db import lyrics_collection, post_collection, users_collection
from config.settings import SettingsError, get_settings
from model.lyrics_shemas import Lyrics
from model.user_shemas import NewUser


try:
    settings = get_settings()
except SettingsError as exc:
    raise RuntimeError("Failed to load security configuration") from exc

SSH_USERNAME_RES = settings.ssh_username
SSH_PASSWORD_RES = settings.ssh_password
SSH_HOST_RES = settings.ssh_host
SSH_PRIVATE_KEY_PATH_RES = settings.ssh_private_key_path

SECRET_KEY = settings.jwt_secret_key
ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

# Configuración de la seguridad y autenticación OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
 
# Configuración de logs
logging.basicConfig(filename='app.log', level=logging.INFO)
 
# Configuración de Prometheus
requests_counter = Counter('requests_total', 'Total number of requests')

def get_ssh_connection_kwargs() -> dict:
    """Return keyword arguments for Paramiko SSH connections."""
    return settings.ssh_connection_kwargs()

async def get_user(username: str) -> Optional[NewUser]:
    try:
        user = await users_collection.find_one({"username": username})
        if user:
            return NewUser(**user)
    except Exception as exc:  # pragma: no cover - passthrough for database errors
        raise HTTPException(status_code=500, detail="Database error") from exc

async def decode_token(token: str) -> Optional[NewUser]:
    try:
        # Decodifica el token y valida
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await get_user(username)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except PyJWTError:
        raise HTTPException(status_code=403, detail="Could not validate credentials")


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    user = await decode_token(token)  # Ensure this is awaited
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    return user

async def get_current_user_without_confirmation(token: Annotated[str, Depends(oauth2_scheme)]):
    user = await decode_token(token)  # Ensure this is awaited
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_user_id(username: str):
    user = await users_collection.find_one({"username": username})
    if user:
        return str(user["_id"])
    else:
        return "Usuario no encontrado" 
async def get_post_id_saved(_id: str):
    lyric = await post_collection.find_one({"_id": ObjectId(_id)})
    if lyric:
        return str(lyric["user_id"])
    else:
        return "Lyric no encontrado" 

async def get_lyric_id(lyric: Lyrics):
    lyric = await lyrics_collection.find_one({lyric.dict()})
    if lyric:
        return str(user["_id"])
    else:
        return "Lyric no encontrado" 
    
async def get_username(user_id: str):
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if user:
        return user["username"]
    else:
        return "Usuario no encontrado"

async def check_post_exists(post_id: str, db):
    existing_post = await post_collection.find_one({"_id": ObjectId(post_id)})
    if not existing_post:
        raise HTTPException(status_code=404, detail="Post not found")

 
def guardar_log(evento):
    now = datetime.now()
    logging.info(f'{now} - {evento}')

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)  # Duración por defecto de 15 minutos
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt