#!/usr/bin/env python3
"""
诊断ag1用户权限问题
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.admin import User, Role, Api
from app.core.init_app import init_db
from app.core.agent_permissions import AgentPermissionChecker, AgentPermission


async def diagnose_ag1_permissions():
    """诊断ag1用户重置密码权限问题"""
    print("🔧 初始化数据库连接...")
    await init_db()

    print("\n🔍 诊断ag1用户重置密码权限问题...")

    # 1. 查找ag1用户
    ag1_user = await User.filter(username="ag1").prefetch_related('roles').first()
    if not ag1_user:
        print("❌ 未找到ag1用户")
        return

    print(f"✅ 找到用户: {ag1_user.username} (ID: {ag1_user.id})")
    print(f"   - 是否超级管理员: {ag1_user.is_superuser}")
    print(f"   - 父用户ID: {ag1_user.parent_user_id}")

    # 2. 查看用户角色
    roles = await ag1_user.roles.all()
    print(f"\n👤 用户角色 (共{len(roles)}个):")
    for role in roles:
        print(f"   - {role.name} (ID: {role.id})")
        print(f"     * 是否代理角色: {role.is_agent_role}")
        print(f"     * 代理权限: {role.agent_permissions}")

    # 3. 检查MODIFY_SUBORDINATE_USERS权限
    print(f"\n🔑 MODIFY_SUBORDINATE_USERS权限检查:")
    has_modify_permission = await AgentPermissionChecker.check_agent_permission(
        ag1_user.id, AgentPermission.MODIFY_SUBORDINATE_USERS
    )
    print(f"   ag1是否有MODIFY_SUBORDINATE_USERS权限: {has_modify_permission}")

    # 4. 获取ag1的所有代理权限
    all_permissions = await AgentPermissionChecker.get_user_agent_permissions(ag1_user.id)
    print(f"\n📜 ag1的所有代理权限:")
    for perm in all_permissions:
        print(f"   - {perm}")

    # 5. 测试目标用户
    print(f"\n🎯 测试重置密码权限:")
    target_users = await User.filter(username__in=['ag1ag2', 'ag1_normal_2210']).all()
    for target_user in target_users:
        print(f"\n   目标用户: {target_user.username} (ID: {target_user.id})")
        print(f"   - 父用户ID: {target_user.parent_user_id}")

        # 测试can_manage_user
        can_manage = await AgentPermissionChecker.can_manage_user(
            ag1_user.id, target_user.id, AgentPermission.MODIFY_SUBORDINATE_USERS
        )
        print(f"   - ag1能否管理此用户: {can_manage}")

        # 详细检查管理权限逻辑
        print(f"   - 详细权限检查:")
        print(f"     * ag1是超级用户: {ag1_user.is_superuser}")
        print(f"     * 目标用户的父用户ID: {target_user.parent_user_id}")
        print(f"     * ag1的ID: {ag1_user.id}")
        print(f"     * 父用户匹配: {target_user.parent_user_id == ag1_user.id}")

    # 6. 检查重置密码API权限
    print(f"\n🔧 重置密码API权限检查:")
    reset_password_api = await Api.filter(path="/api/v1/user/reset_password", method="POST").first()
    if reset_password_api:
        print(f"   找到重置密码API: {reset_password_api.method} {reset_password_api.path}")

        # 检查用户是否有直接的API权限
        has_direct_api_permission = False
        for role in roles:
            role_apis = await role.apis.all()
            if reset_password_api in role_apis:
                has_direct_api_permission = True
                print(f"   ✅ 角色 '{role.name}' 拥有直接的重置密码API权限")

        if not has_direct_api_permission:
            print("   ⚠️  用户没有直接的重置密码API权限（应通过代理权限映射获得）")
    else:
        print("   ❌ 未找到重置密码API")

    # 7. 测试重置密码API调用
    print(f"\n🧪 测试重置密码API调用:")

    # 测试目标用户
    target_user = await User.filter(username='ag1ag2').first()
    if target_user:
        print(f"   目标用户: {target_user.username} (ID: {target_user.id})")

        # 检查权限
        can_reset = await AgentPermissionChecker.can_manage_user(
            ag1_user.id, target_user.id, AgentPermission.MODIFY_SUBORDINATE_USERS
        )
        print(f"   权限检查结果: {can_reset}")

        if can_reset:
            print("   ✅ 权限验证通过，重置密码功能应该可以正常工作")
        else:
            print("   ❌ 权限验证失败，重置密码功能无法使用")

    print("\n✅ ag1用户重置密码权限诊断完成")


if __name__ == "__main__":
    asyncio.run(diagnose_ag1_permissions())
