#!/usr/bin/env python3
"""
调试角色权限越级问题
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.admin import User, Role
from app.core.init_app import init_db


async def debug_role_permission_issue():
    """调试角色权限越级问题"""
    print("🔧 调试角色权限越级问题...")
    await init_db()
    
    # 1. 查看所有角色及其权限
    print("\n1️⃣ 查看所有角色及其权限...")
    all_roles = await Role.all()
    
    for role in all_roles:
        print(f"   角色: {role.name}")
        print(f"     - ID: {role.id}")
        print(f"     - 是否代理角色: {role.is_agent_role}")
        print(f"     - 代理权限: {role.agent_permissions}")
        print(f"     - 权限数量: {len(role.agent_permissions or [])}")
        print()
    
    # 2. 查看二级代理用户的角色和权限
    print("\n2️⃣ 查看二级代理用户的角色和权限...")
    ag2_user = await User.filter(username="ag2").first()
    
    if ag2_user:
        ag2_roles = await ag2_user.roles.all()
        print(f"   ag2用户角色:")
        
        current_user_permissions = set()
        for role in ag2_roles:
            print(f"     - {role.name} (ID: {role.id})")
            print(f"       代理权限: {role.agent_permissions}")
            if role.is_agent_role and role.agent_permissions:
                current_user_permissions.update(role.agent_permissions)
        
        print(f"   ag2用户总权限: {current_user_permissions}")
        print(f"   权限数量: {len(current_user_permissions)}")
    else:
        print("   ❌ 没有找到ag2用户")
    
    # 3. 模拟可创建角色的逻辑
    print("\n3️⃣ 模拟ag2用户可创建角色的逻辑...")
    
    if ag2_user:
        user_roles = await ag2_user.roles.all()
        
        # 检查是否有创建下级代理的权限
        can_create_agent = False
        current_user_permissions = set()
        for role in user_roles:
            if role.is_agent_role and role.agent_permissions:
                current_user_permissions.update(role.agent_permissions)
                if "CREATE_SUBORDINATE_AGENT" in role.agent_permissions:
                    can_create_agent = True
        
        print(f"   ag2是否有创建代理权限: {can_create_agent}")
        print(f"   ag2的权限集合: {current_user_permissions}")
        print(f"   ag2的权限数量: {len(current_user_permissions)}")
        
        # 检查每个角色是否可以创建
        print("\n   检查每个角色是否可以创建:")
        for role in all_roles:
            if role.name == "普通用户":
                print(f"     ✅ {role.name} - 总是可以创建")
            elif can_create_agent and role.is_agent_role and role.name != "管理员":
                target_permissions = set(role.agent_permissions or [])
                
                # 检查权限条件
                is_subset = target_permissions.issubset(current_user_permissions)
                is_less_permissions = len(target_permissions) < len(current_user_permissions)
                
                print(f"     🔍 {role.name}:")
                print(f"         目标权限: {target_permissions}")
                print(f"         目标权限数量: {len(target_permissions)}")
                print(f"         是否为子集: {is_subset}")
                print(f"         权限数量更少: {is_less_permissions}")
                
                if is_less_permissions and is_subset:
                    print(f"         ✅ 可以创建")
                else:
                    print(f"         ❌ 不能创建")
            else:
                print(f"     ❌ {role.name} - 不能创建（非代理角色或管理员）")
    
    # 4. 检查一级代理和三级代理的权限对比
    print("\n4️⃣ 检查一级代理和三级代理的权限对比...")
    
    level1_role = await Role.filter(name="一级代理").first()
    level3_role = await Role.filter(name="三级代理").first()
    
    if level1_role and level3_role:
        level1_permissions = set(level1_role.agent_permissions or [])
        level3_permissions = set(level3_role.agent_permissions or [])
        
        print(f"   一级代理权限: {level1_permissions}")
        print(f"   一级代理权限数量: {len(level1_permissions)}")
        print(f"   三级代理权限: {level3_permissions}")
        print(f"   三级代理权限数量: {len(level3_permissions)}")
        
        # 检查二级代理是否应该能创建一级代理
        print(f"\n   二级代理是否应该能创建一级代理:")
        print(f"     一级代理权限是否为二级代理权限子集: {level1_permissions.issubset(current_user_permissions)}")
        print(f"     一级代理权限数量是否更少: {len(level1_permissions) < len(current_user_permissions)}")
        
        # 检查二级代理是否应该能创建三级代理
        print(f"\n   二级代理是否应该能创建三级代理:")
        print(f"     三级代理权限是否为二级代理权限子集: {level3_permissions.issubset(current_user_permissions)}")
        print(f"     三级代理权限数量是否更少: {len(level3_permissions) < len(current_user_permissions)}")
    
    print("\n🎉 角色权限调试完成！")


if __name__ == "__main__":
    asyncio.run(debug_role_permission_issue())
