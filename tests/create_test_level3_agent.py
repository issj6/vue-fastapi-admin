#!/usr/bin/env python3
"""
创建三级代理测试用户
"""

import asyncio
import aiohttp
import json


async def create_test_level3_agent():
    """创建三级代理测试用户"""
    base_url = "http://localhost:9999"
    
    async with aiohttp.ClientSession() as session:
        print("🔧 创建三级代理测试用户...")
        
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
        
        # 2. 获取三级代理角色ID
        print("\n2️⃣ 获取三级代理角色ID...")
        
        async with session.get(f"{base_url}/api/v1/role/list?page=1&page_size=50", headers=ag2_headers) as resp:
            result = await resp.json()
            all_roles = result['data']
            level3_role_id = None
            for role in all_roles:
                if role['name'] == '三级代理':
                    level3_role_id = role['id']
                    break
        
        if not level3_role_id:
            print("   ❌ 未找到三级代理角色")
            return
        
        print(f"   ✅ 找到三级代理角色ID: {level3_role_id}")
        
        # 3. 创建三级代理用户
        print("\n3️⃣ 创建三级代理用户...")
        
        create_user_data = {
            "username": "ag3",
            "email": "ag3@example.com",
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
                print(f"   ✅ 成功创建三级代理用户 ag3")
            else:
                print(f"   ❌ 创建三级代理用户失败")
        
        print("\n🎉 三级代理用户创建完成！")


if __name__ == "__main__":
    asyncio.run(create_test_level3_agent())
