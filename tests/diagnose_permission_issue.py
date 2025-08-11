#!/usr/bin/env python3
"""
诊断积分使用记录权限问题
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


async def diagnose_permission_issue():
    """诊断积分使用记录权限问题"""
    print("🔧 初始化数据库连接...")
    await init_db()

    print("\n🔍 诊断积分使用记录权限问题...")

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

    # 3. 检查MANAGE_POINTS权限
    has_manage_points = await AgentPermissionChecker.check_agent_permission(
        ag1_user.id, AgentPermission.MANAGE_POINTS
    )
    print(f"\n🔍 ag1是否有MANAGE_POINTS权限: {has_manage_points}")

    # 4. 获取所有代理权限
    all_permissions = await AgentPermissionChecker.get_user_agent_permissions(ag1_user.id)
    print(f"\n📋 ag1的所有代理权限: {all_permissions}")

    # 5. 检查admin用户作为对比
    admin_user = await User.filter(username="admin").prefetch_related('roles').first()
    if admin_user:
        print(f"\n🔍 对比admin用户:")
        print(f"   - 是否超级管理员: {admin_user.is_superuser}")
        admin_has_manage_points = await AgentPermissionChecker.check_agent_permission(
            admin_user.id, AgentPermission.MANAGE_POINTS
        )
        print(f"   - 是否有MANAGE_POINTS权限: {admin_has_manage_points}")

    # 6. 分析问题
    print(f"\n🔍 问题分析:")
    print(f"   - ag1是超级管理员: {ag1_user.is_superuser}")
    print(f"   - ag1有MANAGE_POINTS权限: {has_manage_points}")
    
    if ag1_user.is_superuser:
        print("   ⚠️  问题发现: ag1被设置为超级管理员，这导致它拥有所有权限！")
    elif has_manage_points:
        print("   ⚠️  问题发现: ag1的角色被分配了MANAGE_POINTS权限！")
    else:
        print("   ✅ ag1权限正常，问题可能在前端逻辑")


if __name__ == "__main__":
    asyncio.run(diagnose_permission_issue())
