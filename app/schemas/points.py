from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


# 积分充值记录相关模式
class PointsRechargeBase(BaseModel):
    amount: Decimal = Field(..., description="充值金额")
    points: int = Field(..., description="获得积分数量")
    payment_method: Optional[str] = Field(None, description="支付方式")
    exchange_code: Optional[str] = Field(None, description="兑换码")
    transaction_id: Optional[str] = Field(None, description="交易ID")
    remark: Optional[str] = Field(None, description="备注")


class PointsRechargeCreate(PointsRechargeBase):
    user_id: int = Field(..., description="用户ID")


class PointsRechargeUpdate(BaseModel):
    status: Optional[str] = Field(None, description="状态")
    remark: Optional[str] = Field(None, description="备注")


class PointsRechargeOut(PointsRechargeBase):
    id: int
    user_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# 积分使用记录相关模式
class PointsUsageBase(BaseModel):
    points: int = Field(..., description="消耗积分数量")
    usage_type: str = Field(..., description="使用类型")
    description: str = Field(..., description="使用描述")
    related_id: Optional[int] = Field(None, description="关联ID")
    remark: Optional[str] = Field(None, description="备注")


class PointsUsageCreate(PointsUsageBase):
    user_id: int = Field(..., description="用户ID")


class PointsUsageUpdate(BaseModel):
    remark: Optional[str] = Field(None, description="备注")


class PointsUsageOut(PointsUsageBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# 兑换码相关模式
class ExchangeCodeBase(BaseModel):
    code: str = Field(..., description="兑换码")
    points: int = Field(..., description="积分数量")
    expires_at: Optional[datetime] = Field(None, description="过期时间")
    remark: Optional[str] = Field(None, description="备注")


class ExchangeCodeCreate(ExchangeCodeBase):
    created_by: Optional[int] = Field(None, description="创建者ID")


class ExchangeCodeUpdate(BaseModel):
    is_used: Optional[bool] = Field(None, description="是否已使用")
    remark: Optional[str] = Field(None, description="备注")


class ExchangeCodeOut(ExchangeCodeBase):
    id: int
    is_used: bool
    used_by: Optional[int]
    used_at: Optional[datetime]
    created_at: datetime
    created_by: Optional[int]

    class Config:
        from_attributes = True


# API请求模式
class ExchangeCodeUseRequest(BaseModel):
    code: str = Field(..., description="兑换码")


class RechargeRequest(BaseModel):
    amount: Decimal = Field(..., description="充值金额", ge=100)  # 最低100元
    payment_method: str = Field(..., description="支付方式")  # alipay, wechat


class PointsStatsOut(BaseModel):
    """积分统计输出模式"""
    current_balance: int = Field(..., description="当前积分余额")
    total_recharged_amount: float = Field(..., description="历史充值总额")
    total_recharged_points: int = Field(..., description="历史充值积分总数")
    total_used_points: int = Field(..., description="历史使用积分总数")
    recharge_records_count: int = Field(..., description="充值记录数量")
    usage_records_count: int = Field(..., description="使用记录数量")


class PointsInfoOut(BaseModel):
    """积分信息输出模式"""
    stats: PointsStatsOut
    recent_recharge_records: list[PointsRechargeOut]
    exchange_rate: dict = Field(default={"cny_to_points": 1, "description": "1元 = 1积分"})
