from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    name: str = Field(..., min_length=1)
    role: Literal["instructor", "student"]


class UserCreate(UserBase):
    password_hash: str = Field(..., min_length=1)


class UserResponse(UserBase):
    user_id: int

    model_config = ConfigDict(from_attributes=True)
