from config.db import get_database, genres_collection, users_collection, moods_collection, instruments_collection
from config.security import get_current_user
from fastapi import APIRouter, Depends, HTTPException

from model.user_shemas import User


# Iniciar router
router = APIRouter()

@router.get("/genres")
async def list_genres(current_user: User = Depends(get_current_user), db=Depends(get_database)):
    # Verificar si el usuario solicitado existe
    user_exists = await users_collection.find_one({"username": current_user.username})
    if not user_exists:
        raise HTTPException(status_code=404, detail="User not found")

    genres = genres_collection.find()  # Get all genres
    results = []
    async for document in genres:  # Asynchronous iteration
        results.append({"name": document["name"]})

    return results

@router.get("/moods")
async def list_moods(current_user: User = Depends(get_current_user), db=Depends(get_database)):
    # Verificar si el usuario solicitado existe
    user_exists = await users_collection.find_one({"username": current_user.username})
    if not user_exists:
        raise HTTPException(status_code=404, detail="User not found")

    genres = moods_collection.find()  # Get all genres
    results = []
    async for document in genres:  # Asynchronous iteration
        results.append({"name": document["name"]})

    return results

@router.get("/instruments")
async def list_instruments(current_user: User = Depends(get_current_user), db=Depends(get_database)):
    # Verificar si el usuario solicitado existe
    user_exists = await users_collection.find_one({"username": current_user.username})
    if not user_exists:
        raise HTTPException(status_code=404, detail="User not found")

    genres = instruments_collection.find()  # Get all genres
    results = []
    async for document in genres:  # Asynchronous iteration
        results.append({"name": document["name"]})

    return results