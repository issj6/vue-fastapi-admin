from datetime import datetime
from typing import List, Optional
from decimal import Decimal

from fastapi.exceptions import HTTPException
from tortoise.transactions import in_transaction
from tortoise.expressions import Q

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

    async def get_user_usage_records(
        self,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
        usage_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> tuple[List[PointsUsageRecord], int]:
        """获取用户使用记录"""
        query = self.model.filter(user_id=user_id)

        # 使用类型筛选
        if usage_type:
            query = query.filter(usage_type=usage_type)

        # 时间范围筛选
        if start_date:
            query = query.filter(created_at__gte=start_date)
        if end_date:
            query = query.filter(created_at__lte=end_date)

        # 获取总数
        total = await query.count()

        # 获取记录
        records = await query.order_by("-created_at").limit(limit).offset(offset)

        return records, total

    async def get_user_usage_stats(self, user_id: int) -> dict:
        """获取用户使用统计"""
        records = await self.model.filter(user_id=user_id)
        total_points = sum(record.points for record in records)
        return {
            "total_points": total_points,
            "total_records": len(records)
        }

    async def get_admin_usage_records(
        self,
        limit: int = 20,
        offset: int = 0,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        usage_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> tuple[List[PointsUsageRecord], int]:
        """
        管理员获取积分使用记录（支持筛选）

        Args:
            limit: 每页数量
            offset: 偏移量
            user_id: 用户ID筛选
            username: 用户名筛选
            start_date: 开始时间
            end_date: 结束时间

        Returns:
            tuple: (记录列表, 总数)
        """
        # 构建查询条件
        query = self.model.all()

        # 用户筛选
        if user_id:
            query = query.filter(user_id=user_id)
        elif username:
            # 通过用户名查找用户ID
            user = await User.filter(username=username).first()
            if user:
                query = query.filter(user_id=user.id)
            else:
                # 用户不存在，返回空结果
                return [], 0

        # 使用类型筛选
        if usage_type:
            query = query.filter(usage_type=usage_type)

        # 时间范围筛选
        if start_date:
            query = query.filter(created_at__gte=start_date)
        if end_date:
            query = query.filter(created_at__lte=end_date)

        # 获取总数
        total = await query.count()

        # 获取记录（包含用户信息）
        records = await query.select_related('user').order_by('-created_at').limit(limit).offset(offset)

        return records, total


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


class PointsTransferController:
    """积分划转控制器"""

    def __init__(self):
        self.recharge_controller = PointsRechargeController()
        self.usage_controller = PointsUsageController()

    async def transfer_points(self, from_user_id: int, to_user_id: int, points: int,
                            description: str = None, remark: str = None) -> dict:
        """
        积分划转功能

        Args:
            from_user_id: 划转方用户ID
            to_user_id: 接收方用户ID
            points: 划转积分数量
            description: 划转描述
            remark: 备注

        Returns:
            dict: 划转结果信息
        """
        if points <= 0:
            raise HTTPException(status_code=400, detail="划转积分数量必须大于0")

        if from_user_id == to_user_id:
            raise HTTPException(status_code=400, detail="不能给自己划转积分")

        async with in_transaction():
            # 获取用户信息
            from_user = await User.get(id=from_user_id)
            to_user = await User.get(id=to_user_id)

            # 检查划转方余额
            if from_user.points_balance < points:
                raise HTTPException(status_code=400, detail="积分余额不足")

            # 生成划转ID用于关联记录
            import uuid
            transfer_id = int(uuid.uuid4().hex[:8], 16) % 2147483647  # 确保是32位整数

            # 创建划转方的使用记录
            usage_description = description or f"给用户{to_user.username}划转积分"
            usage_record = await self.usage_controller.model.create(
                user_id=from_user_id,
                points=points,
                usage_type="transfer_to_others",
                description=usage_description,
                related_id=transfer_id,
                remark=remark or f"积分划转给用户ID:{to_user_id}"
            )

            # 扣除划转方积分
            from_user.points_balance -= points
            await from_user.save()

            # 创建接收方的充值记录
            recharge_description = f"从用户{from_user.username}接收积分划转"
            recharge_record = await self.recharge_controller.model.create(
                user_id=to_user_id,
                amount=Decimal("0.00"),  # 划转不涉及金额
                points=points,
                payment_method="transfer",
                transaction_id=f"TRANSFER_{transfer_id}",
                status="completed",
                remark=remark or f"从用户ID:{from_user_id}接收积分划转"
            )

            # 增加接收方积分
            to_user.points_balance += points
            await to_user.save()

            return {
                "transfer_id": transfer_id,
                "from_user_id": from_user_id,
                "from_username": from_user.username,
                "to_user_id": to_user_id,
                "to_username": to_user.username,
                "points": points,
                "usage_record_id": usage_record.id,
                "recharge_record_id": recharge_record.id,
                "from_user_balance": from_user.points_balance,
                "to_user_balance": to_user.points_balance
            }


# 创建控制器实例
points_recharge_controller = PointsRechargeController()
points_usage_controller = PointsUsageController()
exchange_code_controller = ExchangeCodeController()
points_transfer_controller = PointsTransferController()
