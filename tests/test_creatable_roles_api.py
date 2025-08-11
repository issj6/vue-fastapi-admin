#!/usr/bin/env python3
"""
测试可创建角色API
"""

import asyncio
import aiohttp
import json


async def test_creatable_roles_api():
    """测试可创建角色API"""
    base_url = "http://localhost:9999"
    
    async with aiohttp.ClientSession() as session:
        print("🔧 测试可创建角色API...")
        
        # 1. 二级代理登录
        print("\n1️⃣ 二级代理登录...")
        ag2_login_data = {"username": "ag2", "password": "123456"}
        
        async with session.post(f"{base_url}/api/v1/base/admin_access_token", json=ag2_login_data) as resp:
            if resp.status == 200:
                result = await resp.json()
                ag2_token = result['data']['access_token']
                ag2_headers = {"token": ag2_token}
                print(f"   ✅ 二级代理登录成功: {result['data']['username']}")
            else:
                result_text = await resp.text()
                print(f"   ❌ 二级代理登录失败: {resp.status} - {result_text}")
                return
        
        # 2. 获取二级代理可创建的角色
        print("\n2️⃣ 获取二级代理可创建的角色...")
        
        async with session.get(f"{base_url}/api/v1/role/creatable", headers=ag2_headers) as resp:
            if resp.status == 200:
                result = await resp.json()
                creatable_roles = result['data']
                
                print(f"   ✅ 成功获取可创建角色列表:")
                for role in creatable_roles:
                    agent_permissions = role.get('agent_permissions') or []
                    print(f"     - {role['name']} (ID: {role['id']})")
                    print(f"       代理权限: {agent_permissions}")
                    print(f"       权限数量: {len(agent_permissions)}")
                
                # 检查是否包含一级代理
                level1_in_list = any(role['name'] == '一级代理' for role in creatable_roles)
                level3_in_list = any(role['name'] == '三级代理' for role in creatable_roles)
                
                print(f"\n   🔍 权限检查结果:")
                print(f"     一级代理在列表中: {level1_in_list} {'❌ 不应该出现' if level1_in_list else '✅ 正确'}")
                print(f"     三级代理在列表中: {level3_in_list} {'✅ 正确' if level3_in_list else '❌ 应该出现'}")
                
            else:
                result_text = await resp.text()
                print(f"   ❌ 获取可创建角色失败: {resp.status} - {result_text}")
        
        # 3. 测试尝试创建一级代理用户（应该被拒绝）
        print("\n3️⃣ 测试尝试创建一级代理用户...")
        
        # 获取一级代理角色ID
        async with session.get(f"{base_url}/api/v1/role/list?page=1&page_size=50", headers=ag2_headers) as resp:
            result = await resp.json()
            all_roles = result['data']
            level1_role_id = None
            for role in all_roles:
                if role['name'] == '一级代理':
                    level1_role_id = role['id']
                    break
        
        if level1_role_id:
            create_user_data = {
                "username": "test_level1_user",
                "email": "test_level1@example.com",
                "password": "123456",
                "role_ids": [level1_role_id],
                "school": "测试学校",
                "major": "测试专业"
            }
            
            async with session.post(f"{base_url}/api/v1/user/create", json=create_user_data, headers=ag2_headers) as resp:
                result_text = await resp.text()
                print(f"   状态码: {resp.status}")
                print(f"   响应: {result_text}")
                
                if resp.status == 403:
                    print(f"   ✅ 正确拒绝创建一级代理用户")
                else:
                    print(f"   ❌ 权限验证失败，应该拒绝但允许了创建")
        
        # 4. 测试创建三级代理用户（应该成功）
        print("\n4️⃣ 测试创建三级代理用户...")
        
        # 获取三级代理角色ID
        level3_role_id = None
        for role in all_roles:
            if role['name'] == '三级代理':
                level3_role_id = role['id']
                break
        
        if level3_role_id:
            import time
            timestamp = int(time.time()) % 10000  # 只取后4位
            create_user_data = {
                "username": f"test_l3_{timestamp}",
                "email": f"test_l3_{timestamp}@example.com",
                "password": "123456",
                "role_ids": [level3_role_id],
                "school": "测试学校",
                "major": "测试专业"
            }
            
            async with session.post(f"{base_url}/api/v1/user/create", json=create_user_data, headers=ag2_headers) as resp:
                result_text = await resp.text()
                print(f"   状态码: {resp.status}")
                print(f"   响应: {result_text}")
                
                if resp.status == 200:
                    print(f"   ✅ 成功创建三级代理用户")
                    
                    # 删除测试用户
                    try:
                        result = json.loads(result_text)
                        # 查找刚创建的用户并删除
                        async with session.get(f"{base_url}/api/v1/user/list?page=1&page_size=50", headers=ag2_headers) as resp:
                            users_result = await resp.json()
                            for user in users_result['data']:
                                if user['username'].startswith('test_l3_'):
                                    await session.delete(f"{base_url}/api/v1/user/delete?user_id={user['id']}", headers=ag2_headers)
                                    print(f"   🗑️ 已删除测试用户: {user['username']}")
                                    break
                    except:
                        pass
                else:
                    print(f"   ❌ 创建三级代理用户失败")
        
        print("\n🎉 可创建角色API测试完成！")


if __name__ == "__main__":
    asyncio.run(test_creatable_roles_api())
