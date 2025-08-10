#!/usr/bin/env python3
"""
测试权限系统修复
验证一级代理用户是否能正常访问用户管理功能
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.admin import User, Role
from app.core.agent_permissions import AgentPermissionChecker
from app.core.menu_permissions import MenuPermissionMapping
from app.models.enums import AgentPermission
from app.core.init_app import init_db


async def test_permission_system():
    """测试权限系统"""
    print("🔧 初始化数据库连接...")
    await init_db()
    
    print("\n📋 测试权限系统修复...")
    
    # 查看所有用户
    all_users = await User.all()
    print(f"📋 数据库中的所有用户:")
    for user in all_users:
        print(f"   - {user.username} (ID: {user.id}, 超级管理员: {user.is_superuser})")

    # 查找一级代理用户
    agent_user = await User.filter(username="test001").first()
    if not agent_user:
        # 尝试查找其他可能的代理用户
        agent_user = await User.filter(is_superuser=False).first()
        if not agent_user:
            print("❌ 未找到任何非超级管理员用户")
            return
        print(f"⚠️  未找到 test001，使用用户: {agent_user.username}")
    else:
        print(f"✅ 找到一级代理用户: {agent_user.username} (ID: {agent_user.id})")

    
    # 获取用户角色
    roles = await agent_user.roles.all()
    print(f"📝 用户角色: {[role.name for role in roles]}")
    
    # 检查代理权限
    for role in roles:
        if role.is_agent_role:
            print(f"🎯 代理角色: {role.name}")
            print(f"   代理权限: {role.agent_permissions}")
            
            # 检查具体权限
            if AgentPermission.VIEW_SUBORDINATE_USERS.value in role.agent_permissions:
                print("   ✅ 拥有查看下级用户权限")
            if AgentPermission.CREATE_USER.value in role.agent_permissions:
                print("   ✅ 拥有创建用户权限")
    
    # 测试权限检查
    print("\n🧪 测试权限检查...")
    
    # 测试查看下级用户权限
    has_view_permission = await AgentPermissionChecker.check_agent_permission(
        agent_user.id, AgentPermission.VIEW_SUBORDINATE_USERS
    )
    print(f"查看下级用户权限: {'✅ 有权限' if has_view_permission else '❌ 无权限'}")
    
    # 测试创建用户权限
    has_create_permission = await AgentPermissionChecker.check_agent_permission(
        agent_user.id, AgentPermission.CREATE_USER
    )
    print(f"创建用户权限: {'✅ 有权限' if has_create_permission else '❌ 无权限'}")
    
    # 检查API映射
    print("\n🔗 检查API权限映射...")
    
    # 查看下级用户权限对应的API
    view_apis = MenuPermissionMapping.PERMISSION_API_MAP.get(
        AgentPermission.VIEW_SUBORDINATE_USERS.value, []
    )
    print(f"查看下级用户权限对应的API: {view_apis}")
    
    # 创建用户权限对应的API
    create_apis = MenuPermissionMapping.PERMISSION_API_MAP.get(
        AgentPermission.CREATE_USER.value, []
    )
    print(f"创建用户权限对应的API: {create_apis}")
    
    print("\n✅ 权限系统测试完成")


if __name__ == "__main__":
    asyncio.run(test_permission_system())
