#!/usr/bin/env python3
"""
测试ag1用户创建用户功能
"""

import asyncio
import aiohttp
import json


async def test_ag1_create_user():
    """测试ag1用户创建用户功能"""
    base_url = "http://localhost:9999"
    
    async with aiohttp.ClientSession() as session:
        print("🔧 测试ag1用户创建用户功能...")
        
        # 1. 登录获取token
        print("\n1️⃣ ag1用户登录...")
        login_data = {
            "username": "ag1",
            "password": "123456"
        }
        
        async with session.post(f"{base_url}/api/v1/base/access_token", json=login_data) as resp:
            if resp.status == 200:
                result = await resp.json()
                token = result['data']['access_token']
                print(f"✅ ag1登录成功，获取到token")
            else:
                result = await resp.text()
                print(f"❌ ag1登录失败: {resp.status} - {result}")
                return
        
        headers = {"token": token}
        
        # 2. 测试获取角色列表（创建用户时需要）
        print("\n2️⃣ 测试获取角色列表...")
        async with session.get(f"{base_url}/api/v1/role/list?page=1&page_size=10", headers=headers) as resp:
            if resp.status == 200:
                result = await resp.json()
                # 检查数据结构
                if 'data' in result:
                    if isinstance(result['data'], list):
                        roles = result['data']
                    elif isinstance(result['data'], dict) and 'items' in result['data']:
                        roles = result['data']['items']
                    else:
                        roles = result['data']
                else:
                    roles = []
                print(f"✅ 角色列表获取成功，共 {len(roles)} 个角色")
                for role in roles:
                    print(f"   - {role['name']} (ID: {role['id']}, 代理角色: {role.get('is_agent_role', False)})")
            else:
                result = await resp.text()
                print(f"❌ 角色列表获取失败: {resp.status} - {result}")
                return
        
        # 3. 测试创建用户API
        print("\n3️⃣ 测试创建用户API...")
        
        # 找一个合适的角色ID（二级代理或普通用户）
        suitable_role_id = None
        for role in roles:
            if role['name'] in ['二级代理', '普通用户'] or not role.get('is_agent_role', False):
                suitable_role_id = role['id']
                print(f"   选择角色: {role['name']} (ID: {role['id']})")
                break
        
        if not suitable_role_id:
            print("   ⚠️  未找到合适的角色，使用第一个角色")
            suitable_role_id = roles[0]['id'] if roles else 1
        
        import time
        timestamp = int(time.time()) % 10000  # 只取后4位，确保用户名不超过20字符
        create_user_data = {
            "username": f"ag1_test_{timestamp}",  # 最多12个字符
            "email": f"ag1_test_{timestamp}@example.com",
            "password": "123456",
            "is_active": True,
            "role_ids": [suitable_role_id],
            "school": "测试学校",
            "major": "测试专业"
        }
        
        async with session.post(f"{base_url}/api/v1/user/create", json=create_user_data, headers=headers) as resp:
            result_text = await resp.text()
            print(f"   📋 创建用户请求数据: {create_user_data}")
            print(f"   📋 响应状态: {resp.status}")
            print(f"   📋 响应内容: {result_text}")

            if resp.status == 200:
                result = json.loads(result_text)
                print(f"✅ 用户创建成功: {result.get('msg', '成功')}")
            else:
                print(f"❌ 用户创建失败: {resp.status} - {result_text}")

                # 如果是权限问题，详细分析
                if resp.status == 403:
                    print("   🔍 权限问题分析:")
                    print("   - 检查代理权限映射是否正确配置")
                    print("   - 检查权限验证逻辑是否正确")
                elif resp.status == 500:
                    print("   🔍 服务器错误分析:")
                    print("   - 可能是数据验证错误")
                    print("   - 可能是数据库约束错误")
                    print("   - 检查后端日志获取详细错误信息")
        
        # 4. 测试用户菜单（检查前端权限控制）
        print("\n4️⃣ 测试用户菜单...")
        async with session.get(f"{base_url}/api/v1/base/usermenu", headers=headers) as resp:
            if resp.status == 200:
                result = await resp.json()
                menus = result['data']
                print(f"✅ 用户菜单获取成功，共 {len(menus)} 个菜单:")
                for menu in menus:
                    print(f"   - {menu['name']} (路径: {menu['path']})")
                    if menu.get('children'):
                        for child in menu['children']:
                            print(f"     └─ {child['name']} (路径: {child['path']})")
            else:
                result = await resp.text()
                print(f"❌ 用户菜单获取失败: {resp.status} - {result}")
        
        # 5. 测试用户API权限
        print("\n5️⃣ 测试用户API权限...")
        async with session.get(f"{base_url}/api/v1/base/userapi", headers=headers) as resp:
            if resp.status == 200:
                result = await resp.json()
                apis = result['data']
                print(f"✅ 用户API权限获取成功，共 {len(apis)} 个API权限")
                
                # 检查是否包含创建用户相关的API
                create_user_apis = [api for api in apis if 'user/create' in api or 'role/list' in api]
                if create_user_apis:
                    print("   ✅ 包含创建用户相关的API权限:")
                    for api in create_user_apis:
                        print(f"     - {api}")
                else:
                    print("   ❌ 不包含创建用户相关的API权限")
            else:
                result = await resp.text()
                print(f"❌ 用户API权限获取失败: {resp.status} - {result}")
        
        print("\n✅ ag1用户创建用户功能测试完成")


if __name__ == "__main__":
    asyncio.run(test_ag1_create_user())
