"""
菜单权限映射配置
定义代理权限与菜单项的映射关系
"""
from typing import Dict, List
from app.models.enums import AgentPermission


class MenuPermissionMapping:
    """菜单权限映射类"""

    # 所有登录用户都可以访问的基础API（个人中心等）
    BASIC_USER_APIS: List[tuple] = [
        ("GET", "/api/v1/base/userinfo"),      # 获取用户信息
        ("GET", "/api/v1/base/usermenu"),      # 获取用户菜单
        ("GET", "/api/v1/base/userapi"),       # 获取用户API权限
        ("POST", "/api/v1/base/update_password"), # 修改密码
        ("GET", "/api/v1/user/invitation_info"), # 获取邀请信息
        ("POST", "/api/v1/user/update"),       # 更新个人信息（仅限自己）
        # 积分管理相关API
        ("GET", "/api/v1/points/info"),        # 获取积分信息
        ("POST", "/api/v1/points/exchange"),   # 使用兑换码
        ("POST", "/api/v1/points/recharge"),   # 积分充值
        ("GET", "/api/v1/points/recharge/records"), # 获取充值记录
        ("GET", "/api/v1/points/usage/records"), # 获取使用记录
        ("POST", "/api/v1/points/usage/create"), # 创建使用记录
    ]

    # 所有登录用户都可以访问的基础菜单
    BASIC_USER_MENUS: List[str] = [
        "/profile",  # 个人中心
        "/points",   # 积分管理
        "/points/info",  # 积分信息
        "/points/usage", # 使用记录
    ]

    # 定义代理权限与API的映射关系
    PERMISSION_API_MAP: Dict[str, List[tuple]] = {
        # 查看下级用户权限 -> 用户相关API
        AgentPermission.VIEW_SUBORDINATE_USERS.value: [
            ("GET", "/api/v1/user/list"),
            ("GET", "/api/v1/user/subordinates"),
            ("GET", "/api/v1/user/agents"),  # 代理用户列表API
        ],

        # 创建用户权限 -> 用户创建API
        AgentPermission.CREATE_USER.value: [
            ("POST", "/api/v1/user/create"),
            ("GET", "/api/v1/role/list"),  # 创建用户时需要获取角色列表
            ("GET", "/api/v1/role/creatable"),  # 获取可创建的角色列表
        ],

        # 修改下级用户权限 -> 用户修改API
        AgentPermission.MODIFY_SUBORDINATE_USERS.value: [
            ("POST", "/api/v1/user/update"),
            ("POST", "/api/v1/user/reset_password"),  # 重置密码API
            ("GET", "/api/v1/role/list"),  # 修改用户时需要获取角色列表
        ],

        # 积分管理权限 -> 积分相关API
        AgentPermission.MANAGE_POINTS.value: [
            ("POST", "/api/v1/user/add_points"),
            ("POST", "/api/v1/user/deduct_points"),
        ],

        # 删除用户权限 -> 用户删除API
        AgentPermission.DELETE_USER.value: [
            ("DELETE", "/api/v1/user/delete"),
        ],

        # 禁用用户权限 -> 用户状态管理API
        AgentPermission.DISABLE_USER.value: [
            ("POST", "/api/v1/user/update"),  # 通过更新用户状态来禁用
        ],

        # 充值卡管理权限 -> 充值卡相关API
        AgentPermission.MANAGE_RECHARGE_CARDS.value: [
            # 这里可以添加充值卡相关的API
        ],

        # 创建下级代理权限 -> 角色和用户创建API
        AgentPermission.CREATE_SUBORDINATE_AGENT.value: [
            ("POST", "/api/v1/user/create"),
            ("GET", "/api/v1/role/list"),
            ("GET", "/api/v1/role/agent_roles"),  # 获取代理角色列表
        ],
    }

    # 定义代理权限与菜单的映射关系
    PERMISSION_MENU_MAP: Dict[str, List[str]] = {
        # 查看下级用户权限 -> 用户管理和代理管理菜单
        AgentPermission.VIEW_SUBORDINATE_USERS.value: [
            "用户管理",  # 普通用户列表页面
            "代理管理",  # 代理用户列表页面
        ],

        # 创建用户权限 -> 用户管理和代理管理菜单
        AgentPermission.CREATE_USER.value: [
            "用户管理",
            "代理管理",
        ],

        # 修改下级用户权限 -> 用户管理和代理管理菜单
        AgentPermission.MODIFY_SUBORDINATE_USERS.value: [
            "用户管理",
            "代理管理",
        ],

        # 积分管理权限 -> 用户管理和代理管理菜单
        AgentPermission.MANAGE_POINTS.value: [
            "用户管理",
            "代理管理",
        ],

        # 删除用户权限 -> 用户管理和代理管理菜单
        AgentPermission.DELETE_USER.value: [
            "用户管理",
            "代理管理",
        ],

        # 禁用用户权限 -> 用户管理和代理管理菜单
        AgentPermission.DISABLE_USER.value: [
            "用户管理",
            "代理管理",
        ],

        # 充值卡管理权限 -> 充值卡管理菜单（如果存在）
        AgentPermission.MANAGE_RECHARGE_CARDS.value: [
            "充值卡管理",
        ],

        # 创建下级代理权限 -> 代理管理菜单
        AgentPermission.CREATE_SUBORDINATE_AGENT.value: [
            "代理管理",
        ],
    }
    
    # 超级管理员专用菜单（只有超级管理员能看到）
    SUPER_ADMIN_ONLY_MENUS: List[str] = [
        "角色管理",
        "菜单管理", 
        "API管理",
        "系统管理",
    ]
    
    @classmethod
    def get_accessible_menus_by_permissions(cls, permissions: List[str]) -> List[str]:
        """
        根据用户权限获取可访问的菜单列表
        
        Args:
            permissions: 用户拥有的权限列表
            
        Returns:
            List[str]: 可访问的菜单名称列表
        """
        accessible_menus = set()
        
        for permission in permissions:
            if permission in cls.PERMISSION_MENU_MAP:
                accessible_menus.update(cls.PERMISSION_MENU_MAP[permission])
        
        return list(accessible_menus)
    
    @classmethod
    def is_menu_accessible(cls, menu_name: str, permissions: List[str], is_superuser: bool = False) -> bool:
        """
        检查指定菜单是否可访问
        
        Args:
            menu_name: 菜单名称
            permissions: 用户权限列表
            is_superuser: 是否为超级管理员
            
        Returns:
            bool: 是否可访问
        """
        # 超级管理员可以访问所有菜单
        if is_superuser:
            return True
            
        # 检查是否为超级管理员专用菜单
        if menu_name in cls.SUPER_ADMIN_ONLY_MENUS:
            return False
            
        # 检查是否有对应权限
        accessible_menus = cls.get_accessible_menus_by_permissions(permissions)
        return menu_name in accessible_menus
    
    @classmethod
    def get_permission_description(cls) -> Dict[str, str]:
        """
        获取权限与菜单的映射描述
        
        Returns:
            Dict[str, str]: 权限描述映射
        """
        descriptions = {}
        for permission, menus in cls.PERMISSION_MENU_MAP.items():
            menu_list = "、".join(menus)
            descriptions[permission] = f"可访问：{menu_list}"
        
        return descriptions
