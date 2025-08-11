#!/usr/bin/env python3
"""
检查ag1用户是否有VIEW_GLOBAL_POINTS_USAGE权限
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.admin import User, Role
from app.core.init_app import init_db
from app.core.agent_permissions import AgentPermissionChecker
from app.models.enums import AgentPermission


async def check_ag1_global_view_permission():
    """检查ag1用户是否有VIEW_GLOBAL_POINTS_USAGE权限"""
    print("🔧 初始化数据库连接...")
    await init_db()

    print("\n🔍 检查ag1用户的VIEW_GLOBAL_POINTS_USAGE权限...")

    # 1. 查找ag1用户
    ag1_user = await User.filter(username="ag1").prefetch_related('roles').first()
    if not ag1_user:
        print("❌ 未找到ag1用户")
        return

    print(f"✅ ag1用户信息:")
    print(f"   - ID: {ag1_user.id}")
    print(f"   - 用户名: {ag1_user.username}")
    print(f"   - 是否超级管理员: {ag1_user.is_superuser}")

    # 2. 查看角色
    roles = await ag1_user.roles.all()
    print(f"\n👤 ag1的角色 (共{len(roles)}个):")
    for role in roles:
        print(f"   - 角色名: {role.name}")
        print(f"   - 是否代理角色: {role.is_agent_role}")
        print(f"   - 代理权限: {role.agent_permissions}")
        print(f"   - 用户层级: {role.user_level}")

    # 3. 检查VIEW_GLOBAL_POINTS_USAGE权限
    print(f"\n🔍 VIEW_GLOBAL_POINTS_USAGE权限检查:")
    has_global_view_permission = await AgentPermissionChecker.check_agent_permission(
        ag1_user.id, AgentPermission.VIEW_GLOBAL_POINTS_USAGE
    )
    print(f"   ag1是否有VIEW_GLOBAL_POINTS_USAGE权限: {has_global_view_permission}")

    # 4. 检查MANAGE_POINTS权限
    print(f"\n🔍 MANAGE_POINTS权限检查:")
    has_manage_points_permission = await AgentPermissionChecker.check_agent_permission(
        ag1_user.id, AgentPermission.MANAGE_POINTS
    )
    print(f"   ag1是否有MANAGE_POINTS权限: {has_manage_points_permission}")

    # 5. 获取ag1的所有代理权限
    all_permissions = await AgentPermissionChecker.get_user_agent_permissions(ag1_user.id)
    print(f"\n📜 ag1的所有代理权限:")
    for perm in all_permissions:
        print(f"   - {perm}")

    # 6. 分析问题
    print(f"\n🔍 问题分析:")
    print(f"   - ag1是超级管理员: {ag1_user.is_superuser}")
    print(f"   - ag1有VIEW_GLOBAL_POINTS_USAGE权限: {has_global_view_permission}")
    print(f"   - ag1有MANAGE_POINTS权限: {has_manage_points_permission}")
    
    if has_global_view_permission:
        print("   ⚠️  问题发现: ag1的角色被分配了VIEW_GLOBAL_POINTS_USAGE权限！")
        print("   这导致ag1被前端识别为管理员，能看到全局积分使用记录")
    else:
        print("   ✅ ag1没有VIEW_GLOBAL_POINTS_USAGE权限，这是正确的")

    print("\n✅ ag1用户VIEW_GLOBAL_POINTS_USAGE权限检查完成")


if __name__ == "__main__":
    asyncio.run(check_ag1_global_view_permission())
