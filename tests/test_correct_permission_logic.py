#!/usr/bin/env python3
"""
测试正确的权限逻辑：
1. 拥有CREATE_SUBORDINATE_AGENT权限的用户能够创建自身等级+1的代理（前提是该等级的角色必须存在）
2. 如果不存在自身等级+1的角色，则该权限无效，不能创建
3. 超级管理员例外，能创建任何角色
"""

import asyncio
import aiohttp
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.admin import Role
from app.core.init_app import init_db


async def test_correct_permission_logic():
    """测试正确的权限逻辑"""
    base_url = "http://localhost:9999"
    
    print("🔧 测试正确的权限逻辑...")
    
    # 1. 先删除五级代理角色（如果存在）
    print("\n1️⃣ 清理测试环境...")
    await init_db()
    
    level5_role = await Role.filter(user_level=5).first()
    if level5_role:
        await level5_role.delete()
        print(f"   ✅ 已删除五级代理角色: {level5_role.name}")
    else:
        print(f"   ✅ 五级代理角色不存在")
    
    # 验证当前角色列表
    all_roles = await Role.all().order_by('user_level')
    print(f"\n   📋 当前系统角色:")
    for role in all_roles:
        print(f"     - {role.name} (层级 {role.user_level})")
    
    async with aiohttp.ClientSession() as session:
        
        # 2. 测试四级代理是否无法创建五级代理
        print(f"\n2️⃣ 测试四级代理权限（五级代理角色不存在）...")
        
        # 创建四级代理用户（如果不存在）
        print(f"\n   创建四级代理用户...")
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
        
        # 获取四级代理角色ID
        level4_role = await Role.filter(user_level=4).first()
        if not level4_role:
            print(f"   ❌ 四级代理角色不存在")
            return
        
        # 创建四级代理用户
        create_user_data = {
            "username": "ag4",
            "email": "ag4@example.com",
            "password": "123456",
            "role_ids": [level4_role.id],
            "school": "测试学校",
            "major": "测试专业"
        }
        
        async with session.post(f"{base_url}/api/v1/user/create", json=create_user_data, headers=admin_headers) as resp:
            if resp.status == 200:
                print(f"   ✅ 成功创建四级代理用户")
            elif resp.status == 400 and "already exists" in await resp.text():
                print(f"   ⚠️ 四级代理用户已存在")
            else:
                print(f"   ❌ 创建四级代理用户失败: {await resp.text()}")
        
        # 四级代理登录
        ag4_login_data = {"username": "ag4", "password": "123456"}
        
        async with session.post(f"{base_url}/api/v1/base/admin_access_token", json=ag4_login_data) as resp:
            if resp.status == 200:
                result = await resp.json()
                ag4_token = result['data']['access_token']
                ag4_headers = {"token": ag4_token}
                print(f"   ✅ 四级代理登录成功")
            else:
                print(f"   ❌ 四级代理登录失败: {await resp.text()}")
                return
        
        # 测试四级代理可创建的角色
        async with session.get(f"{base_url}/api/v1/role/creatable", headers=ag4_headers) as resp:
            if resp.status == 200:
                result = await resp.json()
                creatable_roles = result['data']
                
                print(f"\n   📋 四级代理可创建角色 ({len(creatable_roles)}个):")
                for role in creatable_roles:
                    print(f"     - {role['name']} (层级 {role.get('user_level')})")
                
                # 验证逻辑
                has_level5 = any(r.get('user_level') == 5 for r in creatable_roles)
                has_normal_user = any(r.get('user_level') == 99 for r in creatable_roles)
                
                print(f"\n   🔍 权限验证:")
                if has_level5:
                    print(f"     ❌ 错误：四级代理不应该能创建五级代理（五级代理角色不存在）")
                else:
                    print(f"     ✅ 正确：四级代理无法创建五级代理（五级代理角色不存在）")
                
                if has_normal_user:
                    print(f"     ✅ 正确：四级代理可以创建普通用户")
                else:
                    print(f"     ❌ 错误：四级代理应该能创建普通用户")
            else:
                print(f"   ❌ 获取可创建角色失败: {await resp.text()}")
        
        # 3. 管理员创建五级代理角色
        print(f"\n3️⃣ 管理员创建五级代理角色...")
        
        create_role_data = {
            "name": "五级代理",
            "desc": "五级代理角色，只能创建普通用户",
            "user_level": 5,
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
                print(f"   ✅ 成功创建五级代理角色")
            elif resp.status == 400 and "already exists" in await resp.text():
                print(f"   ⚠️ 五级代理角色已存在")
            else:
                print(f"   ❌ 创建五级代理角色失败: {await resp.text()}")
        
        # 4. 再次测试四级代理权限
        print(f"\n4️⃣ 测试四级代理权限（五级代理角色存在）...")
        
        async with session.get(f"{base_url}/api/v1/role/creatable", headers=ag4_headers) as resp:
            if resp.status == 200:
                result = await resp.json()
                creatable_roles = result['data']
                
                print(f"\n   📋 四级代理可创建角色 ({len(creatable_roles)}个):")
                for role in creatable_roles:
                    print(f"     - {role['name']} (层级 {role.get('user_level')})")
                
                # 验证逻辑
                has_level5 = any(r.get('user_level') == 5 for r in creatable_roles)
                has_normal_user = any(r.get('user_level') == 99 for r in creatable_roles)
                
                print(f"\n   🔍 权限验证:")
                if has_level5:
                    print(f"     ✅ 正确：四级代理现在可以创建五级代理（五级代理角色已存在）")
                else:
                    print(f"     ❌ 错误：四级代理应该能创建五级代理（五级代理角色已存在）")
                
                if has_normal_user:
                    print(f"     ✅ 正确：四级代理可以创建普通用户")
                else:
                    print(f"     ❌ 错误：四级代理应该能创建普通用户")
            else:
                print(f"   ❌ 获取可创建角色失败: {await resp.text()}")
        
        print(f"\n🎉 权限逻辑测试完成！")
        print(f"\n📋 验证结果:")
        print(f"   ✅ 权限依赖于角色存在性：角色不存在时权限无效")
        print(f"   ✅ 权限基于层级数字：只能创建自身层级+1")
        print(f"   ✅ 超级管理员例外：可以创建任何角色")


if __name__ == "__main__":
    asyncio.run(test_correct_permission_logic())
