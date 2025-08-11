#!/usr/bin/env python3
"""
测试用户层级显示修复
"""

import asyncio
import aiohttp
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.admin import User, Role
from app.core.init_app import init_db


async def test_user_level_display():
    """测试用户层级显示修复"""
    base_url = "http://localhost:9999"
    
    print("🔧 测试用户层级显示修复...")
    
    # 1. 验证数据库中的角色和用户
    print("\n1️⃣ 验证数据库中的角色层级...")
    await init_db()
    
    # 查看校级代理角色
    school_agent_role = await Role.filter(name="校级代理").first()
    if school_agent_role:
        print(f"   ✅ 校级代理角色: {school_agent_role.name} (层级: {school_agent_role.user_level})")
    else:
        print("   ❌ 校级代理角色不存在")
        return
    
    # 查看拥有校级代理角色的用户
    users_with_school_agent = await User.filter(roles__name="校级代理").prefetch_related('roles')
    print(f"   📋 拥有校级代理角色的用户数量: {len(users_with_school_agent)}")
    
    for user in users_with_school_agent[:3]:  # 只显示前3个
        user_roles = await user.roles.all()
        min_level = 99
        for role in user_roles:
            if role.user_level < min_level:
                min_level = role.user_level
        print(f"      - {user.username}: 计算层级 = {min_level}")
    
    # 2. 测试API返回的数据
    print(f"\n2️⃣ 测试API返回的用户层级...")
    
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
        
        # 测试代理用户列表API
        async with session.get(f"{base_url}/api/v1/user/agents", headers=admin_headers) as resp:
            if resp.status == 200:
                result = await resp.json()
                agents = result.get('data', [])
                print(f"   ✅ 代理用户列表API正常，共 {len(agents)} 个代理用户")
                
                # 检查校级代理用户的层级显示
                school_agents = [agent for agent in agents if any(role['name'] == '校级代理' for role in agent.get('roles', []))]
                print(f"   📋 校级代理用户数量: {len(school_agents)}")
                
                for agent in school_agents[:3]:  # 只显示前3个
                    user_level = agent.get('user_level', 'N/A')
                    roles = [role['name'] for role in agent.get('roles', [])]
                    print(f"      - {agent['username']}: API返回层级 = {user_level}, 角色 = {roles}")
                    
                    # 验证层级是否正确
                    if user_level == 1:  # 校级代理应该是层级1
                        print(f"        ✅ 层级显示正确")
                    else:
                        print(f"        ❌ 层级显示错误，应该是1，实际是{user_level}")
                        
            else:
                print(f"   ❌ 代理用户列表API失败: {resp.status}")
        
        # 测试普通用户列表API
        async with session.get(f"{base_url}/api/v1/user/list", headers=admin_headers) as resp:
            if resp.status == 200:
                result = await resp.json()
                users = result.get('data', [])
                print(f"   ✅ 普通用户列表API正常，共 {len(users)} 个普通用户")
                
                # 检查普通用户的层级显示
                for user in users[:3]:  # 只显示前3个
                    user_level = user.get('user_level', 'N/A')
                    roles = [role['name'] for role in user.get('roles', [])]
                    print(f"      - {user['username']}: API返回层级 = {user_level}, 角色 = {roles}")
                    
                    # 验证层级是否正确
                    if user_level == 99:  # 普通用户应该是层级99
                        print(f"        ✅ 层级显示正确")
                    else:
                        print(f"        ❌ 层级显示错误，应该是99，实际是{user_level}")
                        
            else:
                print(f"   ❌ 普通用户列表API失败: {resp.status}")
    
    print(f"\n🎯 前端验证指南:")
    print(f"   1. 刷新代理管理页面: http://localhost:3000/system/agent")
    print(f"   2. 查看校级代理用户的'角色层级'列")
    print(f"   3. 应该显示'层级1'而不是'层级99'")
    print(f"   4. 验证其他代理用户的层级显示是否正确")
    
    print(f"\n✅ 用户层级显示测试完成！")


if __name__ == "__main__":
    asyncio.run(test_user_level_display())
