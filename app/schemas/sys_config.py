from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BaseSysConfig(BaseModel):
    """系统配置基础模型"""
    id: int
    config_name: str
    config_key: str
    config_value: str
    is_enabled: bool
    created_by: int
    created_at: datetime
    updated_at: datetime


class SysConfigCreate(BaseModel):
    """创建系统配置请求模型"""
    config_name: str = Field(..., min_length=1, max_length=100, description="设置项名称")
    config_key: str = Field(..., min_length=1, max_length=50, description="设置项标识")
    config_value: str = Field(..., description="设置项值")
    is_enabled: Optional[bool] = Field(default=True, description="是否启用")

    def create_dict(self):
        return self.model_dump(exclude_unset=True)


class SysConfigUpdate(BaseModel):
    """更新系统配置请求模型"""
    id: int = Field(..., description="配置ID")
    config_name: Optional[str] = Field(None, min_length=1, max_length=100, description="设置项名称")
    config_key: Optional[str] = Field(None, min_length=1, max_length=50, description="设置项标识")
    config_value: Optional[str] = Field(None, description="设置项值")
    is_enabled: Optional[bool] = Field(None, description="是否启用")

    def update_dict(self):
        return self.model_dump(exclude_unset=True, exclude={"id"})


class SysConfigResponse(BaseModel):
    """系统配置响应模型"""
    id: int
    config_name: str
    config_key: str
    config_value: str
    is_enabled: bool
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FrontendConfigUpdate(BaseModel):
    """前台设置批量更新模型"""
    site_name: Optional[str] = Field(None, max_length=100, description="网站名称")
    recharge_rate: Optional[str] = Field(None, description="积分充值单价")
    maintenance_mode: Optional[bool] = Field(None, description="是否开启维护模式")


class FrontendConfigResponse(BaseModel):
    """前台设置响应模型"""
    site_name: str = ""
    recharge_rate: str = "1.0"
    maintenance_mode: bool = False
