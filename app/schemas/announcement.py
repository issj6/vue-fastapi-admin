from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.enums import AnnouncementType


class BaseAnnouncement(BaseModel):
    """公告基础模型"""
    id: int
    title: Optional[str]
    content: str
    announcement_type: AnnouncementType
    is_active: bool
    priority: int
    start_date: datetime
    end_date: datetime
    created_by: int
    created_at: datetime
    updated_at: datetime


class AnnouncementCreate(BaseModel):
    """创建公告请求模型"""
    title: Optional[str] = Field(default="", max_length=200, description="公告标题")
    content: str = Field(..., min_length=1, description="公告内容")
    announcement_type: AnnouncementType = Field(..., description="公告类型")
    is_active: Optional[bool] = Field(default=True, description="是否启用")
    priority: Optional[int] = Field(default=0, description="优先级")
    start_date: datetime = Field(..., description="开始时间")
    end_date: datetime = Field(..., description="结束时间")

    def create_dict(self):
        return self.model_dump(exclude_unset=True)


class AnnouncementUpdate(BaseModel):
    """更新公告请求模型"""
    id: int = Field(..., description="公告ID")
    title: Optional[str] = Field(None, max_length=200, description="公告标题")
    content: Optional[str] = Field(None, min_length=1, description="公告内容")
    announcement_type: Optional[AnnouncementType] = Field(None, description="公告类型")
    is_active: Optional[bool] = Field(None, description="是否启用")
    priority: Optional[int] = Field(None, description="优先级")
    start_date: Optional[datetime] = Field(None, description="开始时间")
    end_date: Optional[datetime] = Field(None, description="结束时间")

    def update_dict(self):
        return self.model_dump(exclude_unset=True, exclude={"id"})


class AnnouncementResponse(BaseModel):
    """公告响应模型"""
    id: int
    title: Optional[str]
    content: str
    announcement_type: str
    is_active: bool
    priority: int
    start_date: datetime
    end_date: datetime
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

