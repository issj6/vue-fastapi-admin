from typing import List

from app.core.crud import CRUDBase
from app.models.admin import Api, Menu, Role
from app.schemas.roles import RoleCreate, RoleUpdate
from app.models.enums import AgentPermission


class RoleController(CRUDBase[Role, RoleCreate, RoleUpdate]):
    def __init__(self):
        super().__init__(model=Role)

    async def is_exist(self, name: str) -> bool:
        return await self.model.filter(name=name).exists()

    async def update_roles(self, role: Role, menu_ids: List[int], api_infos: List[dict]) -> None:
        await role.menus.clear()
        for menu_id in menu_ids:
            menu_obj = await Menu.filter(id=menu_id).first()
            await role.menus.add(menu_obj)

        await role.apis.clear()
        for item in api_infos:
            api_obj = await Api.filter(path=item.get("path"), method=item.get("method")).first()
            await role.apis.add(api_obj)

    async def update_agent_permissions(self, role: Role, agent_permissions: List[str],
                                     is_agent_role: bool) -> None:
        """更新角色的代理权限配置"""
        # 验证权限有效性
        valid_permissions = AgentPermission.get_all_permissions()
        filtered_permissions = [p for p in agent_permissions if p in valid_permissions]

        # 更新角色配置
        role.agent_permissions = filtered_permissions
        role.is_agent_role = is_agent_role
        await role.save()

    async def get_agent_roles(self) -> List[Role]:
        """获取所有代理角色"""
        return await self.model.filter(is_agent_role=True).all()

    async def create_agent_role(self, name: str, desc: str,
                              agent_permissions: List[str]) -> Role:
        """创建代理角色"""
        # 验证权限有效性
        valid_permissions = AgentPermission.get_all_permissions()
        filtered_permissions = [p for p in agent_permissions if p in valid_permissions]

        role = await self.model.create(
            name=name,
            desc=desc,
            agent_permissions=filtered_permissions,
            is_agent_role=True
        )
        return role


role_controller = RoleController()
