#!/usr/bin/env python3
"""
测试前端角色删除功能
"""

import asyncio
import aiohttp
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.admin import User, Role
from app.core.init_app import init_db


async def test_frontend_role_deletion():
    """测试前端角色删除功能"""
    base_url = "http://localhost:9999"
    
    print("🔧 测试前端角色删除功能...")
    
    # 1. 创建测试角色和用户
    print("\n1️⃣ 准备测试数据...")
    await init_db()
    
    # 创建测试角色
    test_role = await Role.filter(name="前端测试角色").first()
    if not test_role:
        test_role = await Role.create(
            name="前端测试角色",
            desc="用于测试前端删除功能的角色",
            user_level=15,
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
        for i in range(2):
            username = f"frontend_test_user_{i+1}"
            email = f"frontend_test_user_{i+1}@example.com"
            
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
        
        # 2. 测试前端API接口
        print(f"\n2️⃣ 测试前端API接口...")
        
        # 测试检查角色用户数量接口
        async with session.get(f"{base_url}/api/v1/role/check_users?role_id={test_role.id}", headers=admin_headers) as resp:
            if resp.status == 200:
                result = await resp.json()
                print(f"   ✅ 检查角色用户数量接口正常: {result['data']}")
            else:
                print(f"   ❌ 检查角色用户数量接口失败: {await resp.text()}")
        
        # 测试删除角色接口（不强制删除）
        async with session.delete(f"{base_url}/api/v1/role/delete?role_id={test_role.id}", headers=admin_headers) as resp:
            result = await resp.json()
            if resp.status == 400 and result.get('data', {}).get('need_confirmation'):
                print(f"   ✅ 删除角色接口正确返回确认提示")
            else:
                print(f"   ❌ 删除角色接口响应异常: {result}")
        
        print(f"\n📋 前端测试总结:")
        print(f"   ✅ 后端API接口已准备就绪")
        print(f"   ✅ 测试角色 '{test_role.name}' (ID: {test_role.id}) 已创建")
        print(f"   ✅ 关联了 {len(test_users)} 个测试用户")
        print(f"   ✅ 可以在前端界面测试删除功能")
        
        print(f"\n🎯 前端测试步骤:")
        print(f"   1. 打开浏览器访问: http://localhost:3000/system/role")
        print(f"   2. 找到角色 '前端测试角色'")
        print(f"   3. 点击删除按钮")
        print(f"   4. 应该弹出确认对话框，显示关联了 {len(test_users)} 个用户")
        print(f"   5. 点击确定删除，应该弹出二次确认")
        print(f"   6. 再次确认后，角色和用户都应该被删除")
        
        # 保持角色和用户，供前端测试使用
        print(f"\n⚠️ 测试数据已保留，供前端测试使用")


if __name__ == "__main__":
    asyncio.run(test_frontend_role_deletion())
