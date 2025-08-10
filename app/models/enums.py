from enum import Enum, StrEnum


class EnumBase(Enum):
    @classmethod
    def get_member_values(cls):
        return [item.value for item in cls._member_map_.values()]

    @classmethod
    def get_member_names(cls):
        return [name for name in cls._member_names_]


class MethodType(StrEnum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


class PermissionType(StrEnum):
    """权限类型枚举"""
    VIEW_SUBORDINATE_USERS = "VIEW_SUBORDINATE_USERS"  # 查看下级用户


class AgentPermission(StrEnum):
    """代理权限枚举 - 8个核心权限选项"""
    VIEW_SUBORDINATE_USERS = "VIEW_SUBORDINATE_USERS"  # 查看下级用户权限
    CREATE_USER = "CREATE_USER"  # 创建用户权限
    MODIFY_SUBORDINATE_USERS = "MODIFY_SUBORDINATE_USERS"  # 修改下级用户权限
    MANAGE_POINTS = "MANAGE_POINTS"  # 积分管理权限
    DELETE_USER = "DELETE_USER"  # 删除用户权限
    MANAGE_RECHARGE_CARDS = "MANAGE_RECHARGE_CARDS"  # 充值卡管理权限
    DISABLE_USER = "DISABLE_USER"  # 禁用用户权限
    CREATE_SUBORDINATE_AGENT = "CREATE_SUBORDINATE_AGENT"  # 创建下级代理权限

    @classmethod
    def get_permission_descriptions(cls):
        """获取权限描述"""
        return {
            cls.VIEW_SUBORDINATE_USERS: "查看下级用户权限",
            cls.CREATE_USER: "创建用户权限",
            cls.MODIFY_SUBORDINATE_USERS: "修改下级用户权限",
            cls.MANAGE_POINTS: "积分管理权限",
            cls.DELETE_USER: "删除用户权限",
            cls.MANAGE_RECHARGE_CARDS: "充值卡管理权限",
            cls.DISABLE_USER: "禁用用户权限",
            cls.CREATE_SUBORDINATE_AGENT: "创建下级代理权限"
        }

    @classmethod
    def get_all_permissions(cls):
        """获取所有权限列表"""
        return [permission.value for permission in cls]



