from datetime import datetime
from typing import List
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from model.follow_shemas import Follow
from model.user_shemas import NewUser
from config.db import follows_collection, get_database, follows_collection
from config.security import get_current_user, get_user_id

router = APIRouter()

@router.post("/follow/{user_id}", response_model=Follow, status_code=status.HTTP_201_CREATED)
async def create_follow(user_id: str, current_user: NewUser = Depends(get_current_user), db=Depends(get_database)):
    # Verificar si ya existe una relación de seguimiento entre los usuarios
    user_id_following = await get_user_id(current_user.username)
    existing_follow = await follows_collection.find_one({"user_id_followed": user_id, "user_id_following": user_id_following})
    if existing_follow:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already following this user")

    # Crear una nueva relación de seguimiento
    follow_dict = Follow(user_id_followed=user_id, user_id_following=user_id_following, follow_date=datetime.utcnow()).dict()
    result = await follows_collection.insert_one(follow_dict)
    follow_id = str(result.inserted_id)
    return {**follow_dict, "_id": follow_id}
'''
@router.get("/{follow_id}", response_model=Follow)
async def read_follow(follow_id: str, db=Depends(get_database)):
    follow = await follows_collection.find_one({"_id": follow_id})
    if follow:
        return follow
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Follow not found")


@router.put("/{follow_id}", response_model=Follow)
async def update_follow(follow_id: str, follow: Follow, db=Depends(get_database)):
    existing_follow = await follows_collection.find_one({"_id": follow_id})
    if existing_follow is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Follow not found")
    
    updated_follow = {**existing_follow, **follow.dict()}
    await follows_collection.replace_one({"_id": follow_id}, updated_follow)
    return updated_follow
'''

@router.delete("/unfollow/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_follow(user_id: str, current_user: NewUser = Depends(get_current_user), db=Depends(get_database)):
    # Obtener los IDs de usuario
    user_id_following = await get_user_id(current_user.username)
    user_id_followed = user_id
    result = await follows_collection.find_one({"user_id_following": user_id_following, "user_id_followed": user_id_followed})
    if result is None:        
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Follow not found")
    # Eliminar la relación de seguimiento si existe
    result = await follows_collection.delete_one({"_id": result["_id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Error deleting follow")
    return {"message": "Follow deleted successfully"}
#@router.get("/count/{user_id_followed}")
async def count_followers(user_id_followed: str, current_user: NewUser = Depends(get_current_user), db=Depends(get_database)):
    count = await follows_collection.count_documents({"user_id_followed": user_id_followed})
    return {"user_id_followed": user_id_followed, "followers_count": count}

async def count_following(user_id_follower: str, current_user: NewUser = Depends(get_current_user), db=Depends(get_database)):
    count = await follows_collection.count_documents({"user_id_follower": user_id_follower})
    return {"user_id_follower": user_id_follower, "following_count": count}
#@router.get("/followers/{user_id_followed}")
async def get_follower(user_id_followed: str,  db=Depends(get_database),current_user: NewUser = Depends(get_current_user)):
    followers = await follows_collection.find({"user_id_followed": user_id_followed}).to_list(None)
    return followers

#@router.get("/following/{user_id_following}")
async def get_following(user_id_following: str,db=Depends(get_database),current_user: NewUser = Depends(get_current_user)):
    following = await follows_collection.find({"user_id_following": user_id_following}).to_list(None)
    return following

async def is_following(user_id: str, db=Depends(get_database), current_user: NewUser = Depends(get_current_user)):
    # Obtener los IDs de usuario
    user_id_following = await get_user_id(current_user.username)
    user_id_followed = user_id
    
    # Verificar si existe la relación de seguimiento
    follow = await follows_collection.find_one({"user_id_following": user_id_following, "user_id_followed": user_id_followed})
    return follow is not None
#hay que arreglarlas
@router.get("/followers/{user_id_followed}")
async def get_followers(user_id_followed: str, db = Depends(get_database)):
    # Recuperar todos los documentos que tienen el user_id_followed
    followers_docs = await db.follows_collection.find({"user_id_followed": user_id_followed}).to_list(None)
    
    # Extraer los user_ids de los seguidores
    follower_ids = [doc["user_id_following"] for doc in followers_docs]
    
    # Recuperar detalles completos de cada seguidor
    followers = []
    for user_id in follower_ids:
        user_info = await db.users_collection.find_one({"_id": ObjectId(user_id)})
        if user_info:
            followers.append(user_info)

    return {"followers": followers}

@router.get("/following/{user_id_following}")
async def get_following(user_id_following: str, db = Depends(get_database)):
    # Recuperar todos los documentos que tienen el user_id_following
    following_docs = await follows_collection.find({"user_id_following": user_id_following}).to_list(None)
    
    # Extraer los user_ids de los usuarios seguidos
    following_ids = [doc["user_id_followed"] for doc in following_docs]
    
    # Recuperar detalles completos de cada usuario seguido
    following = []
    for user_id in following_ids:
        user_info = await db.users_collection.find_one({"_id": ObjectId(user_id)})
        if user_info:
            following.append(user_info)

    return {"following": following}
