from fastapi import APIRouter, HTTPException, Depends, Security
from datetime import datetime
from config.db import get_database, interactions_collection
from config.security import get_current_user, get_user_id, check_post_exists, decode_token
from model.user_shemas import NewUser

# Iniciar router
router = APIRouter()

# Función para verificar si una interacción ya existe para un usuario en una publicación
async def check_interaction_exists(user_id: str, post_id: str, interaction_type: str, db):
    interaction = await interactions_collection.find_one({"user_id": user_id, "post_id": post_id})
    if interaction and  interaction.get(interaction_type):
        raise HTTPException(status_code=400, detail=f"{interaction_type.capitalize()} already exists")
    return

async def check_uninteraction_exists(user_id: str, post_id: str, interaction_type: str, db):
    interaction = await interactions_collection.find_one({"user_id": user_id, "post_id": post_id})
    if interaction and interaction.get(interaction_type) is None:
        raise HTTPException(status_code=400, detail=f"{interaction_type.capitalize()} already exists")
    return

# Dar like a publicación
@router.post("/like/{post_id}")
async def add_like(post_id: str, current_user: NewUser = Depends(get_current_user), db=Depends(get_database)):
    await check_post_exists(post_id, db)
    user_id = await get_user_id(current_user.username)
    await check_interaction_exists(user_id, post_id, "like_date", db)
    result = await interactions_collection.update_one(
        {"user_id": user_id, "post_id": post_id},
        {"$set": {"like_date": datetime.now()}},
        upsert=True
    )
    if result.modified_count == 0 and result.upserted_id is None:
        raise HTTPException(status_code=500, detail="Failed to add like")
    return {"message": "Like added successfully"}

# Guardar publicación
@router.post("/save/{post_id}")
async def save_publication(post_id: str, current_user: NewUser = Depends(get_current_user), db=Depends(get_database)):
    await check_post_exists(post_id, db)
    user_id = await get_user_id(current_user.username)
    await check_interaction_exists(user_id, post_id, "saved_date", db)
    result = await interactions_collection.update_one(
        {"user_id": user_id, "post_id": post_id},
        {"$set": {"saved_date": datetime.now()}},
        upsert=True
    )
    if result.modified_count == 0 and result.upserted_id is None:
        raise HTTPException(status_code=500, detail="Failed to save publication")
    return {"message": "Publication saved successfully"}

'''# Dar dislike a publicación
@router.post("/dislike/{post_id}")
async def add_dislike(post_id: str, current_user: NewUser = Depends(get_current_user), db=Depends(get_database)):
    await check_post_exists(post_id, db)
    user_id = await get_user_id(current_user.username)
    await check_interaction_exists(user_id, post_id, "dislike_date", db)
    result = await interactions_collection.update_one(
        {"user_id": user_id, "post_id": post_id},
        {"$set": {"dislike_date": datetime.now()}},
        upsert=True
    )
    if result.modified_count == 0 and result.upserted_id is None:
        raise HTTPException(status_code=500, detail="Failed to add dislike")
    return {"message": "Dislike added successfully"}'''
# Quitar like a publicación
@router.delete("/unlike/{post_id}")
async def remove_like(post_id: str, current_user: NewUser = Depends(get_current_user), db=Depends(get_database)):
    await check_post_exists(post_id, db)
    user_id = await get_user_id(current_user.username)
    await check_uninteraction_exists(user_id, post_id, "like_date", db)
    result = await interactions_collection.update_one(
        {"user_id": user_id, "post_id": post_id},
        {"$unset": {"like_date": ""}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to remove like")
    return {"message": "Like removed successfully"}

# Quitar de guardados una publicación
@router.delete("/unsave/{post_id}")
async def remove_saved(post_id: str, current_user: NewUser = Depends(get_current_user), db=Depends(get_database)):
    await check_post_exists(post_id, db)
    user_id = await get_user_id(current_user.username)
    await check_uninteraction_exists(user_id, post_id, "saved_date", db)
    result = await interactions_collection.update_one(
        {"user_id": user_id, "post_id": post_id},
        {"$unset": {"saved_date": ""}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to remove saved publication")
    return {"message": "Saved publication removed successfully"}

'''# Quitar dislike a publicación
@router.post("/undislike/{post_id}")
async def remove_dislike(post_id: str, current_user: NewUser = Depends(get_current_user), db=Depends(get_database)):
    await check_post_exists(post_id, db)
    user_id = await get_user_id(current_user.username)
    result = await interactions_collection.update_one(
        {"user_id": user_id, "post_id": post_id},
        {"$unset": {"dislike_date": ""}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to remove dislike")
    return {"message": "Dislike removed successfully"}'''

# Contar el número de likes de una publicación
#@router.get("/count/likes/{post_id}")
async def count_likes(post_id: str, db=Depends(get_database)):
    try:
        likes_count = await interactions_collection.count_documents({"post_id": post_id, "like_date": {"$exists": True}})
        return likes_count
    except Exception as e:
        print(f"Error al contar los saves: {e}")
        return 0


# Contar el número de publicaciones guardadas
#@router.get("/count/saved/{post_id}")
async def count_saved(post_id: str, db=Depends(get_database)):
    try:
        saved_count = await interactions_collection.count_documents({"post_id": post_id, "saved_date": {"$exists": True}})
        return saved_count
    except Exception as e:
        print(f"Error al contar los saves: {e}")
        return 0

'''# Contar el número de dislikes de una publicación
#@router.get("/count/dislikes/{post_id}")
async def count_dislikes(post_id: str, db=Depends(get_database)):
    try:
        dislikes_count = await interactions_collection.count_documents({"post_id": post_id, "dislike_date": {"$exists": True}})
        return  dislikes_count
    except Exception as e:
        print(f"Error al contar los saves: {e}")
        return 0'''
'''
@router.get("/protected-route")
async def protected_route(current_user: NewUser = Security(decode_token, scopes=["base"])):
    return {"message": "Hello, secured world!", "user": current_user.username}
'''