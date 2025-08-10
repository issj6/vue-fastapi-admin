#!/usr/bin/env python3
"""
测试前端路由和页面访问
"""

import asyncio
import aiohttp
import json


async def test_frontend_routes():
    """测试前端路由和页面访问"""
    base_url = "http://localhost:9999"
    
    async with aiohttp.ClientSession() as session:
        print("🔧 测试前端路由和页面访问...")
        
        # 1. 测试ag2用户登录并获取菜单
        print("\n1️⃣ ag2用户登录并获取菜单...")
        login_data = {"username": "ag2", "password": "123456"}
        async with session.post(f"{base_url}/api/v1/base/access_token", json=login_data) as resp:
            if resp.status == 200:
                result = await resp.json()
                ag2_token = result['data']['access_token']
                print(f"✅ ag2登录成功")
            else:
                print(f"❌ ag2登录失败")
                return
        
        ag2_headers = {"token": ag2_token}
        
        # 2. 获取用户菜单数据
        async with session.get(f"{base_url}/api/v1/base/usermenu", headers=ag2_headers) as resp:
            if resp.status == 200:
                result = await resp.json()
                menus = result['data']
                print(f"✅ 菜单数据获取成功:")
                print(json.dumps(menus, indent=2, ensure_ascii=False))
            else:
                result = await resp.text()
                print(f"❌ 获取菜单失败: {resp.status} - {result}")
        
        # 3. 测试访问工作台页面
        print("\n2️⃣ 测试访问工作台页面...")
        async with session.get(f"{base_url}/workbench", headers=ag2_headers) as resp:
            print(f"   工作台页面状态码: {resp.status}")
            if resp.status == 200:
                print("   ✅ 工作台页面可访问")
            else:
                print(f"   ❌ 工作台页面访问失败")
        
        # 4. 测试访问系统管理页面
        print("\n3️⃣ 测试访问系统管理页面...")
        async with session.get(f"{base_url}/system", headers=ag2_headers) as resp:
            print(f"   系统管理页面状态码: {resp.status}")
            if resp.status == 200:
                print("   ✅ 系统管理页面可访问")
            else:
                print(f"   ❌ 系统管理页面访问失败")
        
        # 5. 测试访问用户管理页面
        print("\n4️⃣ 测试访问用户管理页面...")
        async with session.get(f"{base_url}/system/user", headers=ag2_headers) as resp:
            print(f"   用户管理页面状态码: {resp.status}")
            if resp.status == 200:
                print("   ✅ 用户管理页面可访问")
            else:
                print(f"   ❌ 用户管理页面访问失败")
        
        print("\n🎉 前端路由测试完成！")


if __name__ == "__main__":
    asyncio.run(test_frontend_routes())
