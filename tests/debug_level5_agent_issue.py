#!/usr/bin/env python3
"""
调试五级代理无法创建六级代理的问题
"""

import asyncio
import aiohttp
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.admin import User, Role
from app.core.init_app import init_db


async def debug_level5_agent_issue():
    """调试五级代理问题"""
    base_url = "http://localhost:9999"
    
    print("🔧 调试五级代理无法创建六级代理的问题...")
    
    # 1. 检查数据库中的角色情况
    print("\n1️⃣ 检查数据库中的角色...")
    await init_db()
    
    all_roles = await Role.all().order_by('user_level')
    print(f"   📋 当前系统角色:")
    for role in all_roles:
        print(f"     - {role.name} (层级 {role.user_level}, is_agent_role: {role.is_agent_role})")
    
    # 2. 检查五级代理角色的权限
    level5_role = await Role.filter(user_level=5).first()
    if level5_role:
        print(f"\n   🔍 五级代理角色详情:")
        print(f"     - 名称: {level5_role.name}")
        print(f"     - 层级: {level5_role.user_level}")
        print(f"     - 是否代理角色: {level5_role.is_agent_role}")
        print(f"     - 代理权限: {level5_role.agent_permissions}")
    else:
        print(f"\n   ❌ 未找到五级代理角色")
        return
    
    # 3. 检查六级代理角色是否存在
    level6_role = await Role.filter(user_level=6).first()
    if level6_role:
        print(f"\n   ✅ 六级代理角色存在:")
        print(f"     - 名称: {level6_role.name}")
        print(f"     - 层级: {level6_role.user_level}")
        print(f"     - 是否代理角色: {level6_role.is_agent_role}")
    else:
        print(f"\n   ❌ 六级代理角色不存在，需要先创建")
        
        # 管理员创建六级代理角色
        print(f"\n2️⃣ 管理员创建六级代理角色...")
        
        async with aiohttp.ClientSession() as session:
            admin_login_data = {"username": "admin", "password": "123456"}
            
            async with session.post(f"{base_url}/api/v1/base/admin_access_token", json=admin_login_data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    admin_token = result['data']['access_token']
                    admin_headers = {"token": admin_token}
                    print(f"   ✅ 管理员登录成功")
                else:
                    print(f"   ❌ 管理员登录失败")
                    return
            
            create_role_data = {
                "name": "六级代理",
                "desc": "六级代理角色，只能创建普通用户",
                "user_level": 6,
                "is_agent_role": True,
                "agent_permissions": [
                    "VIEW_SUBORDINATE_USERS",
                    "CREATE_USER",
                    "MODIFY_SUBORDINATE_USERS",
                    "MANAGE_POINTS"
                ]
            }
            
            async with session.post(f"{base_url}/api/v1/role/create", json=create_role_data, headers=admin_headers) as resp:
                if resp.status == 200:
                    print(f"   ✅ 成功创建六级代理角色")
                    level6_role = await Role.filter(user_level=6).first()
                elif resp.status == 400 and "already exists" in await resp.text():
                    print(f"   ⚠️ 六级代理角色已存在")
                    level6_role = await Role.filter(user_level=6).first()
                else:
                    print(f"   ❌ 创建六级代理角色失败: {await resp.text()}")
                    return
    
    # 4. 检查五级代理用户
    print(f"\n3️⃣ 检查五级代理用户...")
    
    level5_users = await User.filter(roles__user_level=5).prefetch_related('roles')
    if level5_users:
        for user in level5_users:
            print(f"   📋 五级代理用户: {user.username}")
            user_roles = await user.roles.all()
            for role in user_roles:
                print(f"     - 角色: {role.name} (层级 {role.user_level})")
                print(f"     - 权限: {role.agent_permissions}")
    else:
        print(f"   ❌ 未找到五级代理用户，需要先创建")
        
        # 创建五级代理用户
        async with aiohttp.ClientSession() as session:
            admin_login_data = {"username": "admin", "password": "123456"}
            
            async with session.post(f"{base_url}/api/v1/base/admin_access_token", json=admin_login_data) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    admin_token = result['data']['access_token']
                    admin_headers = {"token": admin_token}
                else:
                    print(f"   ❌ 管理员登录失败")
                    return
            
            create_user_data = {
                "username": "ag5",
                "email": "ag5@example.com",
                "password": "123456",
                "role_ids": [level5_role.id],
                "school": "测试学校",
                "major": "测试专业"
            }
            
            async with session.post(f"{base_url}/api/v1/user/create", json=create_user_data, headers=admin_headers) as resp:
                if resp.status == 200:
                    print(f"   ✅ 成功创建五级代理用户")
                elif resp.status == 400 and "already exists" in await resp.text():
                    print(f"   ⚠️ 五级代理用户已存在")
                else:
                    print(f"   ❌ 创建五级代理用户失败: {await resp.text()}")
                    return
    
    # 5. 测试五级代理的可创建角色
    print(f"\n4️⃣ 测试五级代理的可创建角色...")
    
    async with aiohttp.ClientSession() as session:
        # 五级代理登录
        ag5_login_data = {"username": "ag5", "password": "123456"}
        
        async with session.post(f"{base_url}/api/v1/base/admin_access_token", json=ag5_login_data) as resp:
            if resp.status == 200:
                result = await resp.json()
                ag5_token = result['data']['access_token']
                ag5_headers = {"token": ag5_token}
                print(f"   ✅ 五级代理登录成功")
            else:
                print(f"   ❌ 五级代理登录失败: {await resp.text()}")
                return
        
        # 获取可创建的角色
        async with session.get(f"{base_url}/api/v1/role/creatable", headers=ag5_headers) as resp:
            if resp.status == 200:
                result = await resp.json()
                creatable_roles = result['data']
                
                print(f"\n   📋 五级代理可创建角色 ({len(creatable_roles)}个):")
                for role in creatable_roles:
                    print(f"     - {role['name']} (层级 {role.get('user_level')})")
                
                # 检查是否包含六级代理
                has_level6 = any(r.get('user_level') == 6 for r in creatable_roles)
                has_normal_user = any(r.get('user_level') == 99 for r in creatable_roles)
                
                print(f"\n   🔍 权限验证:")
                if has_level6:
                    print(f"     ✅ 五级代理可以创建六级代理")
                else:
                    print(f"     ❌ 五级代理无法创建六级代理 - 这是问题所在！")
                
                if has_normal_user:
                    print(f"     ✅ 五级代理可以创建普通用户")
                else:
                    print(f"     ❌ 五级代理无法创建普通用户")
                
                # 分析问题原因
                print(f"\n   🔍 问题分析:")
                print(f"     - 五级代理层级: 5")
                print(f"     - 期望创建层级: 6")
                print(f"     - 六级代理角色存在: {'是' if level6_role else '否'}")
                print(f"     - 五级代理有CREATE_SUBORDINATE_AGENT权限: {'是' if level5_role.agent_permissions and 'CREATE_SUBORDINATE_AGENT' in level5_role.agent_permissions else '否'}")
                
            else:
                print(f"   ❌ 获取可创建角色失败: {await resp.text()}")
    
    print(f"\n🎉 调试完成！")


if __name__ == "__main__":
    asyncio.run(debug_level5_agent_issue())
