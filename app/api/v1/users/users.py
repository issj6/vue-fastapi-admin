import logging
from typing import Optional

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
    AgentPermissionChecker,
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


@router.get("/list", summary="查看普通用户列表", dependencies=[DependAuth])
async def list_user(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    username: str = Query("", description="用户名称，用于搜索"),
    email: str = Query("", description="邮箱地址"),
):
    """
    查看普通用户列表
    - 只显示 user_level = 99 的普通用户
    - 管理员特权：可以查看所有普通用户
    """
    current_user_id = CTX_USER_ID.get()
    current_user = await User.filter(id=current_user_id).first()

    q = Q()
    if username:
        q &= Q(username__contains=username)
    if email:
        q &= Q(email__contains=email)

    # 过滤普通用户：通过角色的user_level = 99（排除代理用户）
    # 注意：这里需要通过JOIN查询来过滤，暂时先获取所有用户再过滤

    # 权限控制：基于角色的分级代理系统
    if not current_user.is_superuser:
        # 检查用户是否有查看用户列表权限（查看所有用户）
        has_user_list_permission = await check_user_list_permission(current_user_id)

        if has_user_list_permission:
            # 有查看用户列表权限，可以查看所有普通用户（通常只给管理员）
            pass  # 不添加额外过滤条件
        else:
            # 检查用户是否有查看下级用户权限
            has_subordinate_permission = await check_subordinate_permission(current_user_id)

            if has_subordinate_permission:
                # 只显示下级普通用户
                subordinate_ids = await get_subordinate_user_ids(current_user_id)
                if subordinate_ids:
                    q &= Q(id__in=subordinate_ids)
                else:
                    # 没有下级用户，返回空列表
                    return SuccessExtra(data=[], total=0, page=page, page_size=page_size)
            else:
                # 没有权限查看其他用户，检查自己是否是普通用户
                current_user_roles = await current_user.roles.all()
                current_user_level = 99  # 默认层级

                for role in current_user_roles:
                    if role.user_level < current_user_level:
                        current_user_level = role.user_level

                if current_user_level == 99:
                    # 自己是普通用户，可以查看自己
                    q &= Q(id=current_user_id)
                else:
                    # 自己是代理用户，不能查看普通用户列表
                    return SuccessExtra(data=[], total=0, page=page, page_size=page_size)

    # 获取所有符合条件的用户
    total_users, all_user_objs = await user_controller.list(page=1, page_size=10000, search=q)

    # 过滤普通用户（user_level = 99）
    filtered_users = []
    for user in all_user_objs:
        user_roles = await user.roles.all()
        min_level = 99  # 默认层级
        for role in user_roles:
            if role.user_level < min_level:
                min_level = role.user_level

        # 只保留普通用户（层级99）
        if min_level == 99:
            filtered_users.append(user)

    # 手动分页
    total = len(filtered_users)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_users = filtered_users[start_idx:end_idx]

    # 为每个用户添加计算出的层级信息
    data = []
    for obj in paginated_users:
        user_dict = await obj.to_dict(m2m=True, exclude_fields=["password"])

        # 计算用户的最小层级（权限最高）
        user_roles = await obj.roles.all()
        min_level = 99  # 默认层级
        for role in user_roles:
            if role.user_level < min_level:
                min_level = role.user_level

        user_dict['user_level'] = min_level
        data.append(user_dict)

    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/agents", summary="查看代理用户列表", dependencies=[DependAuth])
async def list_agent_users(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    username: str = Query("", description="用户名称，用于搜索"),
    email: str = Query("", description="邮箱地址"),
):
    """
    查看代理用户列表
    - 显示 user_level < 99 且 user_level > 当前用户层级 的用户
    - 管理员特权：可以查看所有层级的代理用户
    """
    current_user_id = CTX_USER_ID.get()
    current_user = await User.filter(id=current_user_id).first()

    # 权限检查：是否有查看下级用户权限
    has_permission = await check_view_subordinate_users(current_user_id)
    if not has_permission:
        return Fail(code=403, msg="没有查看代理用户的权限")

    q = Q()
    if username:
        q &= Q(username__contains=username)
    if email:
        q &= Q(email__contains=email)

    # 过滤代理用户：通过角色的user_level < 99（排除普通用户）
    # 注意：这里需要通过JOIN查询来过滤，暂时先获取所有用户再过滤

    # 权限控制：基于角色的分级代理系统
    if not current_user.is_superuser:
        # 获取当前用户的层级
        current_user_roles = await current_user.roles.all()
        current_user_level = 99  # 默认层级

        for role in current_user_roles:
            if role.user_level < current_user_level:
                current_user_level = role.user_level

        # 只能查看层级比自己低的代理用户（在后续过滤中处理）

        # 检查用户是否有查看用户列表权限（查看所有用户）
        has_user_list_permission = await check_user_list_permission(current_user_id)

        if not has_user_list_permission:
            # 检查用户是否有查看下级用户权限
            has_subordinate_permission = await check_subordinate_permission(current_user_id)

            if has_subordinate_permission:
                # 只显示下级用户
                subordinate_ids = await get_subordinate_user_ids(current_user_id)
                if subordinate_ids:
                    q &= Q(id__in=subordinate_ids)
                else:
                    # 没有下级用户，返回空列表
                    return SuccessExtra(data=[], total=0, page=page, page_size=page_size)
            else:
                # 没有权限查看其他用户，返回空列表
                return SuccessExtra(data=[], total=0, page=page, page_size=page_size)

    # 获取所有符合条件的用户
    total_users, all_user_objs = await user_controller.list(page=1, page_size=10000, search=q)

    # 过滤代理用户（user_level < 99）
    filtered_users = []
    for user in all_user_objs:
        user_roles = await user.roles.all()
        min_level = 99  # 默认层级
        for role in user_roles:
            if role.user_level < min_level:
                min_level = role.user_level

        # 只保留代理用户（层级 < 99）
        if min_level < 99:
            # 如果不是超级管理员，还需要检查层级权限
            if not current_user.is_superuser and min_level <= current_user_level:
                continue  # 跳过层级不符合的用户
            filtered_users.append(user)

    # 手动分页
    total = len(filtered_users)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_users = filtered_users[start_idx:end_idx]

    # 为每个用户添加计算出的层级信息
    data = []
    for obj in paginated_users:
        user_dict = await obj.to_dict(m2m=True, exclude_fields=["password"])

        # 计算用户的最小层级（权限最高）
        user_roles = await obj.roles.all()
        min_level = 99  # 默认层级
        for role in user_roles:
            if role.user_level < min_level:
                min_level = role.user_level

        user_dict['user_level'] = min_level
        data.append(user_dict)

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
                # 非超级管理员需要检查层级权限
                user_roles = await current_user.roles.all()

                # 获取当前用户的最小层级（权限最高）
                current_user_level = min([role.user_level for role in user_roles], default=99)

                # 获取当前用户的代理权限
                current_user_permissions = set()
                can_create_agent = False
                has_create_user_permission = False

                for role in user_roles:
                    if role.is_agent_role and role.agent_permissions:
                        current_user_permissions.update(role.agent_permissions)
                        if "CREATE_SUBORDINATE_AGENT" in role.agent_permissions:
                            can_create_agent = True
                        if "CREATE_USER" in role.agent_permissions:
                            has_create_user_permission = True

                logger.info(f"用户 {current_user.username} 层级: {current_user_level}, 可创建代理: {can_create_agent}, 可创建用户: {has_create_user_permission}")

                # 验证每个要分配的角色
                for role in target_roles:
                    if role.name == "管理员":
                        logger.warning(f"用户 {current_user_id} 尝试创建管理员用户")
                        return Fail(code=403, msg="无权创建管理员用户")
                    elif role.name == "普通用户":
                        # 检查是否有创建普通用户的权限
                        if not has_create_user_permission:
                            logger.warning(f"用户 {current_user_id} 无CREATE_USER权限，无法创建普通用户")
                            return Fail(code=403, msg="无权创建普通用户")
                        logger.info(f"  ✅ 允许创建普通用户")
                    elif role.is_agent_role:
                        if not can_create_agent:
                            logger.warning(f"用户 {current_user_id} 无权创建代理角色用户: {role.name}")
                            return Fail(code=403, msg=f"无权创建代理角色用户: {role.name}")

                        # 基于层级数字进行权限控制：只能创建层级数字大于自己的角色
                        if role.user_level <= current_user_level:
                            logger.warning(f"用户 {current_user_id} 层级权限不足，无法创建角色: {role.name} (层级 {role.user_level} <= {current_user_level})")
                            return Fail(code=403, msg=f"层级权限不足，无法创建角色: {role.name}")

                        logger.info(f"  ✅ 允许创建 {role.name} (层级 {role.user_level} > {current_user_level})")
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

    # 检查是否是用户更新自己的个人信息
    is_self_update = (current_user_id == user_in.id)

    # 如果是用户更新自己的信息，只允许更新特定字段
    if is_self_update:
        # 获取当前用户信息
        current_user = await User.filter(id=current_user_id).first()

        # 超级管理员可以修改自己的所有信息
        if not current_user.is_superuser:
            allowed_self_fields = ['username', 'email', 'school', 'major']
            # 检查是否只更新了允许的字段
            for field in ['is_active', 'role_ids', 'parent_user_id', 'points_balance', 'is_superuser']:
                if hasattr(user_in, field) and getattr(user_in, field) is not None:
                    old_value = getattr(original_user, field, None)
                    new_value = getattr(user_in, field)
                    if field == 'role_ids':
                        current_role_ids = [role.id for role in await original_user.roles.all()]
                        if set(new_value or []) != set(current_role_ids):
                            return Fail(code=403, msg="不能修改自己的角色权限")
                    elif new_value != old_value:
                        return Fail(code=403, msg=f"不能修改{field}字段")

        # 允许用户更新自己的基本信息
        user = await user_controller.update_user_with_validation(user_id=user_in.id, obj_in=user_in)
        return Success(msg="个人信息更新成功")

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

    # 编辑用户时不允许修改角色，只有创建时才设置角色
    # 如果需要修改角色，应该通过专门的角色管理功能
    # await user_controller.update_roles(user, user_in.role_ids)  # 注释掉角色更新

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
    current_user_id = CTX_USER_ID.get()

    # 权限检查：是否有修改下级用户权限（与修改用户信息共用权限）
    has_permission = await AgentPermissionChecker.can_manage_user(
        current_user_id, user_id, AgentPermission.MODIFY_SUBORDINATE_USERS
    )
    if not has_permission:
        return Fail(code=403, msg="权限不足，无法重置该用户密码")

    new_password = await user_controller.reset_password(user_id)
    return Success(data={"new_password": new_password}, msg="密码重置成功")


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


@router.post("/add_points", summary="积分划转（给用户增加积分）", dependencies=[DependAuth])
async def add_user_points(
    user_id: int = Body(..., description="用户ID"),
    points: int = Body(..., description="积分数量"),
    description: Optional[str] = Body(None, description="划转描述"),
    remark: Optional[str] = Body(None, description="备注")
):
    """积分划转功能：从当前用户划转积分给目标用户"""
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
        # 使用积分划转功能
        transfer_result = await user_controller.transfer_points_to_user(
            from_user_id=current_user_id,
            to_user_id=user_id,
            points=points,
            description=description,
            remark=remark
        )

        return Success(
            data={
                "transfer_id": transfer_result["transfer_id"],
                "from_user_id": transfer_result["from_user_id"],
                "to_user_id": transfer_result["to_user_id"],
                "points": transfer_result["points"],
                "from_user_balance": transfer_result["from_user_balance"],
                "to_user_balance": transfer_result["to_user_balance"]
            },
            msg=f"成功划转 {points} 积分给用户 {transfer_result['to_username']}"
        )
    except Exception as e:
        return Fail(code=400, msg=str(e))


@router.post("/deduct_points", summary="扣除用户积分", dependencies=[DependAuth])
async def deduct_user_points(
    user_id: int = Body(..., description="用户ID"),
    points: int = Body(..., description="积分数量"),
    description: Optional[str] = Body(None, description="扣除原因"),
    remark: Optional[str] = Body(None, description="备注")
):
    """扣除用户积分并创建使用记录"""
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
        # 导入积分使用控制器
        from app.controllers.points import points_usage_controller

        # 获取用户信息
        target_user = await User.filter(id=user_id).first()
        if not target_user:
            return Fail(code=404, msg="用户不存在")

        current_user = await User.filter(id=current_user_id).first()

        # 创建积分使用记录并扣除积分
        usage_description = description or f"管理员{current_user.username}扣除积分"
        usage_remark = remark or f"由用户ID:{current_user_id}执行的积分扣除操作"

        usage_record = await points_usage_controller.create_usage_record(
            user_id=user_id,
            points=points,
            usage_type="admin_deduction",
            description=usage_description,
            related_id=current_user_id,  # 关联执行操作的管理员ID
            remark=usage_remark
        )

        # 获取更新后的用户信息
        updated_user = await User.filter(id=user_id).first()

        return Success(
            data={
                "user_id": updated_user.id,
                "points_balance": updated_user.points_balance,
                "usage_record_id": usage_record.id,
                "deducted_points": points
            },
            msg=f"成功扣除 {points} 积分"
        )
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
