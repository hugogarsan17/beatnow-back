from datetime import timedelta
from typing import List, Optional
from passlib.handlers.bcrypt import bcrypt
import bcrypt
from model.user_shemas import NewUser
from config.security import guardar_log, ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, get_user
from config.db import users_collection, post_collection
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import HTTPException, Depends, APIRouter, Query

# Iniciar router
router = APIRouter()

# Login
@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user_dict = await users_collection.find_one({"username": form_data.username})
    if not user_dict:
        guardar_log("Login failed - Incorrect username: " + form_data.username)
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    user = NewUser(**user_dict)
    if not bcrypt.checkpw(form_data.password.encode('utf-8'), user_dict['password']):
        guardar_log("Login failed - Incorrect password for username: " + form_data.username)
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Incorrect username or password"
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}
                                       , expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

