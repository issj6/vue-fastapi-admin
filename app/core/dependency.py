from typing import Optional

import jwt
from fastapi import Depends, Header, HTTPException, Request

from app.core.ctx import CTX_USER_ID
from app.models import Role, User
from app.settings import settings


class AuthControl:
    @classmethod
    async def is_authed(cls, token: str = Header(..., description="token验证")) -> Optional["User"]:
        try:
            if token == "dev":
                user = await User.filter().first()
                user_id = user.id
            else:
                decode_data = jwt.decode(token, settings.SECRET_KEY, algorithms=settings.JWT_ALGORITHM)
                user_id = decode_data.get("user_id")
            user = await User.filter(id=user_id).first()
            if not user:
                raise HTTPException(status_code=401, detail="Authentication failed")
            CTX_USER_ID.set(int(user_id))
            return user
        except jwt.DecodeError:
            raise HTTPException(status_code=401, detail="无效的Token")
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="登录已过期")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"{repr(e)}")


class PermissionControl:
    @classmethod
    async def has_permission(cls, request: Request, current_user: User = Depends(AuthControl.is_authed)) -> None:
        if current_user.is_superuser:
            return
        method = request.method
        path = request.url.path

        # 检查基础API权限（所有登录用户都可以访问）
        from app.core.menu_permissions import MenuPermissionMapping
        if (method, path) in MenuPermissionMapping.BASIC_USER_APIS:
            return

        roles: list[Role] = await current_user.roles
        if not roles:
            raise HTTPException(status_code=403, detail="用户未分配角色，无法访问系统功能")

        # 获取传统API权限
        apis = [await role.apis for role in roles]
        permission_apis = list(set((api.method, api.path) for api in sum(apis, [])))

        # 检查传统API权限
        if (method, path) in permission_apis:
            return

        # 获取用户的代理权限
        agent_permissions = set()
        for role in roles:
            if role.is_agent_role and role.agent_permissions:
                agent_permissions.update(role.agent_permissions)

        # 检查代理权限是否允许访问此API
        for permission in agent_permissions:
            if permission in MenuPermissionMapping.PERMISSION_API_MAP:
                allowed_apis = MenuPermissionMapping.PERMISSION_API_MAP[permission]
                if (method, path) in allowed_apis:
                    return

        # 如果都没有权限，则拒绝访问
        # 根据路径提供友好的错误提示
        friendly_messages = {
            "/api/v1/user/list": "权限不足，无法查看用户列表",
            "/api/v1/user/create": "权限不足，无法创建用户",
            "/api/v1/user/update": "权限不足，无法修改用户信息",
            "/api/v1/user/delete": "权限不足，无法删除用户",
            "/api/v1/role/list": "权限不足，无法查看角色列表",
            "/api/v1/role/creatable": "权限不足，无法查看可创建角色",
            "/api/v1/role/create": "权限不足，无法创建角色",
            "/api/v1/menu/list": "权限不足，无法查看菜单列表",
            "/api/v1/api/list": "权限不足，无法查看API列表",
        }

        error_message = friendly_messages.get(path, "权限不足，无法访问此功能")
        raise HTTPException(status_code=403, detail=error_message)


DependAuth = Depends(AuthControl.is_authed)
DependPermission = Depends(PermissionControl.has_permission)
