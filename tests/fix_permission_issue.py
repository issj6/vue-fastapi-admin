#!/usr/bin/env python3
"""
修复积分使用记录权限问题
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.admin import User, Role
from app.core.init_app import init_db
from app.models.enums import AgentPermission


async def fix_permission_issue():
    """修复积分使用记录权限问题"""
    print("🔧 初始化数据库连接...")
    await init_db()

    print("\n🔧 修复积分使用记录权限问题...")

    # 1. 查找所有代理角色
    agent_roles = await Role.filter(is_agent_role=True).all()
    print(f"\n📋 找到 {len(agent_roles)} 个代理角色:")
    
    for role in agent_roles:
        print(f"   - {role.name} (层级: {role.user_level})")
        print(f"     当前权限: {role.agent_permissions}")
        
        # 检查是否有MANAGE_POINTS权限但不应该有全局查看权限
        if role.agent_permissions and 'MANAGE_POINTS' in role.agent_permissions:
            # 对于一级代理和二级代理，保留MANAGE_POINTS但不给VIEW_GLOBAL_POINTS_USAGE
            if role.user_level > 0:  # 不是超级管理员级别
                print(f"     ⚠️  {role.name} 有MANAGE_POINTS权限，但不应该有全局查看权限")
                
                # 确保没有VIEW_GLOBAL_POINTS_USAGE权限
                if 'VIEW_GLOBAL_POINTS_USAGE' in role.agent_permissions:
                    role.agent_permissions.remove('VIEW_GLOBAL_POINTS_USAGE')
                    await role.save()
                    print(f"     ✅ 已移除 {role.name} 的VIEW_GLOBAL_POINTS_USAGE权限")

    # 2. 查找管理员角色，给予全局查看权限
    admin_roles = await Role.filter(name__in=["管理员", "系统管理员", "超级管理员"]).all()
    print(f"\n👑 找到 {len(admin_roles)} 个管理员角色:")
    
    for role in admin_roles:
        print(f"   - {role.name}")
        print(f"     当前权限: {role.agent_permissions}")
        
        # 确保管理员角色有VIEW_GLOBAL_POINTS_USAGE权限
        if not role.agent_permissions:
            role.agent_permissions = []
        
        if 'VIEW_GLOBAL_POINTS_USAGE' not in role.agent_permissions:
            role.agent_permissions.append('VIEW_GLOBAL_POINTS_USAGE')
            await role.save()
            print(f"     ✅ 已添加 {role.name} 的VIEW_GLOBAL_POINTS_USAGE权限")

    # 3. 验证修复结果
    print(f"\n🔍 验证修复结果:")
    
    # 检查ag1用户
    ag1_user = await User.filter(username="ag1").prefetch_related('roles').first()
    if ag1_user:
        roles = await ag1_user.roles.all()
        for role in roles:
            has_global_view = 'VIEW_GLOBAL_POINTS_USAGE' in (role.agent_permissions or [])
            has_manage_points = 'MANAGE_POINTS' in (role.agent_permissions or [])
            print(f"   - ag1的角色 {role.name}:")
            print(f"     * 有MANAGE_POINTS权限: {has_manage_points}")
            print(f"     * 有VIEW_GLOBAL_POINTS_USAGE权限: {has_global_view}")

    # 检查admin用户
    admin_user = await User.filter(username="admin").first()
    if admin_user:
        print(f"   - admin用户:")
        print(f"     * 是超级管理员: {admin_user.is_superuser}")
        if admin_user.is_superuser:
            print(f"     * 超级管理员自动拥有所有权限")

    print(f"\n✅ 权限修复完成！")
    print(f"📝 修复说明:")
    print(f"   - MANAGE_POINTS权限：用于管理下级用户的积分（增加/扣除）")
    print(f"   - VIEW_GLOBAL_POINTS_USAGE权限：用于查看全局积分使用记录")
    print(f"   - 一级代理保留MANAGE_POINTS权限，但不能查看全局记录")
    print(f"   - 只有真正的管理员才能查看全局积分使用记录")


if __name__ == "__main__":
    asyncio.run(fix_permission_issue())
