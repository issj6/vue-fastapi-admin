from tortoise import fields

from .base import BaseModel, TimestampMixin


class SysConfig(BaseModel, TimestampMixin):
    """系统配置表"""
    
    config_name = fields.CharField(max_length=100, description="设置项名称")
    config_key = fields.CharField(max_length=50, unique=True, description="设置项标识", index=True)
    config_value = fields.TextField(description="设置项值")
    is_enabled = fields.BooleanField(default=True, description="是否启用")
    created_by = fields.ForeignKeyField("models.User", related_name="created_configs", description="创建人")
    
    class Meta:
        table = "sys_config"
        table_description = "系统配置表"
        
    def __str__(self):
        return f"{self.config_name}({self.config_key})"
