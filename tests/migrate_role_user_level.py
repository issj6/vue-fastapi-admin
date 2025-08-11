#!/usr/bin/env python3
"""
数据库迁移：为角色添加user_level字段并设置正确的层级数字
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.admin import Role
from app.core.init_app import init_db


async def migrate_role_user_level():
    """为角色添加user_level字段并设置正确的层级数字"""
    print("🔄 开始角色层级迁移...")
    await init_db()
    
    # 定义角色层级映射
    role_level_mapping = {
        "管理员": -1,        # 超级管理员
        "超级代理": 1,       # 超级代理
        "一级代理": 2,       # 一级代理
        "二级代理": 3,       # 二级代理
        "三级代理": 4,       # 三级代理
        "普通用户": 99       # 普通用户
    }
    
    print("\n📊 角色层级定义:")
    print("   -1: 超级管理员（管理员）")
    print("    1: 超级代理")
    print("    2: 一级代理")
    print("    3: 二级代理")
    print("    4: 三级代理")
    print("   99: 普通用户")
    print("\n   规则：数字越小权限越高，只能创建层级数字大于自己的角色")
    
    # 检查当前角色状态
    print("\n1️⃣ 检查当前角色状态...")
    all_roles = await Role.all()
    
    for role in all_roles:
        current_level = getattr(role, 'user_level', None)
        expected_level = role_level_mapping.get(role.name, 99)
        
        print(f"   {role.name}:")
        print(f"     当前层级: {current_level}")
        print(f"     期望层级: {expected_level}")
        print(f"     需要更新: {current_level != expected_level}")
    
    # 更新角色层级
    print("\n2️⃣ 更新角色层级...")
    updated_count = 0
    
    for role in all_roles:
        expected_level = role_level_mapping.get(role.name, 99)
        current_level = getattr(role, 'user_level', None)
        
        if current_level != expected_level:
            old_level = current_level
            role.user_level = expected_level
            await role.save()
            updated_count += 1
            
            print(f"   ✅ 更新 {role.name}: {old_level} -> {expected_level}")
        else:
            print(f"   ⏭️ 跳过 {role.name}: 层级已正确 ({current_level})")
    
    # 验证层级关系
    print("\n3️⃣ 验证层级关系...")
    
    # 重新获取更新后的角色
    updated_roles = await Role.all().order_by('user_level')
    
    print("   角色层级排序（按权限从高到低）:")
    for role in updated_roles:
        level_desc = {
            -1: "超级管理员",
            1: "超级代理", 
            2: "一级代理",
            3: "二级代理",
            4: "三级代理",
            99: "普通用户"
        }.get(role.user_level, f"未知层级({role.user_level})")
        
        print(f"     {role.name} (层级 {role.user_level}) - {level_desc}")
    
    # 验证创建权限逻辑
    print("\n4️⃣ 验证创建权限逻辑...")
    
    agent_roles = [role for role in updated_roles if role.is_agent_role]
    
    for role in agent_roles:
        if role.agent_permissions and "CREATE_SUBORDINATE_AGENT" in role.agent_permissions:
            print(f"   {role.name} (层级 {role.user_level}) 可以创建的代理角色:")
            
            can_create_any = False
            for target_role in agent_roles:
                if target_role.user_level > role.user_level:
                    print(f"     ✅ {target_role.name} (层级 {target_role.user_level})")
                    can_create_any = True
                elif target_role.user_level <= role.user_level and target_role.name != role.name:
                    print(f"     ❌ {target_role.name} (层级 {target_role.user_level}) - 权限不足")
            
            if not can_create_any:
                print(f"     ⚠️ 无法创建任何代理角色（已是最低层级）")
    
    print(f"\n🎉 角色层级迁移完成！")
    print(f"   更新了 {updated_count} 个角色的层级设置")
    print(f"   现在三级代理（层级4）无法创建任何代理角色了！")
    
    # 显示最终的权限控制逻辑
    print("\n📋 最终权限控制逻辑:")
    print("   超级管理员(-1) -> 可创建所有角色")
    print("   超级代理(1) -> 可创建一级代理(2)、二级代理(3)、三级代理(4)")
    print("   一级代理(2) -> 可创建二级代理(3)、三级代理(4)")
    print("   二级代理(3) -> 可创建三级代理(4)")
    print("   三级代理(4) -> 无法创建任何代理角色 ✅")
    print("   所有角色 -> 可创建普通用户(99)")


if __name__ == "__main__":
    asyncio.run(migrate_role_user_level())
