from tortoise.models import Model
from tortoise import fields
from app.models.enums import AnnouncementType
from app.models.base import BaseModel, TimestampMixin


class Announcement(BaseModel, TimestampMixin):
    """公告模型"""
    
    # 基本信息
    title = fields.CharField(max_length=200, null=True, blank=True, description="公告标题")
    content = fields.TextField(description="公告内容")
    announcement_type = fields.CharEnumField(AnnouncementType, description="公告类型")
    
    # 状态信息
    is_active = fields.BooleanField(default=True, description="是否启用")
    priority = fields.IntField(default=0, description="优先级")
    
    # 时间信息
    start_date = fields.DatetimeField(description="开始时间")
    end_date = fields.DatetimeField(description="结束时间")
    
    # 关联信息 
    created_by = fields.ForeignKeyField("models.User", related_name="created_announcements", description="创建者")
    
    class Meta:
        table = "announcement"
        ordering = ["-priority", "-created_at"]
        
    def __str__(self):
        return f"<Announcement {self.id}: {self.title}>"
