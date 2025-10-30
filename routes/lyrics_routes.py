from fastapi import APIRouter, Depends, HTTPException
from typing import List
from model.lyrics_shemas import Lyrics, LyricsInDB, NewLyrics
from model.user_shemas import NewUser
from config.security import get_current_user, get_user_id
from config.db import get_database
from pymongo.errors import PyMongoError
from bson import ObjectId
from config.db import get_database, lyrics_collection

router = APIRouter()

# Obtener todas las letras del usuario actual
@router.get("/user", response_model=List[Lyrics])
async def get_user_lyrics(current_user: NewUser = Depends(get_current_user), db=Depends(get_database)):
    user_id = await get_user_id(current_user.username)
    try:
        user_lyrics = await lyrics_collection.find({"user_id": user_id}).to_list(None)
        return user_lyrics
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail="Failed to fetch user lyrics") from e

@router.post("/", response_model=LyricsInDB)
async def create_lyrics(new_lyrics: NewLyrics, current_user: NewUser = Depends(get_current_user), db=Depends(get_database)):
    try:
        lyrics_dict = new_lyrics.dict()
        lyrics_dict['user_id'] = await get_user_id(current_user.username)
        result = await lyrics_collection.insert_one(lyrics_dict)
        inserted_id = str(result.inserted_id)  # Obtener el ObjectId y convertirlo a str
        lyrics_out = LyricsInDB(**lyrics_dict, id=inserted_id)
        return lyrics_out
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail="Failed to create lyrics") from e

# Obtener una letra por su ID
@router.get("/{lyrics_id}", response_model=Lyrics)
async def get_lyrics(lyrics_id: str, current_user: NewUser = Depends(get_current_user), db=Depends(get_database)):
    try:
        lyrics = await lyrics_collection.find_one({"_id": ObjectId(lyrics_id), "user_id":await get_user_id(current_user.username)})
        if lyrics:
            return lyrics
        else:
            raise HTTPException(status_code=404, detail="Lyrics not found")
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail="Failed to fetch lyrics") from e

# Actualizar una letra por su ID
@router.put("/{lyrics_id}", response_model=LyricsInDB)
async def update_lyrics(lyrics_id: str, updated_lyrics: NewLyrics, current_user: NewUser = Depends(get_current_user), db=Depends(get_database)):
    try:
        user_id = await get_user_id(current_user.username)
        lyrics_dict = updated_lyrics.dict()
        result = await lyrics_collection.update_one({"_id": ObjectId(lyrics_id)}, {"$set": lyrics_dict})
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Lyrics not found")
        
        updated_lyrics_in_db = await lyrics_collection.find_one({"_id": ObjectId(lyrics_id)})
        return LyricsInDB(**updated_lyrics_in_db, id=lyrics_id)
    
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail="Failed to update lyrics") from e

# Eliminar una letra por su ID
@router.delete("/{lyrics_id}", response_model=LyricsInDB)
async def delete_lyrics(lyrics_id: str, current_user: NewUser = Depends(get_current_user), db=Depends(get_database)):
    try:
        user_id = await get_user_id(current_user.username)
        lyrics = await lyrics_collection.find_one_and_delete({"_id": ObjectId(lyrics_id), "user_id": user_id})
        if lyrics:
            lyrics_in_db = LyricsInDB(**lyrics, id=str(lyrics_id))
            return lyrics_in_db
        else:
            raise HTTPException(status_code=404, detail="Lyrics not found")
    except PyMongoError as e:
        raise HTTPException(status_code=500, detail="Failed to delete lyrics") from e



