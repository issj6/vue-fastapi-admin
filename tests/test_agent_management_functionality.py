#!/usr/bin/env python3
"""
测试代理管理功能
"""

import asyncio
import aiohttp
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.admin import User, Role, Menu
from app.core.init_app import init_db


async def test_agent_management_functionality():
    """测试代理管理功能"""
    base_url = "http://localhost:9999"
    
    print("🔧 测试代理管理功能...")
    
    # 1. 验证菜单创建
    print("\n1️⃣ 验证菜单结构...")
    await init_db()
    
    # 检查代理管理菜单
    agent_menu = await Menu.filter(name="代理管理").first()
    if agent_menu:
        print(f"   ✅ 代理管理菜单存在: {agent_menu.name} (ID: {agent_menu.id})")
        print(f"   📋 路径: {agent_menu.path}")
        print(f"   📋 图标: {agent_menu.icon}")
        print(f"   📋 父菜单ID: {agent_menu.parent_id}")
    else:
        print("   ❌ 代理管理菜单不存在")
        return
    
    # 2. 创建测试数据
    print(f"\n2️⃣ 创建测试数据...")
    
    # 创建测试代理角色（如果不存在）
    test_agent_role = await Role.filter(name="测试代理", user_level=5).first()
    if not test_agent_role:
        test_agent_role = await Role.create(
            name="测试代理",
            desc="用于测试代理管理功能",
            user_level=5,
            is_agent_role=True,
            agent_permissions=["VIEW_SUBORDINATE_USERS", "CREATE_USER"]
        )
        print(f"   ✅ 创建测试代理角色: {test_agent_role.name} (层级: {test_agent_role.user_level})")
    else:
        print(f"   ✅ 测试代理角色已存在: {test_agent_role.name} (层级: {test_agent_role.user_level})")
    
    # 创建测试普通用户角色（如果不存在）
    test_user_role = await Role.filter(name="测试普通用户", user_level=99).first()
    if not test_user_role:
        test_user_role = await Role.create(
            name="测试普通用户",
            desc="用于测试用户管理功能",
            user_level=99,
            is_agent_role=False,
            agent_permissions=[]
        )
        print(f"   ✅ 创建测试普通用户角色: {test_user_role.name} (层级: {test_user_role.user_level})")
    else:
        print(f"   ✅ 测试普通用户角色已存在: {test_user_role.name} (层级: {test_user_role.user_level})")
    
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
        
        # 3. 测试API接口
        print(f"\n3️⃣ 测试API接口...")
        
        # 测试代理用户列表接口
        async with session.get(f"{base_url}/api/v1/user/agents", headers=admin_headers) as resp:
            if resp.status == 200:
                result = await resp.json()
                agent_count = result.get('total', 0)
                print(f"   ✅ 代理用户列表接口正常，共 {agent_count} 个代理用户")
                
                # 显示前几个代理用户
                agents = result.get('data', [])
                for i, agent in enumerate(agents[:3]):
                    print(f"      - {agent['username']} (层级: {agent.get('user_level', 99)})")
            else:
                print(f"   ❌ 代理用户列表接口失败: {resp.status}")
        
        # 测试普通用户列表接口
        async with session.get(f"{base_url}/api/v1/user/list", headers=admin_headers) as resp:
            if resp.status == 200:
                result = await resp.json()
                user_count = result.get('total', 0)
                print(f"   ✅ 普通用户列表接口正常，共 {user_count} 个普通用户")
                
                # 显示前几个普通用户
                users = result.get('data', [])
                for i, user in enumerate(users[:3]):
                    print(f"      - {user['username']} (层级: {user.get('user_level', 99)})")
            else:
                print(f"   ❌ 普通用户列表接口失败: {resp.status}")
        
        # 4. 验证数据分离
        print(f"\n4️⃣ 验证数据分离效果...")
        
        # 统计数据库中的用户分布
        all_users = await User.all().prefetch_related('roles')
        agent_users = []
        normal_users = []

        for user in all_users:
            user_roles = await user.roles.all()
            min_level = 99  # 默认层级
            for role in user_roles:
                if role.user_level < min_level:
                    min_level = role.user_level

            if min_level < 99:
                agent_users.append((user, min_level))
            else:
                normal_users.append((user, min_level))

        print(f"   📊 数据库用户统计:")
        print(f"      - 总用户数: {len(all_users)}")
        print(f"      - 代理用户数: {len(agent_users)} (层级 < 99)")
        print(f"      - 普通用户数: {len(normal_users)} (层级 = 99)")

        # 显示代理用户详情
        if agent_users:
            print(f"   📋 代理用户列表:")
            for user, level in agent_users[:5]:  # 只显示前5个
                print(f"      - {user.username} (层级: {level})")

        # 显示普通用户详情
        if normal_users:
            print(f"   📋 普通用户列表:")
            for user, level in normal_users[:5]:  # 只显示前5个
                print(f"      - {user.username} (层级: {level})")
        
        print(f"\n🎯 前端测试指南:")
        print(f"   1. 打开浏览器访问: http://localhost:3000")
        print(f"   2. 登录管理员账户")
        print(f"   3. 在系统管理菜单下应该看到:")
        print(f"      - 用户管理 (显示普通用户，层级99)")
        print(f"      - 代理管理 (显示代理用户，层级<99)")
        print(f"   4. 验证两个页面显示的用户数据不同")
        print(f"   5. 验证权限控制是否正确")
        
        print(f"\n✅ 代理管理功能测试完成！")


if __name__ == "__main__":
    asyncio.run(test_agent_management_functionality())
