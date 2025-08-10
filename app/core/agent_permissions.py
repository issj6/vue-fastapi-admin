"""
代理权限管理核心模块
实现基于8个核心权限的简化权限检查逻辑
"""
from typing import List, Optional

from app.models.admin import User, Role
from app.models.enums import AgentPermission


class AgentPermissionChecker:
    """代理权限检查器"""
    
    @staticmethod
    async def check_agent_permission(user_id: int, permission: AgentPermission) -> bool:
        """
        检查用户是否具有指定的代理权限
        
        Args:
            user_id: 用户ID
            permission: 要检查的权限
            
        Returns:
            bool: 是否具有权限
        """
        user = await User.filter(id=user_id).first()
        if not user:
            return False
            
        # 超级管理员默认拥有所有权限
        if user.is_superuser:
            return True
            
        # 检查用户角色的代理权限
        roles = await user.roles.all()
        for role in roles:
            if role.is_agent_role and role.agent_permissions:
                if permission.value in role.agent_permissions:
                    return True
                    
        return False
    
    @staticmethod
    async def get_user_agent_permissions(user_id: int) -> List[str]:
        """
        获取用户的所有代理权限
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[str]: 权限列表
        """
        user = await User.filter(id=user_id).first()
        if not user:
            return []
            
        # 超级管理员拥有所有权限
        if user.is_superuser:
            return AgentPermission.get_all_permissions()
            
        permissions = set()
        roles = await user.roles.all()
        for role in roles:
            if role.is_agent_role and role.agent_permissions:
                permissions.update(role.agent_permissions)
                
        return list(permissions)
    

    
    @staticmethod
    async def can_create_subordinate_agent(user_id: int) -> bool:
        """
        检查用户是否可以创建下级代理
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 是否可以创建下级代理
        """
        # 检查是否有创建下级代理权限
        has_permission = await AgentPermissionChecker.check_agent_permission(
            user_id, AgentPermission.CREATE_SUBORDINATE_AGENT
        )
        if not has_permission:
            return False
            
        # 检查用户层级，只有超级管理员和一级代理可以创建下级代理
        user_level = await AgentPermissionChecker.get_user_level(user_id)
        return user_level in [UserLevel.SUPER_ADMIN.value, UserLevel.LEVEL_1_AGENT.value]
    
    @staticmethod
    async def can_manage_user(user_id: int, target_user_id: int, permission: AgentPermission) -> bool:
        """
        检查用户是否可以管理目标用户
        
        Args:
            user_id: 操作用户ID
            target_user_id: 目标用户ID
            permission: 要检查的权限
            
        Returns:
            bool: 是否可以管理
        """
        # 检查是否有相应权限
        has_permission = await AgentPermissionChecker.check_agent_permission(user_id, permission)
        if not has_permission:
            return False
            
        user = await User.filter(id=user_id).first()
        target_user = await User.filter(id=target_user_id).first()
        
        if not user or not target_user:
            return False
            
        # 超级管理员可以管理所有用户
        if user.is_superuser:
            return True
            
        # 检查是否为下级用户
        return target_user.parent_user_id == user_id
    



# 权限检查装饰器和快捷函数
async def check_view_subordinate_users(user_id: int) -> bool:
    """检查查看下级用户权限"""
    return await AgentPermissionChecker.check_agent_permission(
        user_id, AgentPermission.VIEW_SUBORDINATE_USERS
    )


async def check_create_user(user_id: int) -> bool:
    """检查创建用户权限"""
    return await AgentPermissionChecker.check_agent_permission(
        user_id, AgentPermission.CREATE_USER
    )


async def check_modify_subordinate_users(user_id: int) -> bool:
    """检查修改下级用户权限"""
    return await AgentPermissionChecker.check_agent_permission(
        user_id, AgentPermission.MODIFY_SUBORDINATE_USERS
    )


async def check_manage_points(user_id: int) -> bool:
    """检查积分管理权限"""
    return await AgentPermissionChecker.check_agent_permission(
        user_id, AgentPermission.MANAGE_POINTS
    )


async def check_delete_user(user_id: int) -> bool:
    """检查删除用户权限"""
    return await AgentPermissionChecker.check_agent_permission(
        user_id, AgentPermission.DELETE_USER
    )


async def check_manage_recharge_cards(user_id: int) -> bool:
    """检查充值卡管理权限"""
    return await AgentPermissionChecker.check_agent_permission(
        user_id, AgentPermission.MANAGE_RECHARGE_CARDS
    )


async def check_disable_user(user_id: int) -> bool:
    """检查禁用用户权限"""
    return await AgentPermissionChecker.check_agent_permission(
        user_id, AgentPermission.DISABLE_USER
    )


async def check_create_subordinate_agent(user_id: int) -> bool:
    """检查创建下级代理权限"""
    return await AgentPermissionChecker.can_create_subordinate_agent(user_id)
