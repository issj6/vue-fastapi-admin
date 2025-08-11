#!/usr/bin/env python3
"""
修复代理角色层级问题
确保一级代理权限 > 二级代理权限 > 三级代理权限
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.admin import Role
from app.core.init_app import init_db


async def fix_agent_role_hierarchy():
    """修复代理角色层级权限问题"""
    print("🔧 修复代理角色层级权限问题...")
    await init_db()
    
    # 定义正确的权限层级
    role_permissions = {
        "超级代理": [
            "VIEW_SUBORDINATE_USERS",
            "CREATE_USER", 
            "MODIFY_SUBORDINATE_USERS",
            "MANAGE_POINTS",
            "DELETE_USER",
            "MANAGE_RECHARGE_CARDS",
            "DISABLE_USER",
            "CREATE_SUBORDINATE_AGENT"
        ],
        "一级代理": [
            "VIEW_SUBORDINATE_USERS",
            "CREATE_USER",
            "MODIFY_SUBORDINATE_USERS", 
            "MANAGE_POINTS",
            "DELETE_USER",  # 一级代理有删除权限
            "MANAGE_RECHARGE_CARDS",
            "CREATE_SUBORDINATE_AGENT"
        ],
        "二级代理": [
            "VIEW_SUBORDINATE_USERS",
            "CREATE_USER",
            "MODIFY_SUBORDINATE_USERS",
            "MANAGE_POINTS",
            "MANAGE_RECHARGE_CARDS",
            "CREATE_SUBORDINATE_AGENT"
        ],
        "三级代理": [
            "VIEW_SUBORDINATE_USERS",
            "CREATE_USER", 
            "MODIFY_SUBORDINATE_USERS",
            "MANAGE_POINTS",
            "MANAGE_RECHARGE_CARDS"
        ]
    }
    
    print("\n1️⃣ 当前角色权限状态:")
    for role_name, expected_permissions in role_permissions.items():
        role = await Role.filter(name=role_name).first()
        if role:
            current_permissions = role.agent_permissions or []
            print(f"   {role_name}:")
            print(f"     当前权限: {current_permissions}")
            print(f"     权限数量: {len(current_permissions)}")
            print(f"     期望权限: {expected_permissions}")
            print(f"     期望数量: {len(expected_permissions)}")
            print(f"     需要更新: {set(current_permissions) != set(expected_permissions)}")
            print()
    
    # 更新角色权限
    print("\n2️⃣ 更新角色权限...")
    for role_name, expected_permissions in role_permissions.items():
        role = await Role.filter(name=role_name).first()
        if role:
            old_permissions = role.agent_permissions or []
            role.agent_permissions = expected_permissions
            await role.save()
            print(f"   ✅ 更新 {role_name}:")
            print(f"     旧权限: {old_permissions} ({len(old_permissions)}个)")
            print(f"     新权限: {expected_permissions} ({len(expected_permissions)}个)")
        else:
            print(f"   ❌ 未找到角色: {role_name}")
    
    # 验证权限层级
    print("\n3️⃣ 验证权限层级关系...")
    
    # 获取更新后的角色
    super_agent = await Role.filter(name="超级代理").first()
    level1_agent = await Role.filter(name="一级代理").first() 
    level2_agent = await Role.filter(name="二级代理").first()
    level3_agent = await Role.filter(name="三级代理").first()
    
    roles_hierarchy = [
        ("超级代理", super_agent),
        ("一级代理", level1_agent),
        ("二级代理", level2_agent), 
        ("三级代理", level3_agent)
    ]
    
    for i, (name, role) in enumerate(roles_hierarchy):
        if role:
            permissions = set(role.agent_permissions or [])
            print(f"   {name}: {len(permissions)}个权限")
            
            # 检查是否能创建下级角色
            for j in range(i + 1, len(roles_hierarchy)):
                lower_name, lower_role = roles_hierarchy[j]
                if lower_role:
                    lower_permissions = set(lower_role.agent_permissions or [])
                    
                    can_create = (
                        len(lower_permissions) < len(permissions) and
                        lower_permissions.issubset(permissions)
                    )
                    
                    print(f"     -> 能否创建{lower_name}: {can_create}")
                    if can_create:
                        print(f"        ✅ 权限数量: {len(lower_permissions)} < {len(permissions)}")
                        print(f"        ✅ 权限子集: {lower_permissions.issubset(permissions)}")
                    else:
                        print(f"        ❌ 权限数量: {len(lower_permissions)} >= {len(permissions)}")
                        print(f"        ❌ 权限子集: {lower_permissions.issubset(permissions)}")
    
    print("\n🎉 代理角色层级权限修复完成！")
    
    # 显示最终的权限层级
    print("\n📊 最终权限层级:")
    print("   超级代理 (8个权限) -> 一级代理 (7个权限) -> 二级代理 (6个权限) -> 三级代理 (5个权限)")
    print("   现在二级代理只能创建三级代理，不能创建一级代理了！")


if __name__ == "__main__":
    asyncio.run(fix_agent_role_hierarchy())
