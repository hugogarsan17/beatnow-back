import email
import bcrypt
from bson import ObjectId
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
import jwt
from pydantic import EmailStr
from config.mail import send_email
from config.security import ALGORITHM, SECRET_KEY, get_current_user, get_current_user_without_confirmation, get_user, get_user_id, get_username
from model.user_shemas import NewUser, User
import random
from config.db import mail_code_collection,users_collection
from model.shemas import Mail_Code


router = APIRouter()

def generate_six_digit_number():
    number = random.randrange(0, 999999)
    return str(number).zfill(6)


async def create_and_save_confirmation_code(user: User):
    confirmation_code = generate_six_digit_number()
    # Hash the password before saving it
    code_hash = bcrypt.hashpw(confirmation_code.encode('utf-8'), bcrypt.gensalt())
    user_id=await get_user_id(user.username)
    mail_code=Mail_Code(user_id=user_id,code=code_hash)
    await mail_code_collection.delete_many({"user_id": user_id})
    result = await mail_code_collection.insert_one(mail_code.dict())
    if not result.inserted_id:
        raise HTTPException(status_code=500, detail="Failed to save code")
    return confirmation_code

@router.post("/send-confirmation/")
async def send_confirmation(user: NewUser = Depends(get_current_user_without_confirmation)):
    try:
        if user.is_active:
            raise HTTPException(status_code=400, detail="User already confirmed")
        confirmation_code = await create_and_save_confirmation_code(user)
        subject = "Confirmación de Registro"
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Email Verification</title>
        </head>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5;">
            <div class="container" style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div class="header">
                    <img src="http://172.203.251.28/res/logo.png" alt="BeatNow Logo">
                    <h1>Verify your email address</h1>
                </div>
                <div class="body">
                    <p>Hello {user.username},</p>
                    <p>You need to verify your email address to continue using your BeatNow account. Enter the following code to verify your email address:</p>
                    <h2 style="text-align: center;">{confirmation_code}</h2>
                    <p>In case you were not trying to access your BeatNow Account & are seeing this email, please follow the instructions below:</p>
                    <ul>
                        <li>Reset your BeatNow password.</li>
                        <li>Check if any changes were made to your account & user settings. If yes, revert them immediately.</li>
                    </ul>
                    <p>Thank You!</p>
                    <p>BeatNow Team</p>
                </div>
                <div class="footer">
                    <p>&copy; 2024 BeatNow. All Rights Reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """


        send_email(user.email, subject, html_content)
        return {"message": "Correo de confirmación enviado", "codigo": confirmation_code}
    except Exception as e:
        print(f"Error: {e}")  
        return {"error": str(e)}

async def verify_confirmation_code(user: User, provided_code: str):
    user_id = await get_user_id(user.username)
    stored_code = await mail_code_collection.find_one({"user_id": user_id})

    if not stored_code:
        raise HTTPException(status_code=404, detail="No code found for this user")

    # Compara el hash del código proporcionado con el hash almacenado
    if bcrypt.checkpw(provided_code.encode('utf-8'), stored_code['code'].encode('utf-8')):
        return True  

    return False 

@router.post("/confirmation/")
async def confirmation(code: str, user: NewUser = Depends(get_current_user_without_confirmation)):
    confirmation = await verify_confirmation_code(user, code)
    if not confirmation:
        raise HTTPException(status_code=400, detail="Invalid code")
    else:
        user_id=await get_user_id(user.username)
        await mail_code_collection.delete_many({"user_id": user_id})
        result = await users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"is_active": True}})
        if result.modified_count == 0:
            raise HTTPException(status_code=500, detail="Failed to modify user")
    return {"message": "Ok"}

async def create_request_password(user: User):
    user_id = await get_user_id(user.username)
    if not isinstance(user_id, dict):
        user_id = {'user_id': user_id}
    token = jwt.encode(user_id, SECRET_KEY, algorithm=ALGORITHM)
    return token

@router.post("/send-password-reset/")
async def send_password_reset(mail: str):
    mail = mail.replace("%40", "@")
    try:
        user_find = await users_collection.find_one({"email": mail})
        if not user_find:
            raise HTTPException(status_code=404, detail="Mail not found")
        user = NewUser(**user_find)
        reset_token = await create_request_password(user)
        subject = "Password Reset"
        reset_link = "https://yourwebsite.com/reset-password/{reset_token}"
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reset Your Password</title>
        </head>
        <body style="font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5;">
            <div class="container" style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <div class="header">
                    <img src="http://172.203.251.28/res/logo.png" alt="BeatNow Logo">
                    <h1>Password Reset</h1>
                </div>
                <div class="body">
                    <p>Hello {user.username},</p>
                    <p>We received a request to reset your password. If this was you, please click the following link to reset your password:</p>
                    <a href="{reset_link}">Reset Password</a>
                    <p>{reset_token}</p>
                    <p>If you didn't request a password reset, you can safely ignore this email.</p>
                    <p>Thank you!</p>
                </div>
                <div class="footer">
                    <p>&copy; 2024 BeatNow. All Rights Reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        send_email(user.email, subject, html_content)
        return {"message": "Password reset email sent", "reset_token": reset_token}
    except Exception as e:
        print(f"Error: {e}")  # Print the error message
        raise HTTPException(status_code=500, detail="Failed to send password reset email")

@router.post("/password-change/")
async def password_change(token: str):
    # Ahora puedes decodificar el token de nuevo en un payload
    decoded_payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    if not decoded_payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    username = await get_username(decoded_payload['user_id'])
    user= await get_user(username)
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Incorrect user"
        )
    return {"message": "Ok"}
