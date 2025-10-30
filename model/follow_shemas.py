from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, Field, validator
from datetime import datetime

class Follow(BaseModel):
    user_id_followed: str = Field(alias="user_id_followed")
    user_id_following: str = Field(alias="user_id_following")
    follow_date: Optional[datetime] = Field(default=None, alias="follow_date")