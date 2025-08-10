from datetime import datetime, timedelta, timezone

from fastapi import APIRouter

from app.controllers.user import user_controller
from app.core.ctx import CTX_USER_ID
from app.core.dependency import DependAuth
from app.models.admin import Api, Menu, Role, User
from app.schemas.base import Fail, Success
from app.schemas.login import *
from app.schemas.users import UpdatePassword
from app.settings import settings
from app.utils.jwt_utils import create_access_token
from app.utils.password import get_password_hash, verify_password

router = APIRouter()


@router.post("/access_token", summary="获取token（前台客户端登录）")
async def login_access_token(credentials: CredentialsSchema):
    user: User = await user_controller.authenticate(credentials)
    await user_controller.update_last_login(user.id)
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + access_token_expires

    data = JWTOut(
        access_token=create_access_token(
            data=JWTPayload(
                user_id=user.id,
                username=user.username,
                is_superuser=user.is_superuser,
                exp=expire,
            )
        ),
        username=user.username,
    )
    return Success(data=data.model_dump())


@router.post("/admin_access_token", summary="获取管理平台token（后台管理登录）")
async def admin_login_access_token(credentials: CredentialsSchema):
    user: User = await user_controller.authenticate_admin(credentials)
    await user_controller.update_last_login(user.id)
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + access_token_expires

    data = JWTOut(
        access_token=create_access_token(
            data=JWTPayload(
                user_id=user.id,
                username=user.username,
                is_superuser=user.is_superuser,
                exp=expire,
            )
        ),
        username=user.username,
    )
    return Success(data=data.model_dump())


@router.get("/userinfo", summary="查看用户信息", dependencies=[DependAuth])
async def get_userinfo():
    user_id = CTX_USER_ID.get()
    user_obj = await user_controller.get(id=user_id)
    data = await user_obj.to_dict(exclude_fields=["password"])
    data["avatar"] = "https://avatars.githubusercontent.com/u/54677442?v=4"
    return Success(data=data)


@router.get("/usermenu", summary="查看用户菜单", dependencies=[DependAuth])
async def get_user_menu():
    from app.core.menu_permissions import MenuPermissionMapping
    from app.core.agent_permissions import AgentPermissionChecker

    user_id = CTX_USER_ID.get()
    user_obj = await User.filter(id=user_id).first()

    # 获取所有菜单
    all_menus = await Menu.all()
    accessible_menus = []

    if user_obj.is_superuser:
        # 超级管理员可以访问所有菜单
        accessible_menus = all_menus
    else:
        # 获取用户的代理权限和菜单权限
        user_permissions = []
        role_objs: list[Role] = await user_obj.roles

        # 先收集所有权限和菜单，避免重复添加
        accessible_menu_ids = set()

        for role_obj in role_objs:
            # 获取代理权限
            if role_obj.is_agent_role and role_obj.agent_permissions:
                user_permissions.extend(role_obj.agent_permissions)

            # 获取角色直接分配的菜单权限
            role_menus = await role_obj.menus
            for menu in role_menus:
                accessible_menu_ids.add(menu.id)

        # 去重权限
        user_permissions = list(set(user_permissions))

        # 根据代理权限添加额外的菜单
        for menu in all_menus:
            if MenuPermissionMapping.is_menu_accessible(
                menu.name,
                user_permissions,
                user_obj.is_superuser
            ):
                accessible_menu_ids.add(menu.id)
                # 如果是子菜单，确保其父菜单也被添加
                if menu.parent_id != 0:
                    parent_menu = next((m for m in all_menus if m.id == menu.parent_id), None)
                    if parent_menu:
                        accessible_menu_ids.add(parent_menu.id)

        # 根据ID获取最终的菜单列表（自动去重）
        accessible_menus = [menu for menu in all_menus if menu.id in accessible_menu_ids]

    # 构建菜单树结构
    parent_menus: list[Menu] = []
    for menu in accessible_menus:
        if menu.parent_id == 0:
            parent_menus.append(menu)

    res = []
    for parent_menu in parent_menus:
        parent_menu_dict = await parent_menu.to_dict()
        parent_menu_dict["children"] = []
        for menu in accessible_menus:
            if menu.parent_id == parent_menu.id:
                parent_menu_dict["children"].append(await menu.to_dict())
        res.append(parent_menu_dict)

    return Success(data=res)


@router.get("/permission-menu-mapping", summary="获取权限与菜单的映射关系", dependencies=[DependAuth])
async def get_permission_menu_mapping():
    from app.core.menu_permissions import MenuPermissionMapping

    mapping_info = {
        "permission_menu_map": MenuPermissionMapping.PERMISSION_MENU_MAP,
        "super_admin_only_menus": MenuPermissionMapping.SUPER_ADMIN_ONLY_MENUS,
        "permission_descriptions": MenuPermissionMapping.get_permission_description()
    }

    return Success(data=mapping_info)


@router.get("/userapi", summary="查看用户API", dependencies=[DependAuth])
async def get_user_api():
    from app.core.menu_permissions import MenuPermissionMapping

    user_id = CTX_USER_ID.get()
    user_obj = await User.filter(id=user_id).first()

    if user_obj.is_superuser:
        api_objs: list[Api] = await Api.all()
        apis = [api.method.lower() + api.path for api in api_objs]
        return Success(data=apis)

    role_objs: list[Role] = await user_obj.roles
    apis = []

    # 获取直接分配的API权限
    for role_obj in role_objs:
        api_objs: list[Api] = await role_obj.apis
        apis.extend([api.method.lower() + api.path for api in api_objs])

    # 获取通过代理权限映射的API权限
    agent_permissions = set()
    for role_obj in role_objs:
        if role_obj.is_agent_role and role_obj.agent_permissions:
            agent_permissions.update(role_obj.agent_permissions)

    # 添加代理权限映射的API
    for permission in agent_permissions:
        if permission in MenuPermissionMapping.PERMISSION_API_MAP:
            mapped_apis = MenuPermissionMapping.PERMISSION_API_MAP[permission]
            for method, path in mapped_apis:
                apis.append(method.lower() + path)

    apis = list(set(apis))
    return Success(data=apis)


@router.post("/update_password", summary="修改密码", dependencies=[DependAuth])
async def update_user_password(req_in: UpdatePassword):
    user_id = CTX_USER_ID.get()
    user = await user_controller.get(user_id)
    verified = verify_password(req_in.old_password, user.password)
    if not verified:
        return Fail(msg="旧密码验证错误！")
    user.password = get_password_hash(req_in.new_password)
    await user.save()
    return Success(msg="修改成功")
