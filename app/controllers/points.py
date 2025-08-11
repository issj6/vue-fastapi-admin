from datetime import datetime
from typing import List, Optional
from decimal import Decimal

from fastapi.exceptions import HTTPException
from tortoise.transactions import in_transaction

from app.core.crud import CRUDBase
from app.models.admin import User
from app.models.points import PointsRechargeRecord, PointsUsageRecord, ExchangeCode
from app.schemas.points import (
    PointsRechargeCreate, PointsRechargeUpdate,
    PointsUsageCreate, PointsUsageUpdate,
    ExchangeCodeCreate, ExchangeCodeUpdate
)


class PointsRechargeController(CRUDBase[PointsRechargeRecord, PointsRechargeCreate, PointsRechargeUpdate]):
    def __init__(self):
        super().__init__(model=PointsRechargeRecord)

    async def create_recharge_record(self, user_id: int, amount: Decimal, points: int, 
                                   payment_method: str = None, exchange_code: str = None,
                                   transaction_id: str = None, remark: str = None) -> PointsRechargeRecord:
        """创建充值记录并更新用户积分"""
        async with in_transaction():
            # 创建充值记录
            recharge_record = await self.model.create(
                user_id=user_id,
                amount=amount,
                points=points,
                payment_method=payment_method,
                exchange_code=exchange_code,
                transaction_id=transaction_id,
                status="completed",
                remark=remark
            )
            
            # 更新用户积分余额
            user = await User.get(id=user_id)
            user.points_balance += points
            await user.save()
            
            return recharge_record

    async def get_user_recharge_records(self, user_id: int, limit: int = 20, offset: int = 0) -> List[PointsRechargeRecord]:
        """获取用户充值记录"""
        return await self.model.filter(user_id=user_id).order_by("-created_at").limit(limit).offset(offset)

    async def get_user_recharge_stats(self, user_id: int) -> dict:
        """获取用户充值统计"""
        records = await self.model.filter(user_id=user_id, status="completed")
        total_amount = sum(float(record.amount) for record in records)
        total_points = sum(record.points for record in records)
        return {
            "total_amount": total_amount,
            "total_points": total_points,
            "total_records": len(records)
        }


class PointsUsageController(CRUDBase[PointsUsageRecord, PointsUsageCreate, PointsUsageUpdate]):
    def __init__(self):
        super().__init__(model=PointsUsageRecord)

    async def create_usage_record(self, user_id: int, points: int, usage_type: str,
                                description: str, related_id: int = None, remark: str = None) -> PointsUsageRecord:
        """创建使用记录并扣除用户积分"""
        async with in_transaction():
            # 检查用户积分余额
            user = await User.get(id=user_id)
            if user.points_balance < points:
                raise HTTPException(status_code=400, detail="积分余额不足")
            
            # 创建使用记录
            usage_record = await self.model.create(
                user_id=user_id,
                points=points,
                usage_type=usage_type,
                description=description,
                related_id=related_id,
                remark=remark
            )
            
            # 扣除用户积分
            user.points_balance -= points
            await user.save()
            
            return usage_record

    async def get_user_usage_records(self, user_id: int, limit: int = 20, offset: int = 0) -> List[PointsUsageRecord]:
        """获取用户使用记录"""
        return await self.model.filter(user_id=user_id).order_by("-created_at").limit(limit).offset(offset)

    async def get_user_usage_stats(self, user_id: int) -> dict:
        """获取用户使用统计"""
        records = await self.model.filter(user_id=user_id)
        total_points = sum(record.points for record in records)
        return {
            "total_points": total_points,
            "total_records": len(records)
        }


class ExchangeCodeController(CRUDBase[ExchangeCode, ExchangeCodeCreate, ExchangeCodeUpdate]):
    def __init__(self):
        super().__init__(model=ExchangeCode)

    async def use_exchange_code(self, code: str, user_id: int) -> dict:
        """使用兑换码"""
        async with in_transaction():
            # 查找兑换码
            exchange_code = await self.model.filter(code=code).first()
            if not exchange_code:
                raise HTTPException(status_code=404, detail="兑换码不存在")
            
            # 检查兑换码状态
            if exchange_code.is_used:
                raise HTTPException(status_code=400, detail="兑换码已被使用")
            
            # 检查是否过期
            from datetime import timezone
            now = datetime.now(timezone.utc)
            if exchange_code.expires_at and exchange_code.expires_at < now:
                raise HTTPException(status_code=400, detail="兑换码已过期")
            
            # 标记兑换码为已使用
            exchange_code.is_used = True
            exchange_code.used_by_id = user_id
            exchange_code.used_at = datetime.now(timezone.utc)
            await exchange_code.save()
            
            # 创建充值记录
            recharge_controller = PointsRechargeController()
            await recharge_controller.create_recharge_record(
                user_id=user_id,
                amount=Decimal("0.00"),  # 兑换码充值金额为0
                points=exchange_code.points,
                payment_method="exchange_code",
                exchange_code=code,
                remark=f"使用兑换码 {code} 获得积分"
            )
            
            return {
                "points": exchange_code.points,
                "message": f"成功兑换 {exchange_code.points} 积分"
            }

    async def create_exchange_code(self, code: str, points: int, expires_at: datetime = None,
                                 created_by: int = None, remark: str = None) -> ExchangeCode:
        """创建兑换码"""
        # 检查兑换码是否已存在
        existing_code = await self.model.filter(code=code).first()
        if existing_code:
            raise HTTPException(status_code=400, detail="兑换码已存在")
        
        return await self.model.create(
            code=code,
            points=points,
            expires_at=expires_at,
            created_by_id=created_by,
            remark=remark
        )


# 创建控制器实例
points_recharge_controller = PointsRechargeController()
points_usage_controller = PointsUsageController()
exchange_code_controller = ExchangeCodeController()
