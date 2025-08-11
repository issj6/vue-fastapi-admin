import logging

from fastapi import APIRouter, Query
from fastapi.exceptions import HTTPException
from tortoise.expressions import Q

from app.controllers import role_controller
from app.schemas.base import Success, SuccessExtra, Fail
from app.schemas.roles import *
from app.models.enums import AgentPermission
from app.core.ctx import CTX_USER_ID
from app.core.dependency import DependAuth


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/list", summary="查看角色列表", dependencies=[DependAuth])
async def list_role(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    role_name: str = Query("", description="角色名称，用于查询"),
):
    q = Q()
    if role_name:
        q = Q(name__contains=role_name)
    total, role_objs = await role_controller.list(page=page, page_size=page_size, search=q)
    data = [await obj.to_dict() for obj in role_objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/get", summary="查看角色")
async def get_role(
    role_id: int = Query(..., description="角色ID"),
):
    role_obj = await role_controller.get(id=role_id)
    return Success(data=await role_obj.to_dict())


@router.post("/create", summary="创建角色")
async def create_role(role_in: RoleCreate):
    if await role_controller.is_exist(name=role_in.name):
        raise HTTPException(
            status_code=400,
            detail="The role with this rolename already exists in the system.",
        )
    await role_controller.create(obj_in=role_in)
    return Success(msg="Created Successfully")


@router.post("/update", summary="更新角色")
async def update_role(role_in: RoleUpdate):
    await role_controller.update(id=role_in.id, obj_in=role_in)
    return Success(msg="Updated Successfully")


@router.get("/check_users", summary="检查角色关联的用户数量")
async def check_role_users(
    role_id: int = Query(..., description="角色ID"),
):
    """检查指定角色关联的用户数量"""
    from app.models.admin import User

    # 获取角色信息
    role = await role_controller.get(id=role_id)
    if not role:
        return Fail(msg="角色不存在")

    # 统计关联的用户数量
    user_count = await User.filter(roles__id=role_id).count()

    return Success(data={
        "role_id": role_id,
        "role_name": role.name,
        "user_count": user_count
    })


@router.delete("/delete", summary="删除角色")
async def delete_role(
    role_id: int = Query(..., description="角色ID"),
    force_delete: bool = Query(False, description="是否强制删除（同时删除关联用户）"),
):
    """删除角色，可选择是否同时删除关联用户"""
    from app.models.admin import User

    # 获取角色信息
    role = await role_controller.get(id=role_id)
    if not role:
        return Fail(msg="角色不存在")

    # 检查是否为系统关键角色
    if role.name in ["管理员", "普通用户"]:
        return Fail(msg="系统关键角色不能删除")

    # 统计关联的用户数量
    user_count = await User.filter(roles__id=role_id).count()

    if user_count > 0 and not force_delete:
        return Fail(
            code=400,
            msg=f"该角色关联了 {user_count} 个用户，请确认是否要同时删除这些用户",
            data={
                "role_id": role_id,
                "role_name": role.name,
                "user_count": user_count,
                "need_confirmation": True
            }
        )

    if force_delete and user_count > 0:
        # 删除关联的用户
        users_to_delete = await User.filter(roles__id=role_id).all()
        for user in users_to_delete:
            # 检查用户是否只有这一个角色
            user_role_count = await user.roles.all().count()
            if user_role_count == 1:
                # 如果用户只有这一个角色，删除用户
                await user.delete()
            else:
                # 如果用户有多个角色，只移除这个角色
                await user.roles.remove(role)

        logger.info(f"删除角色 {role.name} 时同时处理了 {user_count} 个关联用户")

    # 删除角色
    await role_controller.remove(id=role_id)

    if force_delete and user_count > 0:
        return Success(msg=f"已删除角色 '{role.name}' 及其关联的 {user_count} 个用户")
    else:
        return Success(msg="角色删除成功")


@router.get("/authorized", summary="查看角色权限")
async def get_role_authorized(id: int = Query(..., description="角色ID")):
    role_obj = await role_controller.get(id=id)
    data = await role_obj.to_dict(m2m=True)
    return Success(data=data)


@router.post("/authorized", summary="更新角色权限")
async def update_role_authorized(role_in: RoleUpdateMenusApis):
    role_obj = await role_controller.get(id=role_in.id)
    await role_controller.update_roles(role=role_obj, menu_ids=role_in.menu_ids, api_infos=role_in.api_infos)
    return Success(msg="Updated Successfully")


@router.post("/agent_permissions", summary="更新角色代理权限")
async def update_role_agent_permissions(role_in: RoleUpdateAgentPermissions):
    """更新角色的代理权限配置"""
    role_obj = await role_controller.get(id=role_in.id)
    await role_controller.update_agent_permissions(
        role=role_obj,
        agent_permissions=role_in.agent_permissions,
        is_agent_role=role_in.is_agent_role
    )
    return Success(msg="代理权限更新成功")


@router.get("/agent_permissions", summary="获取代理权限配置")
async def get_agent_permissions_config():
    """获取代理权限配置选项"""
    return Success(data={
        "permissions": AgentPermission.get_permission_descriptions(),
        "all_permissions": AgentPermission.get_all_permissions()
    })


@router.get("/agent_roles", summary="获取代理角色列表")
async def get_agent_roles():
    """获取所有代理角色"""
    roles = await role_controller.get_agent_roles()
    data = [await role.to_dict() for role in roles]
    return Success(data=data)


@router.get("/creatable", summary="获取可创建的角色列表", dependencies=[DependAuth])
async def get_creatable_roles():
    """获取当前用户可以创建的角色列表 - 基于权限和层级严格控制"""
    current_user_id = CTX_USER_ID.get()

    # 获取当前用户
    from app.models.admin import User, Role
    current_user = await User.filter(id=current_user_id).first()

    if current_user.is_superuser:
        # 超级管理员可以创建除了管理员角色外的所有角色
        all_roles = await Role.all()
        # 过滤掉管理员角色，避免创建多个管理员
        roles = [role for role in all_roles if role.name != "管理员"]
        logger.info(f"超级管理员 {current_user.username} 可创建角色: {[r.name for r in roles]}")
    else:
        # 普通用户根据权限严格控制可创建的角色
        user_roles = await current_user.roles.all()

        # 获取当前用户的最小层级（权限最高）
        current_user_level = min([role.user_level for role in user_roles], default=99)

        # 检查用户权限
        has_create_user_permission = False
        has_create_agent_permission = False

        for role in user_roles:
            if role.agent_permissions:
                if "CREATE_USER" in role.agent_permissions:
                    has_create_user_permission = True
                if "CREATE_SUBORDINATE_AGENT" in role.agent_permissions:
                    has_create_agent_permission = True

        logger.info(f"用户 {current_user.username} 层级: {current_user_level}, CREATE_USER权限: {has_create_user_permission}, CREATE_SUBORDINATE_AGENT权限: {has_create_agent_permission}")

        roles = []

        # 1. 如果有CREATE_USER权限，可以创建普通用户(层级99)
        if has_create_user_permission:
            normal_user_role = await Role.filter(user_level=99).first()
            if normal_user_role:
                roles.append(normal_user_role)
                logger.info(f"  ✅ 可创建普通用户 (层级99)")
            else:
                logger.warning(f"  ⚠️ 未找到层级99的普通用户角色")

        # 2. 如果有CREATE_SUBORDINATE_AGENT权限，只能创建自身层级+1的代理角色（前提是该角色存在）
        if has_create_agent_permission:
            target_level = current_user_level + 1

            # 查找目标层级的代理角色
            target_agent_role = await Role.filter(
                user_level=target_level,
                is_agent_role=True
            ).first()

            if target_agent_role:
                # 只有当该层级的代理角色存在时，才能创建
                roles.append(target_agent_role)
                logger.info(f"  ✅ 可创建下级代理 {target_agent_role.name} (层级{target_level})")
            else:
                # 如果不存在该层级的代理角色，则CREATE_SUBORDINATE_AGENT权限无效
                logger.info(f"  ❌ 层级{target_level}的代理角色不存在，CREATE_SUBORDINATE_AGENT权限无效")

        # 3. 如果都没有权限，返回空列表
        if not has_create_user_permission and not has_create_agent_permission:
            logger.info(f"  ❌ 用户无任何创建权限")

        logger.info(f"用户 {current_user.username} 最终可创建角色: {[r.name for r in roles]}")

    data = [await role.to_dict() for role in roles]
    return Success(data=data)
