from config.security import SSH_USERNAME_RES, SSH_PASSWORD_RES, SSH_HOST_RES, \
    get_current_user, get_user_id
import random
from fastapi import APIRouter, Form, HTTPException, Depends, UploadFile, File
from bson import ObjectId
from typing import List, Optional
import paramiko
from model.post_shemas import Post, PostInDB, PostShowed, NewPost
from config.db import get_database, parse_list, post_collection, users_collection, interactions_collection, lyrics_collection
from config.security import get_current_user, get_user_id, get_username
from model.user_shemas import NewUser, User
from routes.interactions_routes import count_likes, count_saved
from fastapi import File, UploadFile, HTTPException
import os
import shutil
from datetime import datetime

router = APIRouter()

@router.post("/upload", response_model=PostInDB)
async def upload_post(
    cover_file: UploadFile = File(...),
    audio_file: UploadFile = File(...),
    title: str = Form(...),
    description: Optional[str] = Form(...),
    genre: Optional[str] = Form(...),
    tags: Optional[str] = Form(...),
    moods: Optional[str] = Form(...),
    instruments: Optional[str] = Form(...),
    bpm: Optional[int] = Form(...),
    current_user: NewUser = Depends(get_current_user)
):
    # Convertir strings de listas a listas de Python
    tags_list = parse_list(tags)
    moods_list = parse_list(moods)
    instruments_list = parse_list(instruments)
    new_post = NewPost(
        title=title,
        description=description,
        tags=tags_list,
        genre=genre,
        moods=moods_list,
        instruments=instruments_list,
        bpm=bpm,
    )
    # Validar el tipo de archivo antes de continuar
    allowed_image_extensions = {".jpg", ".jpeg",".gif"}
    allowed_audio_extensions = {".wav", ".mp3"}

    if not cover_file.filename.lower().endswith(tuple(allowed_image_extensions)):
        raise HTTPException(status_code=415, detail="Only JPG/JPEG or GIF files are allowed for images.")

    if audio_file:
        if not audio_file.filename.lower().endswith(tuple(allowed_audio_extensions)):
            raise HTTPException(status_code=415, detail="Only MP3/WAV files are allowed for audio.")
    user_id=await get_user_id(current_user.username)
    if not user_id:
        raise HTTPException(status_code=404, detail="User not found")
    audio_file_extension = audio_file.filename.split(".")[-1]
    if audio_file_extension  in ["mp3"]:
        audio_format="mp3"
    else:
        audio_format="wav"
    cover_file_extension = cover_file.filename.split(".")[-1]
    if cover_file_extension  in ["jpg","jpeg"]:
        cover_format="jpg"
    else:
        cover_format="gif"
    # Crear el post en la base de datos
    result = None
    try:
        post = Post(
            user_id=str(ObjectId(user_id)),
            publication_date=datetime.now(),
            audio_format=audio_format,
            cover_format=cover_format,
            likes=0,
            saves=0,
            **new_post.dict()
        )
        result = await post_collection.insert_one(post.dict())
        if not result.inserted_id:
            raise HTTPException(status_code=500, detail="Failed to create publication")

        post_id = str(result.inserted_id)
        post_dir = f"/var/www/html/beatnow/{user_id}/posts/{post_id}/"

        # Configuración de SSH
        with paramiko.SSHClient() as ssh:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(hostname=SSH_HOST_RES, username=SSH_USERNAME_RES, password=SSH_PASSWORD_RES)

            # Verificar si el directorio del usuario existe, si no, crearlo
            if not ssh.exec_command(f"test -d {post_dir}")[1].read():
                
                # Crear directorios en el servidor remoto
                ssh.exec_command(f"sudo mkdir -p {post_dir}")
                ssh.exec_command(f"sudo chown -R $USER:$USER {post_dir}")
            if cover_file:
                if cover_format in ["jpg","jpeg"]:
                    cover_file_path = os.path.join(post_dir, "caratula.jpg")
                else:
                    cover_file_path = os.path.join(post_dir, "caratula.gif")
                with ssh.open_sftp().file(cover_file_path, "wb") as buffer:
                    shutil.copyfileobj(cover_file.file, buffer)
            if audio_file:
                if audio_file_extension  in ["mp3"]:
                    audio_file_path = os.path.join(post_dir, "audio.mp3")
                else:
                    audio_file_path = os.path.join(post_dir, "audio.wav")
                
                with ssh.open_sftp().file(audio_file_path, "wb") as buffer:
                    shutil.copyfileobj(audio_file.file, buffer)

    except paramiko.SSHException as e:
        await post_collection.delete_one({"_id": result.inserted_id})
        raise HTTPException(status_code=500, detail=f"SSH error: {str(e)}")
    except Exception as e:
        if result:
            # Eliminar el post de la base de datos si se ha creado antes de la excepción
            await post_collection.delete_one({"_id": result.inserted_id})
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    existing_post = await post_collection.find_one({"_id": ObjectId(post_id)})
    if not existing_post:
        raise HTTPException(status_code=404, detail="Post not found")
    return PostInDB(_id=post_id, **post.dict())

@router.put("/update/{post_id}", response_model=PostInDB)
async def update_post(
    post_id: str,
    cover_file: UploadFile = File(None),
    audio_file: UploadFile = File(None),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    genre: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    moods: Optional[str] = Form(None),
    instruments: Optional[str] = Form(None),
    bpm: Optional[int] = Form(None),
    current_user: NewUser = Depends(get_current_user)
):
    # Convertir strings de listas a listas de Python
    tags_list = parse_list(tags)
    moods_list = parse_list(moods)
    instruments_list = parse_list(instruments)
    post=await post_collection.find_one({"_id": ObjectId(post_id)})
    if not post:     
        raise HTTPException(status_code=404, detail="Post not found")
    creator_id = post["user_id"]
    publication_date = post["publication_date"]

    if not cover_file.filename.lower().endswith(tuple(allowed_image_extensions)):
        raise HTTPException(status_code=415, detail="Only JPG/JPEG or GIF files are allowed for images.")
    cover_file_extension = cover_file.filename.split(".")[-1]
    if cover_file_extension  in ["jpg","jpeg"]:
        cover_format="jpg"
    else:
        cover_format="gif"
    if audio_file:
        file_extension = audio_file.filename.split(".")[-1]
        if file_extension  in ["mp3"]:
            audio_format="mp3"
        else:
            audio_format="wav"
    else:
        audio_format=post["audio_format"]
    new_post = PostInDB(
        title=title,
        description=description,
        genre=genre,
        tags=tags_list,
        moods=moods_list,
        instruments=instruments_list,
        bpm=bpm,
        user_id=creator_id,
        publication_date=publication_date,
        audio_format=audio_format,
        cover_format=cover_format,
        likes=await count_likes(post_id),
        saves=await count_saved(post_id),
        _id=post_id
    )
    
    user_id = await get_user_id(current_user.username)
    if user_id != post["user_id"]:
        raise HTTPException(status_code=403, detail="You are not authorized to update this publication")
    updated_post= new_post.dict()

    # Actualizar la base de datos
    update_result = await post_collection.update_one(
        {"_id": ObjectId(post_id)},
        {"$set": {k: v for k, v in updated_post.items() if v is not None}}
        )

    if update_result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to update publication")

    # Manejo de archivos si se proporcionan
    try:
        if cover_file or audio_file:
            post_dir = f"/var/www/html/beatnow/{user_id}/posts/{post_id}/"
            with paramiko.SSHClient() as ssh:
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(hostname=SSH_HOST_RES, username=SSH_USERNAME_RES, password=SSH_PASSWORD_RES)
                if cover_file:
                    if cover_format in ["jpg","jpeg"]:
                        cover_file_path = os.path.join(post_dir, "caratula.jpg")
                    else:
                        cover_file_path = os.path.join(post_dir, "caratula.gif")
                    with ssh.open_sftp().file(cover_file_path, "wb") as buffer:
                        shutil.copyfileobj(cover_file.file, buffer)
                if audio_file:
                    if file_extension  in ["mp3"]:
                        audio_file_path = os.path.join(post_dir, "audio.mp3")
                    else:
                        audio_file_path = os.path.join(post_dir, "audio.wav")
                    with ssh.open_sftp().file(audio_file_path, "wb") as buffer:
                        shutil.copyfileobj(audio_file.file, buffer)
    except paramiko.SSHException as e:
        raise HTTPException(status_code=500, detail=f"SSH error: {str(e)}")

    # Devolver la publicación actualizada
    updated_post = await post_collection.find_one({"_id": ObjectId(post_id)})
    return PostInDB(**updated_post)



@router.get("/random", response_model=PostShowed)
async def get_random_publication(current_user: User = Depends(get_current_user), db=Depends(get_database)):
    # Fetch all post IDs
    post_ids = await post_collection.find({}, {"_id": 1}).to_list(length=None)

    if not post_ids:
        raise HTTPException(status_code=404, detail="No publications found")

    # Select a random ID from the list
    random_post_id = random.choice(post_ids)['_id']
    user_id=await get_user_id(current_user.username)

    # Use the existing read_publication function to fetch and return the publication details
    return await read_publication(str(random_post_id), current_user, db)

@router.get("/{post_id}", response_model=PostShowed)
async def read_publication(post_id: str, current_user: User = Depends(get_current_user), db=Depends(get_database)):
    readed_post = await read_post(post_id, current_user)
    if readed_post is not None:
        return readed_post
    else:
        raise HTTPException(status_code=404, detail="Publication not found")

async def read_post(post_id: str, current_user: User):
    post_dict = await post_collection.find_one({"_id": ObjectId(post_id)})
    if post_dict:
        postindb = Post(**post_dict)
        creator_name = await get_username(post_dict["user_id"])  # Use post_dict instead of post_id
        post_result = PostShowed(_id=str(ObjectId(post_id)), **postindb.dict(),creator_username=creator_name,isLiked=await has_liked_post(post_id, current_user),
                          isSaved=await has_saved_post(post_id, current_user))
        return post_result
    else:
        return None
    



#no elimina la publicacion de la base de datos ni servidor
# Eliminar publicación por ID
@router.delete("/{post_id}")
async def delete_publication(post_id: str, current_user: User = Depends(get_current_user), db=Depends(get_database)):
    existing_publication = await post_collection.find_one({"_id": ObjectId(post_id)})
    if existing_publication:
        if existing_publication["user_id"] != await get_user_id(current_user.username):
            raise HTTPException(status_code=403, detail="You are not authorized to delete this publication")
        await interactions_collection.delete_many({"post_id:": post_id})
        await lyrics_collection.update_many({"post_id:": post_id},{ "$set": { "post_id": "None" } })
        result = await post_collection.delete_one({"_id": ObjectId(post_id)})
        if result.deleted_count == 1:
            return {"message": "Publication deleted successfully"}
    raise HTTPException(status_code=404, detail="Publication not found")




async def has_liked_post(post_id: str, current_user: User):
    user_id = await get_user_id(current_user.username)
    like_exists = await interactions_collection.count_documents({"user_id": user_id, "post_id": post_id, "like_date": {"$exists": True}})
    return like_exists > 0

async def has_saved_post(post_id: str, current_user: User):
    user_id = await get_user_id(current_user.username)
    saved_exists = await interactions_collection.count_documents({"user_id": user_id, "post_id": post_id, "saved_date": {"$exists": True}})
    return saved_exists > 0
'''
@router.post("/change_post_cover/{post_id}")
async def change_post_cover(post_id: str, file: UploadFile = File(...), current_user: NewUser = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = await get_user_id(current_user.username)
    try:
        # Obtener el post
        post = await post_collection.find_one({"_id": ObjectId(post_id)})
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        # Verificar si el usuario tiene permisos para editar el post
        if user_id != post["user_id"]:
            raise HTTPException(status_code=403, detail="Unauthorized to edit this post")

        # Guardar la nueva carátula con un nombre único y formato png
        file_path = os.path.join("/var/www/html/beatnow", current_user.username, "posts", post_id, "caratula.jpg")
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    return {"message": "Post cover updated successfully"}
'''
#@router.post("/delete_post_cover/{post_id}")
async def delete_post_cover(post_id: str, current_user: User = Depends(get_current_user)):
    user_id = await get_user_id(current_user.username)
    try:
        # Obtener el post
        post = await post_collection.find_one({"_id": post_id})
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        # Verificar si el usuario tiene permisos para editar el post
        if post["user_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Unauthorized to edit this post")

        # Eliminar la carátula del post
        post_dir = f"/var/www/html/beatnow/{user_id}/posts/{post_id}"
        os.remove(os.path.join(post_dir, "cover.png"))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

    return {"message": "Post cover deleted successfully"}

async def count_user_posts(user_id: str, current_user: User = Depends(get_current_user), db=Depends(get_database)):

    # Contar las publicaciones del usuario
    count = await post_collection.count_documents({"user_id": user_id})
    return count




