from decimal import Decimal
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Query, HTTPException

from app.controllers.points import (
    points_recharge_controller,
    points_usage_controller,
    exchange_code_controller,
    points_transfer_controller
)
from app.controllers.user import user_controller
from app.core.ctx import CTX_USER_ID
from app.core.dependency import DependAuth
from app.core.agent_permissions import AgentPermissionChecker
from app.models.admin import User
from app.models.enums import AgentPermission
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
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    usage_type: Optional[str] = Query(None, description="使用类型筛选"),
    start_date: Optional[str] = Query(None, description="开始时间(YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束时间(YYYY-MM-DD)")
):
    """获取用户积分使用记录"""
    user_id = CTX_USER_ID.get()
    offset = (page - 1) * size

    # 解析时间参数
    start_datetime = None
    end_datetime = None
    try:
        if start_date:
            start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            end_datetime = datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return Fail(code=400, msg="时间格式错误，请使用YYYY-MM-DD格式")

    records, total = await points_usage_controller.get_user_usage_records(
        user_id,
        limit=size,
        offset=offset,
        usage_type=usage_type,
        start_date=start_datetime,
        end_date=end_datetime
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
        "total": total
    })


@router.get("/usage/admin/records", summary="管理员获取全局积分使用记录", dependencies=[DependAuth])
async def get_admin_usage_records(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    username: Optional[str] = Query(None, description="用户名筛选"),
    usage_type: Optional[str] = Query(None, description="使用类型筛选"),
    start_date: Optional[str] = Query(None, description="开始时间(YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束时间(YYYY-MM-DD)")
):
    """管理员获取全局积分使用记录"""
    current_user_id = CTX_USER_ID.get()

    # 权限检查：是否有查看全局积分使用记录权限
    has_permission = await AgentPermissionChecker.check_agent_permission(
        current_user_id, AgentPermission.VIEW_GLOBAL_POINTS_USAGE
    )
    if not has_permission:
        return Fail(code=403, msg="没有查看全局积分使用记录的权限")

    # 解析时间参数
    start_datetime = None
    end_datetime = None
    try:
        if start_date:
            start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            end_datetime = datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return Fail(code=400, msg="时间格式错误，请使用YYYY-MM-DD格式")

    offset = (page - 1) * size

    # 获取记录
    records, total = await points_usage_controller.get_admin_usage_records(
        limit=size,
        offset=offset,
        user_id=user_id,
        username=username,
        usage_type=usage_type,
        start_date=start_datetime,
        end_date=end_datetime
    )

    # 转换为字典格式
    records_data = []
    for record in records:
        # 获取用户信息
        user_info = await record.user if hasattr(record, 'user') else await User.get(id=record.user_id)

        record_dict = {
            'id': record.id,
            'user_id': record.user_id,
            'username': user_info.username if user_info else "未知用户",
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
        "total": total
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


@router.post("/transfer", summary="积分划转", dependencies=[DependAuth])
async def transfer_points(
    to_user_id: int = Query(..., description="接收方用户ID"),
    points: int = Query(..., description="划转积分数量"),
    description: Optional[str] = Query(None, description="划转描述"),
    remark: Optional[str] = Query(None, description="备注")
):
    """积分划转功能"""
    from_user_id = CTX_USER_ID.get()

    # 权限检查：是否有积分管理权限
    has_permission = await AgentPermissionChecker.can_manage_user(
        from_user_id, to_user_id, AgentPermission.MANAGE_POINTS
    )
    if not has_permission:
        return Fail(code=403, msg="没有给该用户划转积分的权限")

    if points <= 0:
        return Fail(code=400, msg="划转积分数量必须大于0")

    try:
        transfer_result = await points_transfer_controller.transfer_points(
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            points=points,
            description=description,
            remark=remark
        )

        return Success(
            data=transfer_result,
            msg=f"成功划转 {points} 积分给用户 {transfer_result['to_username']}"
        )
    except HTTPException as e:
        return Fail(code=e.status_code, msg=e.detail)
    except Exception as e:
        return Fail(code=500, msg=f"划转失败: {str(e)}")
