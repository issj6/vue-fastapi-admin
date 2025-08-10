from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BaseRole(BaseModel):
    id: int
    name: str
    desc: str = ""
    users: Optional[list] = []
    menus: Optional[list] = []
    apis: Optional[list] = []
    agent_permissions: Optional[list] = []
    is_agent_role: bool = False
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


class RoleCreate(BaseModel):
    name: str = Field(example="管理员")
    desc: str = Field("", example="管理员角色")
    agent_permissions: Optional[list] = Field(default=[], example=["VIEW_SUBORDINATE_USERS", "CREATE_USER"])
    is_agent_role: bool = Field(default=False, example=True)


class RoleUpdate(BaseModel):
    id: int = Field(example=1)
    name: str = Field(example="管理员")
    desc: str = Field("", example="管理员角色")
    agent_permissions: Optional[list] = Field(default=[], example=["VIEW_SUBORDINATE_USERS", "CREATE_USER"])
    is_agent_role: bool = Field(default=False, example=True)


class RoleUpdateMenusApis(BaseModel):
    id: int
    menu_ids: list[int] = []
    api_infos: list[dict] = []


class RoleUpdateAgentPermissions(BaseModel):
    """更新角色代理权限"""
    id: int = Field(description="角色ID")
    agent_permissions: list[str] = Field(default=[], description="代理权限列表")
    is_agent_role: bool = Field(default=False, description="是否为代理角色")
