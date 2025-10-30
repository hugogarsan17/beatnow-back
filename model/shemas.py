from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, Field, validator
from datetime import datetime


class Interaction(BaseModel):
    user_id: str = Field(alias="user_id")
    post_id: str = Field(alias="publication_id")
    like_date: Optional[datetime] = Field(default=None, alias="like_date")
    saved_date: Optional[datetime] = Field(default=None, alias="saved_date")
    dislike_date: Optional[datetime] = Field(default=None, alias="dislike_date")

class Mail_Code(BaseModel):
    user_id: str = Field(alias="user_id")
    code: str = Field(alias="code")



# Schemas para comprobar uso
'''


class LicenseType(BaseModel):
    license_type: str = Field(alias="license_type")
    description: str = Field(alias="description")

class License(BaseModel):
    license_type_id: str = Field(alias="license_type")
    user_description: str = Field(alias="user_description")
    post_id: str = Field(alias="post_id")
    price: float = Field(alias="price")

class Purchase(BaseModel):
    buyer_user_id: str = Field(alias="user_id")
    owner_user_id: str = Field(alias="user_id")
    base_id: str = Field(alias="base_id")
    price: float = Field(alias="price")

'''




