import logging

from fastapi import APIRouter, Body, Query
from tortoise.expressions import Q

from app.controllers.user import user_controller
from app.core.ctx import CTX_USER_ID
from app.core.dependency import DependAuth
from app.models.admin import User, Role, Api
from app.models.enums import PermissionType, AgentPermission
from app.schemas.base import Fail, Success, SuccessExtra
from app.schemas.users import *
from app.utils.invitation_code import get_subordinate_user_ids
from app.core.agent_permissions import (
    check_view_subordinate_users,
    check_create_user,
    check_modify_subordinate_users,
    check_manage_points,
    check_delete_user,
    check_disable_user,
    AgentPermissionChecker
)


logger = logging.getLogger(__name__)

router = APIRouter()


async def check_subordinate_permission(user_id: int) -> bool:
    """检查用户是否有查看下级用户的权限 - 使用新的代理权限系统"""
    return await check_view_subordinate_users(user_id)


async def check_user_list_permission(user_id: int) -> bool:
    """检查用户是否有查看用户列表的权限（查看所有用户）"""
    user = await User.filter(id=user_id).first()
    if not user:
        return False

    # 超级管理员默认有所有权限
    if user.is_superuser:
        return True

    # 检查用户角色是否有管理员权限（通过角色名称判断）
    roles = await user.roles.all()
    for role in roles:
        # 只有管理员角色才有查看所有用户的权限
        if role.name in ["管理员", "系统管理员"]:
            return True

    return False


@router.get("/list", summary="查看用户列表", dependencies=[DependAuth])
async def list_user(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    username: str = Query("", description="用户名称，用于搜索"),
    email: str = Query("", description="邮箱地址"),
):
    current_user_id = CTX_USER_ID.get()
    current_user = await User.filter(id=current_user_id).first()

    q = Q()
    if username:
        q &= Q(username__contains=username)
    if email:
        q &= Q(email__contains=email)

    # 权限控制：基于角色的分级代理系统
    if not current_user.is_superuser:
        # 检查用户是否有查看用户列表权限（查看所有用户）
        has_user_list_permission = await check_user_list_permission(current_user_id)

        if has_user_list_permission:
            # 有查看用户列表权限，可以查看所有用户（通常只给管理员）
            pass  # 不添加额外过滤条件
        else:
            # 检查用户是否有查看下级用户权限
            has_subordinate_permission = await check_subordinate_permission(current_user_id)

            if has_subordinate_permission:
                # 只显示下级用户和自己
                subordinate_ids = await get_subordinate_user_ids(current_user_id)
                subordinate_ids.append(current_user_id)  # 包含自己
                q &= Q(id__in=subordinate_ids)
            else:
                # 没有权限查看其他用户，只能查看自己
                q &= Q(id=current_user_id)

    total, user_objs = await user_controller.list(page=page, page_size=page_size, search=q)
    data = [await obj.to_dict(m2m=True, exclude_fields=["password"]) for obj in user_objs]

    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/get", summary="查看用户")
async def get_user(
    user_id: int = Query(..., description="用户ID"),
):
    user_obj = await user_controller.get(id=user_id)
    user_dict = await user_obj.to_dict(exclude_fields=["password"])
    return Success(data=user_dict)


@router.post("/create", summary="创建用户", dependencies=[DependAuth])
async def create_user(
    user_in: UserCreate,
):
    try:
        current_user_id = CTX_USER_ID.get()
        logger.info(f"用户 {current_user_id} 尝试创建用户: {user_in.username}")

        # 权限检查：是否有创建用户权限
        has_permission = await check_create_user(current_user_id)
        if not has_permission:
            logger.warning(f"用户 {current_user_id} 没有创建用户权限")
            return Fail(code=403, msg="没有创建用户的权限")

        # 获取当前用户信息
        current_user = await User.filter(id=current_user_id).first()
        if not current_user:
            return Fail(code=403, msg="用户不存在")

        # 超级管理员权限检查：只有超级管理员才能设置超级管理员权限
        if user_in.is_superuser:
            if not current_user.is_superuser:
                logger.warning(f"用户 {current_user_id} 无权设置超级管理员")
                return Fail(code=403, msg="只有超级管理员才能创建超级管理员用户")

        # 角色创建权限验证 - 角色必须指定
        if not user_in.role_ids or len(user_in.role_ids) == 0:
            logger.warning(f"用户 {current_user_id} 尝试创建用户但未指定角色")
            return Fail(code=400, msg="必须为新用户指定角色")

        if user_in.role_ids:
            # 获取要分配的角色
            target_roles = await Role.filter(id__in=user_in.role_ids).all()

            if current_user.is_superuser:
                # 超级管理员可以创建除管理员外的所有角色
                for role in target_roles:
                    if role.name == "管理员":
                        logger.warning(f"超级管理员尝试创建管理员角色用户")
                        return Fail(code=403, msg="不能创建管理员角色用户")
            else:
                # 非超级管理员需要检查代理权限
                user_roles = await current_user.roles.all()

                # 获取当前用户的代理权限
                current_user_permissions = set()
                can_create_agent = False
                for role in user_roles:
                    if role.is_agent_role and role.agent_permissions:
                        current_user_permissions.update(role.agent_permissions)
                        if "CREATE_SUBORDINATE_AGENT" in role.agent_permissions:
                            can_create_agent = True

                # 验证每个要分配的角色
                for role in target_roles:
                    if role.name == "管理员":
                        logger.warning(f"用户 {current_user_id} 尝试创建管理员用户")
                        return Fail(code=403, msg="无权创建管理员用户")
                    elif role.name == "普通用户":
                        # 普通用户角色总是可以创建
                        continue
                    elif role.is_agent_role:
                        if not can_create_agent:
                            logger.warning(f"用户 {current_user_id} 无权创建代理角色用户: {role.name}")
                            return Fail(code=403, msg=f"无权创建代理角色用户: {role.name}")

                        # 检查是否能创建这个特定的代理角色
                        target_permissions = set(role.agent_permissions or [])

                        # 只能创建权限严格少于自己的角色，且目标权限必须是自己权限的子集
                        if not (len(target_permissions) < len(current_user_permissions) and
                                target_permissions.issubset(current_user_permissions)):
                            logger.warning(f"用户 {current_user_id} 权限不足，无法创建角色: {role.name}")
                            return Fail(code=403, msg=f"权限不足，无法创建角色: {role.name}")
                    else:
                        logger.warning(f"用户 {current_user_id} 尝试创建未知角色: {role.name}")
                        return Fail(code=403, msg=f"无权创建角色: {role.name}")

        user = await user_controller.get_by_email(user_in.email)
        if user:
            logger.warning(f"邮箱 {user_in.email} 已存在")
            return Fail(code=400, msg="The user with this email already exists in the system.")

        logger.info(f"开始创建用户: {user_in.username}")
        new_user = await user_controller.create_user(obj_in=user_in)
        logger.info(f"用户创建成功: {new_user.username} (ID: {new_user.id})")

        # 设置上下级关系：非超级管理员创建的用户需要设置parent_user_id
        if not current_user.is_superuser:
            new_user.parent_user_id = current_user_id
            await new_user.save()
            logger.info(f"设置上下级关系: {new_user.username} 的上级为 {current_user.username} (ID: {current_user_id})")

        logger.info(f"开始分配角色: {user_in.role_ids}")
        await user_controller.update_roles(new_user, user_in.role_ids)
        logger.info(f"角色分配成功")

        return Success(msg="Created Successfully")
    except Exception as e:
        logger.error(f"创建用户失败: {str(e)}", exc_info=True)
        return Fail(code=500, msg=f"创建用户失败: {str(e)}")


@router.post("/update", summary="更新用户")
async def update_user(
    user_in: UserUpdate,
):
    current_user_id = CTX_USER_ID.get()

    # 获取原用户数据以判断更新类型
    original_user = await User.filter(id=user_in.id).first()
    if not original_user:
        return Fail(code=404, msg="用户不存在")

    # 检查是否是禁用/启用操作（只有is_active字段发生变化）
    is_status_change = (
        hasattr(user_in, 'is_active') and
        user_in.is_active != original_user.is_active
    )

    # 检查是否有其他实质性字段变化
    significant_fields = ['email', 'username', 'role_ids', 'parent_user_id', 'school', 'major', 'points_balance']
    has_other_changes = False

    logger.info(f"用户更新操作分析 - 用户ID: {user_in.id}, is_active变化: {is_status_change}")

    for field in significant_fields:
        if hasattr(user_in, field):
            new_value = getattr(user_in, field)
            old_value = getattr(original_user, field, None)

            # 特殊处理role_ids字段
            if field == 'role_ids':
                current_role_ids = [role.id for role in await original_user.roles.all()]
                if set(new_value or []) != set(current_role_ids):
                    logger.info(f"字段 {field} 发生变化: {current_role_ids} -> {new_value}")
                    has_other_changes = True
                    break
            elif new_value != old_value:
                logger.info(f"字段 {field} 发生变化: {old_value} -> {new_value}")
                has_other_changes = True
                break

    logger.info(f"操作类型判断 - 状态变化: {is_status_change}, 其他变化: {has_other_changes}")

    if is_status_change and not has_other_changes:
        # 纯禁用/启用操作需要DISABLE_USER权限
        logger.info("判定为禁用/启用操作，检查DISABLE_USER权限")
        has_permission = await AgentPermissionChecker.can_manage_user(
            current_user_id, user_in.id, AgentPermission.DISABLE_USER
        )
        if not has_permission:
            logger.warning(f"用户 {current_user_id} 没有DISABLE_USER权限")
            return Fail(code=403, msg="权限不足，无法禁用/启用该用户")
    else:
        # 其他修改操作需要MODIFY_SUBORDINATE_USERS权限
        logger.info("判定为修改用户信息操作，检查MODIFY_SUBORDINATE_USERS权限")
        has_permission = await AgentPermissionChecker.can_manage_user(
            current_user_id, user_in.id, AgentPermission.MODIFY_SUBORDINATE_USERS
        )
        if not has_permission:
            logger.warning(f"用户 {current_user_id} 没有MODIFY_SUBORDINATE_USERS权限")
            return Fail(code=403, msg="权限不足，无法修改该用户信息")

    user = await user_controller.update_user_with_validation(user_id=user_in.id, obj_in=user_in)
    await user_controller.update_roles(user, user_in.role_ids)
    return Success(msg="更新成功")


@router.delete("/delete", summary="删除用户")
async def delete_user(
    user_id: int = Query(..., description="用户ID"),
):
    current_user_id = CTX_USER_ID.get()

    # 权限检查：是否有删除用户权限
    has_permission = await AgentPermissionChecker.can_manage_user(
        current_user_id, user_id, AgentPermission.DELETE_USER
    )
    if not has_permission:
        return Fail(code=403, msg="没有删除该用户的权限")

    await user_controller.remove(id=user_id)
    return Success(msg="Deleted Successfully")


@router.post("/reset_password", summary="重置密码")
async def reset_password(user_id: int = Body(..., description="用户ID", embed=True)):
    await user_controller.reset_password(user_id)
    return Success(msg="密码已重置为123456")


@router.get("/subordinates", summary="查看下级用户", dependencies=[DependAuth])
async def get_subordinate_users(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
):
    """获取当前用户的下级用户列表"""
    current_user_id = CTX_USER_ID.get()

    # 检查权限
    has_permission = await check_subordinate_permission(current_user_id)
    if not has_permission:
        return Fail(code=403, msg="没有查看下级用户的权限")

    # 获取下级用户
    subordinate_ids = await get_subordinate_user_ids(current_user_id)
    if not subordinate_ids:
        return SuccessExtra(data=[], total=0, page=page, page_size=page_size)

    q = Q(id__in=subordinate_ids)
    total, user_objs = await user_controller.list(page=page, page_size=page_size, search=q)
    data = [await obj.to_dict(m2m=True, exclude_fields=["password"]) for obj in user_objs]

    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.post("/add_points", summary="增加用户积分", dependencies=[DependAuth])
async def add_user_points(
    user_id: int = Body(..., description="用户ID"),
    points: int = Body(..., description="积分数量"),
):
    """为用户增加积分"""
    current_user_id = CTX_USER_ID.get()

    # 权限检查：是否有积分管理权限
    has_permission = await AgentPermissionChecker.can_manage_user(
        current_user_id, user_id, AgentPermission.MANAGE_POINTS
    )
    if not has_permission:
        return Fail(code=403, msg="没有管理该用户积分的权限")

    if points <= 0:
        return Fail(code=400, msg="积分数量必须大于0")

    user = await user_controller.add_points(user_id, points)
    return Success(data={"user_id": user.id, "points_balance": user.points_balance}, msg="积分增加成功")


@router.post("/deduct_points", summary="扣除用户积分", dependencies=[DependAuth])
async def deduct_user_points(
    user_id: int = Body(..., description="用户ID"),
    points: int = Body(..., description="积分数量"),
):
    """扣除用户积分"""
    current_user_id = CTX_USER_ID.get()

    # 权限检查：是否有积分管理权限
    has_permission = await AgentPermissionChecker.can_manage_user(
        current_user_id, user_id, AgentPermission.MANAGE_POINTS
    )
    if not has_permission:
        return Fail(code=403, msg="没有管理该用户积分的权限")

    if points <= 0:
        return Fail(code=400, msg="积分数量必须大于0")

    try:
        user = await user_controller.deduct_points(user_id, points)
        return Success(data={"user_id": user.id, "points_balance": user.points_balance}, msg="积分扣除成功")
    except Exception as e:
        return Fail(code=400, msg=str(e))


@router.get("/invitation_info", summary="获取邀请信息", dependencies=[DependAuth])
async def get_invitation_info():
    """获取当前用户的邀请码和邀请统计"""
    current_user_id = CTX_USER_ID.get()
    current_user = await User.filter(id=current_user_id).first()

    # 统计邀请的用户数量
    invited_count = await User.filter(parent_user_id=current_user_id).count()

    return Success(data={
        "invitation_code": current_user.invitation_code,
        "invited_count": invited_count,
        "points_balance": current_user.points_balance
    })
