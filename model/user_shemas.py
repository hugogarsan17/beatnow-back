from typing import Dict, List, Optional
from xml.dom.minidom import Document
from bson import ObjectId
from pydantic import BaseModel, Field, validator


class NewUser(BaseModel):
    full_name: Optional[str] = Field(alias="full_name")
    username: str = Field(alias="username")
    email: Optional[str] = Field(alias="email")
    password: Optional[str] = Field(alias="password")
    is_active: Optional[bool] = Field(default=False, alias="is_active")

class User(NewUser):
    bio : Optional[str] = Field(default=None, alias="bio")


class UserInDB(User):
    id: Optional[str] = Field(default=None, alias='_id')

    @validator('id', pre=True, always=True)
    def convert_id(cls, v):
        return str(v) if isinstance(v, ObjectId) else v

class UserProfile(UserInDB):
    followers: int = Field(alias="followers")
    following: int = Field(alias="following")
    post_num: int = Field(alias="post_num")
    is_following: bool = Field(alias="is_following")
    #publications: List[PostShowed] = Field(alias="publications")

class UserInfo(UserInDB):
    followers: Optional[list[str]] = Field(alias="followers")
    following: Optional[list[str]] = Field(alias="following")

class UserSearch(BaseModel):
    username: str