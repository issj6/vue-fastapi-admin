#!/usr/bin/env python3
"""
测试权限层级修复效果
"""

import asyncio
import aiohttp
import json


async def test_permission_hierarchy():
    """测试权限层级修复效果"""
    base_url = "http://localhost:9999"
    
    async with aiohttp.ClientSession() as session:
        print("🔧 测试权限层级修复效果...")
        
        # 1. 测试ag1用户（一级代理）
        print("\n1️⃣ 测试ag1用户（一级代理）权限...")
        
        # 登录ag1用户
        login_data = {"username": "ag1", "password": "123456"}
        async with session.post(f"{base_url}/api/v1/base/access_token", json=login_data) as resp:
            if resp.status == 200:
                result = await resp.json()
                ag1_token = result['data']['access_token']
                print(f"✅ ag1登录成功")
            else:
                print(f"❌ ag1登录失败")
                return
        
        ag1_headers = {"token": ag1_token}
        
        # 测试获取可创建角色列表
        print("\n📋 测试ag1用户可创建的角色列表...")
        async with session.get(f"{base_url}/api/v1/role/creatable", headers=ag1_headers) as resp:
            if resp.status == 200:
                result = await resp.json()
                creatable_roles = result['data']
                print(f"✅ ag1可创建角色 (共{len(creatable_roles)}个):")
                for role in creatable_roles:
                    print(f"   - {role['name']} (ID: {role['id']})")
            else:
                result = await resp.text()
                print(f"❌ 获取可创建角色失败: {resp.status} - {result}")
        
        # 测试创建超级管理员用户（应该失败）
        print("\n🚫 测试ag1创建超级管理员用户（应该被拒绝）...")
        super_admin_data = {
            "username": "test_super",
            "email": "test_super@example.com",
            "password": "123456",
            "is_active": True,
            "is_superuser": True,  # 尝试设置为超级管理员
            "role_ids": [1],  # 管理员角色
            "school": "测试学校",
            "major": "测试专业"
        }
        
        async with session.post(f"{base_url}/api/v1/user/create", json=super_admin_data, headers=ag1_headers) as resp:
            result_text = await resp.text()
            if resp.status == 403:
                print(f"✅ 正确拒绝：{result_text}")
            else:
                print(f"❌ 安全漏洞：ag1成功创建了超级管理员用户！状态码: {resp.status}")
        
        # 测试创建高权限角色用户（应该失败）
        print("\n🚫 测试ag1创建管理员角色用户（应该被拒绝）...")
        admin_role_data = {
            "username": "test_admin",
            "email": "test_admin@example.com",
            "password": "123456",
            "is_active": True,
            "is_superuser": False,
            "role_ids": [1],  # 管理员角色（权限高于一级代理）
            "school": "测试学校",
            "major": "测试专业"
        }
        
        async with session.post(f"{base_url}/api/v1/user/create", json=admin_role_data, headers=ag1_headers) as resp:
            result_text = await resp.text()
            if resp.status == 403:
                print(f"✅ 正确拒绝：{result_text}")
            else:
                print(f"❌ 安全漏洞：ag1成功创建了管理员角色用户！状态码: {resp.status}")
        
        # 测试创建合法的低权限用户（应该成功）
        print("\n✅ 测试ag1创建普通用户（应该成功）...")
        normal_user_data = {
            "username": "test_normal",
            "email": "test_normal@example.com",
            "password": "123456",
            "is_active": True,
            "is_superuser": False,
            "role_ids": [2],  # 普通用户角色
            "school": "测试学校",
            "major": "测试专业"
        }
        
        async with session.post(f"{base_url}/api/v1/user/create", json=normal_user_data, headers=ag1_headers) as resp:
            result_text = await resp.text()
            if resp.status == 200:
                print(f"✅ 成功创建普通用户")
            else:
                print(f"❌ 创建普通用户失败: {resp.status} - {result_text}")
        
        # 2. 测试超级管理员权限
        print("\n2️⃣ 测试超级管理员权限...")
        
        # 登录admin用户（超级管理员）
        admin_login_data = {"username": "admin", "password": "123456"}
        async with session.post(f"{base_url}/api/v1/base/access_token", json=admin_login_data) as resp:
            if resp.status == 200:
                result = await resp.json()
                admin_token = result['data']['access_token']
                print(f"✅ admin登录成功")
            else:
                print(f"❌ admin登录失败")
                return
        
        admin_headers = {"token": admin_token}
        
        # 测试超级管理员获取所有角色
        print("\n📋 测试超级管理员获取所有角色...")
        async with session.get(f"{base_url}/api/v1/role/list?page=1&page_size=10", headers=admin_headers) as resp:
            if resp.status == 200:
                result = await resp.json()
                all_roles = result['data']
                print(f"✅ 超级管理员可访问所有角色 (共{len(all_roles)}个):")
                for role in all_roles:
                    print(f"   - {role['name']} (ID: {role['id']})")
            else:
                result = await resp.text()
                print(f"❌ 获取角色列表失败: {resp.status} - {result}")
        
        # 测试超级管理员创建超级管理员用户（应该成功）
        print("\n✅ 测试超级管理员创建超级管理员用户（应该成功）...")
        super_admin_by_admin_data = {
            "username": "test_super2",
            "email": "test_super2@example.com",
            "password": "123456",
            "is_active": True,
            "is_superuser": True,
            "role_ids": [1],
            "school": "测试学校",
            "major": "测试专业"
        }
        
        async with session.post(f"{base_url}/api/v1/user/create", json=super_admin_by_admin_data, headers=admin_headers) as resp:
            result_text = await resp.text()
            if resp.status == 200:
                print(f"✅ 超级管理员成功创建超级管理员用户")
            else:
                print(f"❌ 超级管理员创建超级管理员用户失败: {resp.status} - {result_text}")
        
        print("\n🎉 权限层级测试完成！")


if __name__ == "__main__":
    asyncio.run(test_permission_hierarchy())
