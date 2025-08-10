import logging

from fastapi import APIRouter, Query
from fastapi.exceptions import HTTPException
from tortoise.expressions import Q

from app.controllers import role_controller
from app.schemas.base import Success, SuccessExtra
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


@router.delete("/delete", summary="删除角色")
async def delete_role(
    role_id: int = Query(..., description="角色ID"),
):
    await role_controller.remove(id=role_id)
    return Success(msg="Deleted Success")


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
    """获取当前用户可以创建的角色列表"""
    current_user_id = CTX_USER_ID.get()

    # 获取当前用户
    from app.models.admin import User, Role
    current_user = await User.filter(id=current_user_id).first()

    if current_user.is_superuser:
        # 超级管理员可以创建除了管理员角色外的所有角色
        all_roles = await Role.all()
        # 过滤掉管理员角色，避免创建多个管理员
        roles = [role for role in all_roles if role.name != "管理员"]
    else:
        # 普通用户根据代理权限决定可创建的角色
        user_roles = await current_user.roles.all()

        # 检查是否有创建下级代理的权限
        can_create_agent = False
        for role in user_roles:
            if role.is_agent_role and role.agent_permissions:
                if "CREATE_SUBORDINATE_AGENT" in role.agent_permissions:
                    can_create_agent = True
                    break

        # 根据权限返回可创建的角色
        all_roles = await Role.all()
        roles = []

        for role in all_roles:
            # 普通用户角色总是可以创建
            if role.name == "普通用户":
                roles.append(role)
            # 如果有创建下级代理权限，只能创建比自己权限低的代理角色
            elif can_create_agent and role.is_agent_role and role.name != "管理员":
                # 获取当前用户的代理权限数量
                current_user_permissions = set()
                for user_role in user_roles:
                    if user_role.is_agent_role and user_role.agent_permissions:
                        current_user_permissions.update(user_role.agent_permissions)

                # 目标角色的代理权限数量
                target_permissions = set(role.agent_permissions or [])

                # 只能创建权限严格少于自己的角色，且目标权限必须是自己权限的子集
                if (len(target_permissions) < len(current_user_permissions) and
                    target_permissions.issubset(current_user_permissions)):
                    roles.append(role)

    data = [await role.to_dict() for role in roles]
    return Success(data=data)
