#!/usr/bin/env python3
"""
测试角色删除功能
"""

import asyncio
import aiohttp
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.admin import User, Role
from app.core.init_app import init_db


async def test_role_deletion():
    """测试角色删除功能"""
    base_url = "http://localhost:9999"
    
    print("🔧 测试角色删除功能...")
    
    # 1. 创建测试角色和用户
    print("\n1️⃣ 准备测试数据...")
    await init_db()
    
    # 创建测试角色
    test_role = await Role.filter(name="测试角色").first()
    if not test_role:
        test_role = await Role.create(
            name="测试角色",
            desc="用于测试删除功能的角色",
            user_level=10,
            is_agent_role=True,
            agent_permissions=["CREATE_USER"]
        )
        print(f"   ✅ 创建测试角色: {test_role.name}")
    else:
        print(f"   ✅ 测试角色已存在: {test_role.name}")
    
    async with aiohttp.ClientSession() as session:
        # 管理员登录
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
        
        # 创建测试用户
        test_users = []
        for i in range(3):
            username = f"test_user_{i+1}"
            email = f"test_user_{i+1}@example.com"
            
            # 检查用户是否已存在
            existing_user = await User.filter(username=username).first()
            if existing_user:
                await existing_user.delete()
                print(f"   🗑️ 删除已存在的测试用户: {username}")
            
            create_user_data = {
                "username": username,
                "email": email,
                "password": "123456",
                "role_ids": [test_role.id],
                "school": "测试学校",
                "major": "测试专业"
            }
            
            async with session.post(f"{base_url}/api/v1/user/create", json=create_user_data, headers=admin_headers) as resp:
                if resp.status == 200:
                    test_users.append(username)
                    print(f"   ✅ 创建测试用户: {username}")
                else:
                    print(f"   ❌ 创建测试用户失败: {username} - {await resp.text()}")
        
        print(f"   📊 创建了 {len(test_users)} 个测试用户")
        
        # 2. 测试检查角色用户数量接口
        print(f"\n2️⃣ 测试检查角色用户数量接口...")
        
        async with session.get(f"{base_url}/api/v1/role/check_users?role_id={test_role.id}", headers=admin_headers) as resp:
            if resp.status == 200:
                result = await resp.json()
                print(f"   ✅ 检查结果: {result}")
                
                data = result['data']
                print(f"   📋 角色名称: {data['role_name']}")
                print(f"   📋 关联用户数: {data['user_count']}")
            else:
                print(f"   ❌ 检查失败: {await resp.text()}")
        
        # 3. 测试删除有用户的角色（不强制删除）
        print(f"\n3️⃣ 测试删除有用户的角色（不强制删除）...")
        
        async with session.delete(f"{base_url}/api/v1/role/delete?role_id={test_role.id}", headers=admin_headers) as resp:
            result = await resp.json()
            print(f"   状态码: {resp.status}")
            print(f"   响应: {result}")
            
            if resp.status == 400 and result.get('data', {}).get('need_confirmation'):
                print(f"   ✅ 正确返回需要确认的提示")
            else:
                print(f"   ❌ 未正确处理有用户的角色删除")
        
        # 4. 测试强制删除角色及用户
        print(f"\n4️⃣ 测试强制删除角色及用户...")
        
        async with session.delete(f"{base_url}/api/v1/role/delete?role_id={test_role.id}&force_delete=true", headers=admin_headers) as resp:
            result = await resp.json()
            print(f"   状态码: {resp.status}")
            print(f"   响应: {result}")
            
            if resp.status == 200:
                print(f"   ✅ 成功删除角色及关联用户")
                
                # 验证角色和用户是否被删除
                role_exists = await Role.filter(id=test_role.id).exists()
                print(f"   📋 角色是否还存在: {role_exists}")
                
                remaining_users = 0
                for username in test_users:
                    user_exists = await User.filter(username=username).exists()
                    if user_exists:
                        remaining_users += 1
                
                print(f"   📋 剩余测试用户数: {remaining_users}")
                
                if not role_exists and remaining_users == 0:
                    print(f"   ✅ 角色和用户都已正确删除")
                else:
                    print(f"   ❌ 删除不完整")
            else:
                print(f"   ❌ 强制删除失败")
        
        # 5. 测试删除系统关键角色
        print(f"\n5️⃣ 测试删除系统关键角色...")
        
        # 获取管理员角色ID
        admin_role = await Role.filter(name="管理员").first()
        if admin_role:
            async with session.delete(f"{base_url}/api/v1/role/delete?role_id={admin_role.id}", headers=admin_headers) as resp:
                result = await resp.json()
                print(f"   状态码: {resp.status}")
                print(f"   响应: {result}")
                
                if resp.status == 400 and "系统关键角色不能删除" in result.get('msg', ''):
                    print(f"   ✅ 正确阻止删除系统关键角色")
                else:
                    print(f"   ❌ 未正确保护系统关键角色")
        
        print(f"\n🎉 角色删除功能测试完成！")


if __name__ == "__main__":
    asyncio.run(test_role_deletion())
