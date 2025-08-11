#!/usr/bin/env python3
"""
测试API权限修复
通过HTTP请求测试一级代理用户是否能正常访问用户管理API
"""

import asyncio
import aiohttp
import json


async def test_api_permissions():
    """测试API权限"""
    base_url = "http://localhost:9999"
    
    print("🔧 测试API权限修复...")
    
    async with aiohttp.ClientSession() as session:
        # 1. 登录获取token
        print("\n1️⃣ 登录获取token...")
        login_data = {
            "username": "test001",
            "password": "123456"  # 假设密码是123456
        }
        
        async with session.post(f"{base_url}/api/v1/base/access_token", json=login_data) as resp:
            if resp.status == 200:
                result = await resp.json()
                if result.get("code") == 200:
                    token = result["data"]["access_token"]
                    print(f"✅ 登录成功，获取到token: {token[:20]}...")
                else:
                    print(f"❌ 登录失败: {result}")
                    return
            else:
                error_text = await resp.text()
                print(f"❌ 登录请求失败: {resp.status} - {error_text}")
                return
        
        # 2. 测试用户信息接口
        print("\n2️⃣ 测试用户信息接口...")
        headers = {"token": token}
        
        async with session.get(f"{base_url}/api/v1/base/userinfo", headers=headers) as resp:
            if resp.status == 200:
                result = await resp.json()
                print(f"✅ 用户信息获取成功: {result['data']['username']}")
            else:
                print(f"❌ 用户信息获取失败: {resp.status}")
        
        # 3. 测试用户列表接口（之前失败的接口）
        print("\n3️⃣ 测试用户列表接口...")
        
        async with session.get(f"{base_url}/api/v1/user/list?page=1&page_size=10", headers=headers) as resp:
            if resp.status == 200:
                result = await resp.json()
                print(f"✅ 用户列表获取成功，共 {result.get('total', 0)} 个用户")
            else:
                result = await resp.text()
                print(f"❌ 用户列表获取失败: {resp.status} - {result}")
        
        # 4. 测试角色列表接口（之前失败的接口）
        print("\n4️⃣ 测试角色列表接口...")
        
        async with session.get(f"{base_url}/api/v1/role/list?page=1&page_size=9999", headers=headers) as resp:
            if resp.status == 200:
                result = await resp.json()
                print(f"✅ 角色列表获取成功，共 {result.get('total', 0)} 个角色")
            else:
                result = await resp.text()
                print(f"❌ 角色列表获取失败: {resp.status} - {result}")
        
        # 5. 测试用户菜单接口
        print("\n5️⃣ 测试用户菜单接口...")

        async with session.get(f"{base_url}/api/v1/base/usermenu", headers=headers) as resp:
            if resp.status == 200:
                result = await resp.json()
                menus = result['data']
                print(f"✅ 用户菜单获取成功，共 {len(menus)} 个菜单:")
                for menu in menus:
                    print(f"   - {menu['name']} (路径: {menu['path']}, 组件: {menu.get('component', 'N/A')})")
                    if menu.get('children'):
                        for child in menu['children']:
                            print(f"     └─ {child['name']} (路径: {child['path']}, 组件: {child.get('component', 'N/A')})")
            else:
                result = await resp.text()
                print(f"❌ 用户菜单获取失败: {resp.status} - {result}")
        
        # 6. 测试用户API权限接口
        print("\n6️⃣ 测试用户API权限接口...")
        
        async with session.get(f"{base_url}/api/v1/base/userapi", headers=headers) as resp:
            if resp.status == 200:
                result = await resp.json()
                apis = result['data']
                print(f"✅ 用户API权限获取成功，共 {len(apis)} 个API权限")
                # 检查关键API权限
                key_apis = [
                    "get/api/v1/user/list",
                    "get/api/v1/role/list"
                ]
                for api in key_apis:
                    if api in apis:
                        print(f"   ✅ 拥有权限: {api}")
                    else:
                        print(f"   ❌ 缺少权限: {api}")
            else:
                result = await resp.text()
                print(f"❌ 用户API权限获取失败: {resp.status} - {result}")
    
    print("\n✅ API权限测试完成")


if __name__ == "__main__":
    asyncio.run(test_api_permissions())
