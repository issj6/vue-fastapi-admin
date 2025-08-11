#!/usr/bin/env python3
"""
测试超级代理权限，验证是否能创建同级超级代理
"""

import asyncio
import aiohttp
import json


async def test_super_agent_permissions():
    """测试超级代理权限"""
    base_url = "http://localhost:9999"
    
    async with aiohttp.ClientSession() as session:
        print("🔧 测试超级代理权限...")
        
        # 1. 管理员登录创建超级代理用户
        print("\n1️⃣ 管理员登录...")
        admin_login_data = {"username": "admin", "password": "123456"}
        
        async with session.post(f"{base_url}/api/v1/base/admin_access_token", json=admin_login_data) as resp:
            if resp.status == 200:
                result = await resp.json()
                admin_token = result['data']['access_token']
                admin_headers = {"token": admin_token}
                print(f"   ✅ 管理员登录成功")
            else:
                result_text = await resp.text()
                print(f"   ❌ 管理员登录失败: {resp.status} - {result_text}")
                return
        
        # 2. 获取超级代理角色ID
        print("\n2️⃣ 获取超级代理角色ID...")
        
        async with session.get(f"{base_url}/api/v1/role/list?page=1&page_size=50", headers=admin_headers) as resp:
            result = await resp.json()
            all_roles = result['data']
            super_agent_role_id = None
            for role in all_roles:
                if role['name'] == '超级代理':
                    super_agent_role_id = role['id']
                    break
        
        if not super_agent_role_id:
            print("   ❌ 未找到超级代理角色")
            return
        
        print(f"   ✅ 找到超级代理角色ID: {super_agent_role_id}")
        
        # 3. 创建超级代理用户
        print("\n3️⃣ 创建超级代理用户...")
        
        create_user_data = {
            "username": "super_agent",
            "email": "super_agent@example.com",
            "password": "123456",
            "role_ids": [super_agent_role_id],
            "school": "测试学校",
            "major": "测试专业"
        }
        
        async with session.post(f"{base_url}/api/v1/user/create", json=create_user_data, headers=admin_headers) as resp:
            result_text = await resp.text()
            print(f"   状态码: {resp.status}")
            
            if resp.status == 200:
                print(f"   ✅ 成功创建超级代理用户")
            elif resp.status == 400 and "already exists" in result_text:
                print(f"   ⚠️ 超级代理用户已存在，继续测试")
            else:
                print(f"   ❌ 创建超级代理用户失败: {result_text}")
                return
        
        # 4. 超级代理登录
        print("\n4️⃣ 超级代理登录...")
        super_agent_login_data = {"username": "super_agent", "password": "123456"}
        
        async with session.post(f"{base_url}/api/v1/base/admin_access_token", json=super_agent_login_data) as resp:
            if resp.status == 200:
                result = await resp.json()
                super_agent_token = result['data']['access_token']
                super_agent_headers = {"token": super_agent_token}
                print(f"   ✅ 超级代理登录成功")
            else:
                result_text = await resp.text()
                print(f"   ❌ 超级代理登录失败: {resp.status} - {result_text}")
                return
        
        # 5. 测试超级代理可创建的角色
        print("\n5️⃣ 测试超级代理可创建的角色...")
        
        async with session.get(f"{base_url}/api/v1/role/creatable", headers=super_agent_headers) as resp:
            if resp.status == 200:
                result = await resp.json()
                creatable_roles = result['data']
                
                print(f"   ✅ 超级代理可创建角色列表 ({len(creatable_roles)}个):")
                
                has_super_agent = False
                for role in creatable_roles:
                    level_desc = {
                        -1: "超级管理员",
                        0: "超级代理", 
                        1: "一级代理",
                        2: "二级代理",
                        3: "三级代理",
                        99: "普通用户"
                    }.get(role.get('user_level'), f"未知层级({role.get('user_level')})")
                    
                    print(f"     - {role['name']} (层级 {role.get('user_level')}) - {level_desc}")
                    
                    if role['name'] == '超级代理':
                        has_super_agent = True
                
                print(f"\n   🔍 权限控制分析:")
                if has_super_agent:
                    print(f"     ❌ 超级代理不应该能创建同级的超级代理角色")
                else:
                    print(f"     ✅ 超级代理正确无法创建同级的超级代理角色")
                
            else:
                result_text = await resp.text()
                print(f"   ❌ 获取可创建角色失败: {resp.status} - {result_text}")
        
        # 6. 测试尝试创建超级代理用户
        print("\n6️⃣ 测试尝试创建超级代理用户...")
        
        test_create_data = {
            "username": "test_super_agent_2",
            "email": "test_super_agent_2@example.com",
            "password": "123456",
            "role_ids": [super_agent_role_id],
            "school": "测试学校",
            "major": "测试专业"
        }
        
        async with session.post(f"{base_url}/api/v1/user/create", json=test_create_data, headers=super_agent_headers) as resp:
            result_text = await resp.text()
            print(f"   状态码: {resp.status}")
            print(f"   响应: {result_text}")
            
            if resp.status == 403:
                print(f"   ✅ 正确拒绝超级代理创建同级用户")
            else:
                print(f"   ❌ 超级代理不应该能创建同级用户，但状态码是 {resp.status}")
        
        print("\n🎉 超级代理权限测试完成！")


if __name__ == "__main__":
    asyncio.run(test_super_agent_permissions())
