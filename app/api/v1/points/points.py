from decimal import Decimal
from typing import List

from fastapi import APIRouter, Query, HTTPException

from app.controllers.points import (
    points_recharge_controller, 
    points_usage_controller, 
    exchange_code_controller
)
from app.controllers.user import user_controller
from app.core.ctx import CTX_USER_ID
from app.core.dependency import DependAuth
from app.models.admin import User
from app.schemas.base import Success, Fail
from app.schemas.points import (
    ExchangeCodeUseRequest, RechargeRequest, 
    PointsRechargeOut, PointsUsageOut,
    PointsStatsOut, PointsInfoOut
)

router = APIRouter()


@router.get("/info", summary="获取积分信息", dependencies=[DependAuth])
async def get_points_info():
    """获取用户积分信息，包括余额、统计和最近充值记录"""
    user_id = CTX_USER_ID.get()
    
    # 获取用户信息
    user = await User.get(id=user_id)
    
    # 获取充值统计
    recharge_stats = await points_recharge_controller.get_user_recharge_stats(user_id)
    
    # 获取使用统计
    usage_stats = await points_usage_controller.get_user_usage_stats(user_id)
    
    # 获取最近充值记录
    recent_recharge_records = await points_recharge_controller.get_user_recharge_records(
        user_id, limit=10
    )
    
    # 构建统计信息
    stats = PointsStatsOut(
        current_balance=user.points_balance,
        total_recharged_amount=recharge_stats["total_amount"],
        total_recharged_points=recharge_stats["total_points"],
        total_used_points=usage_stats["total_points"],
        recharge_records_count=recharge_stats["total_records"],
        usage_records_count=usage_stats["total_records"]
    )
    
    # 转换充值记录为字典
    recharge_records_data = []
    for record in recent_recharge_records:
        record_dict = {
            'id': record.id,
            'user_id': record.user_id,
            'amount': float(record.amount),
            'points': record.points,
            'payment_method': record.payment_method,
            'exchange_code': record.exchange_code,
            'status': record.status,
            'transaction_id': record.transaction_id,
            'created_at': record.created_at.isoformat() if record.created_at else None,
            'updated_at': record.updated_at.isoformat() if record.updated_at else None,
            'remark': record.remark
        }
        recharge_records_data.append(record_dict)

    points_info_data = {
        'stats': {
            'current_balance': user.points_balance,
            'total_recharged_amount': recharge_stats["total_amount"],
            'total_recharged_points': recharge_stats["total_points"],
            'total_used_points': usage_stats["total_points"],
            'recharge_records_count': recharge_stats["total_records"],
            'usage_records_count': usage_stats["total_records"]
        },
        'recent_recharge_records': recharge_records_data,
        'exchange_rate': {'cny_to_points': 1, 'description': '1元 = 1积分'}
    }

    return Success(data=points_info_data)


@router.post("/exchange", summary="使用兑换码", dependencies=[DependAuth])
async def use_exchange_code(request: ExchangeCodeUseRequest):
    """使用兑换码兑换积分"""
    user_id = CTX_USER_ID.get()
    
    try:
        result = await exchange_code_controller.use_exchange_code(request.code, user_id)
        return Success(data=result, msg=result["message"])
    except HTTPException as e:
        return Fail(code=e.status_code, msg=e.detail)
    except Exception as e:
        return Fail(code=500, msg=f"兑换失败: {str(e)}")


@router.post("/recharge", summary="积分充值", dependencies=[DependAuth])
async def recharge_points(request: RechargeRequest):
    """积分充值（模拟支付）"""
    user_id = CTX_USER_ID.get()
    
    # 检查用户是否为代理
    user = await User.get(id=user_id)
    roles = await user.roles.all()
    role_names = [role.name for role in roles]
    
    # 检查是否为代理用户
    is_agent = any("代理" in name for name in role_names) or user.is_superuser
    if not is_agent:
        return Fail(code=403, msg="只有代理用户才能进行积分充值")
    
    # 验证支付方式
    if request.payment_method not in ["alipay", "wechat"]:
        return Fail(code=400, msg="不支持的支付方式")
    
    # 计算积分数量（1元=1积分）
    points = int(request.amount)
    
    try:
        # 模拟支付成功，创建充值记录
        import uuid
        transaction_id = f"TXN_{uuid.uuid4().hex[:16].upper()}"
        
        recharge_record = await points_recharge_controller.create_recharge_record(
            user_id=user_id,
            amount=request.amount,
            points=points,
            payment_method=request.payment_method,
            transaction_id=transaction_id,
            remark=f"通过{request.payment_method}充值"
        )
        
        return Success(
            data={
                "transaction_id": transaction_id,
                "amount": float(request.amount),
                "points": points,
                "payment_method": request.payment_method
            },
            msg=f"充值成功，获得 {points} 积分"
        )
    except Exception as e:
        return Fail(code=500, msg=f"充值失败: {str(e)}")


@router.get("/recharge/records", summary="获取充值记录", dependencies=[DependAuth])
async def get_recharge_records(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """获取用户充值记录"""
    user_id = CTX_USER_ID.get()
    offset = (page - 1) * size
    
    records = await points_recharge_controller.get_user_recharge_records(
        user_id, limit=size, offset=offset
    )

    # 转换为字典格式
    records_data = []
    for record in records:
        record_dict = {
            'id': record.id,
            'user_id': record.user_id,
            'amount': float(record.amount),
            'points': record.points,
            'payment_method': record.payment_method,
            'exchange_code': record.exchange_code,
            'status': record.status,
            'transaction_id': record.transaction_id,
            'created_at': record.created_at.isoformat() if record.created_at else None,
            'updated_at': record.updated_at.isoformat() if record.updated_at else None,
            'remark': record.remark
        }
        records_data.append(record_dict)

    return Success(data={
        "records": records_data,
        "page": page,
        "size": size,
        "total": len(records)
    })


@router.get("/usage/records", summary="获取使用记录", dependencies=[DependAuth])
async def get_usage_records(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """获取用户积分使用记录"""
    user_id = CTX_USER_ID.get()
    offset = (page - 1) * size
    
    records = await points_usage_controller.get_user_usage_records(
        user_id, limit=size, offset=offset
    )

    # 转换为字典格式
    records_data = []
    for record in records:
        record_dict = {
            'id': record.id,
            'user_id': record.user_id,
            'points': record.points,
            'usage_type': record.usage_type,
            'description': record.description,
            'related_id': record.related_id,
            'created_at': record.created_at.isoformat() if record.created_at else None,
            'remark': record.remark
        }
        records_data.append(record_dict)

    return Success(data={
        "records": records_data,
        "page": page,
        "size": size,
        "total": len(records)
    })


@router.post("/usage/create", summary="创建积分使用记录", dependencies=[DependAuth])
async def create_usage_record(
    points: int = Query(..., description="消耗积分"),
    usage_type: str = Query(..., description="使用类型"),
    description: str = Query(..., description="使用描述"),
    related_id: int = Query(None, description="关联ID")
):
    """创建积分使用记录（供系统内部调用）"""
    user_id = CTX_USER_ID.get()
    
    try:
        usage_record = await points_usage_controller.create_usage_record(
            user_id=user_id,
            points=points,
            usage_type=usage_type,
            description=description,
            related_id=related_id
        )
        
        usage_data = {
            'id': usage_record.id,
            'user_id': usage_record.user_id,
            'points': usage_record.points,
            'usage_type': usage_record.usage_type,
            'description': usage_record.description,
            'related_id': usage_record.related_id,
            'created_at': usage_record.created_at.isoformat() if usage_record.created_at else None,
            'remark': usage_record.remark
        }

        return Success(
            data=usage_data,
            msg=f"成功消耗 {points} 积分"
        )
    except HTTPException as e:
        return Fail(code=e.status_code, msg=e.detail)
    except Exception as e:
        return Fail(code=500, msg=f"操作失败: {str(e)}")
