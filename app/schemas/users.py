from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class BaseUser(BaseModel):
    id: int
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    last_login: Optional[datetime]
    roles: Optional[list] = []
    # 新增字段
    parent_user_id: Optional[int] = -1
    points_balance: Optional[int] = 0
    invitation_code: Optional[str] = None
    school: Optional[str] = ""
    major: Optional[str] = ""


class UserCreate(BaseModel):
    email: EmailStr = Field(example="admin@qq.com")
    username: str = Field(example="admin")
    password: str = Field(example="123456")
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    role_ids: Optional[List[int]] = []
    # 新增字段
    invitation_code: Optional[str] = Field(None, description="邀请码")
    school: Optional[str] = Field("", description="学校")
    major: Optional[str] = Field("", description="专业")

    def create_dict(self):
        return self.model_dump(exclude_unset=True, exclude={"role_ids", "invitation_code"})


class UserUpdate(BaseModel):
    id: int
    email: EmailStr
    username: str
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    role_ids: Optional[List[int]] = []
    # 新增字段
    parent_user_id: Optional[int] = -1
    points_balance: Optional[int] = 0
    school: Optional[str] = ""
    major: Optional[str] = ""


class UpdatePassword(BaseModel):
    old_password: str = Field(description="旧密码")
    new_password: str = Field(description="新密码")
