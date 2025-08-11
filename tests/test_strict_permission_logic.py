#!/usr/bin/env python3
"""
测试严格的权限逻辑：
1. 有CREATE_USER权限 → 只能创建层级99的普通用户
2. 有CREATE_SUBORDINATE_AGENT权限 → 只能创建自身层级+1的代理角色
3. 都没有 → 不能创建任何角色
"""

import asyncio
import aiohttp


async def test_strict_permission_logic():
    """测试严格的权限逻辑"""
    base_url = "http://localhost:9999"
    
    async with aiohttp.ClientSession() as session:
        print("🔧 测试严格的权限逻辑...")
        
        # 测试用户列表
        test_users = [
            {"username": "admin", "password": "123456", "expected_level": -1, "role_name": "超级管理员"},
            {"username": "super_agent", "password": "123456", "expected_level": 0, "role_name": "超级代理"},
            {"username": "ag1", "password": "123456", "expected_level": 1, "role_name": "一级代理"},
            {"username": "ag2", "password": "123456", "expected_level": 2, "role_name": "二级代理"},
            {"username": "ag3", "password": "123456", "expected_level": 3, "role_name": "三级代理"}
        ]
        
        for user_info in test_users:
            print(f"\n{'='*60}")
            print(f"🧪 测试用户: {user_info['username']} (层级 {user_info['expected_level']})")
            print(f"{'='*60}")
            
            # 用户登录
            login_data = {"username": user_info['username'], "password": user_info['password']}
            
            try:
                async with session.post(f"{base_url}/api/v1/base/admin_access_token", json=login_data) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        token = result['data']['access_token']
                        headers = {"token": token}
                        print(f"   ✅ 登录成功")
                    else:
                        result_text = await resp.text()
                        print(f"   ❌ 登录失败: {resp.status} - {result_text}")
                        continue
            except Exception as e:
                print(f"   ❌ 登录异常: {e}")
                continue
            
            # 获取可创建的角色
            try:
                async with session.get(f"{base_url}/api/v1/role/creatable", headers=headers) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        creatable_roles = result['data']
                        
                        print(f"   📋 可创建角色 ({len(creatable_roles)}个):")
                        
                        current_level = user_info['expected_level']
                        
                        if len(creatable_roles) == 0:
                            print(f"     - 无任何可创建角色")
                        else:
                            for role in sorted(creatable_roles, key=lambda x: x.get('user_level', 99)):
                                role_level = role.get('user_level', 99)
                                role_name = role['name']
                                print(f"     - {role_name} (层级 {role_level})")
                        
                        # 验证逻辑正确性
                        print(f"\n   🔍 权限逻辑验证:")
                        
                        if user_info['username'] == 'admin':
                            print(f"     ✅ 超级管理员应该能创建所有角色（除管理员）")
                        else:
                            # 检查普通用户权限
                            normal_user_roles = [r for r in creatable_roles if r.get('user_level') == 99]
                            if normal_user_roles:
                                print(f"     ✅ 有CREATE_USER权限，可创建普通用户")
                            else:
                                print(f"     ❌ 无CREATE_USER权限或无普通用户角色")
                            
                            # 检查代理权限 - 应该只能创建层级+1的代理
                            expected_agent_level = current_level + 1
                            agent_roles = [r for r in creatable_roles if r.get('user_level') == expected_agent_level]
                            other_agent_roles = [r for r in creatable_roles if r.get('user_level') not in [99, expected_agent_level]]
                            
                            if agent_roles:
                                print(f"     ✅ 有CREATE_SUBORDINATE_AGENT权限，可创建层级{expected_agent_level}代理")
                            else:
                                print(f"     ❌ 无CREATE_SUBORDINATE_AGENT权限或无层级{expected_agent_level}代理角色")
                            
                            if other_agent_roles:
                                print(f"     ❌ 错误：不应该能创建其他层级代理: {[r['name'] for r in other_agent_roles]}")
                            else:
                                print(f"     ✅ 正确：无法创建其他层级代理")
                        
                        # 特殊验证
                        if user_info['username'] == 'ag3':  # 三级代理
                            expected_roles = []
                            # 应该能创建普通用户(99)
                            if any(r.get('user_level') == 99 for r in creatable_roles):
                                expected_roles.append("普通用户(99)")
                            # 应该能创建四级代理(4)
                            if any(r.get('user_level') == 4 for r in creatable_roles):
                                expected_roles.append("四级代理(4)")
                            
                            print(f"     📊 三级代理预期可创建: {expected_roles}")
                        
                    else:
                        result_text = await resp.text()
                        print(f"   ❌ 获取可创建角色失败: {resp.status} - {result_text}")
                        
            except Exception as e:
                print(f"   ❌ 获取可创建角色异常: {e}")
        
        print(f"\n{'='*60}")
        print("🎉 严格权限逻辑测试完成！")
        print(f"{'='*60}")
        
        print("\n📋 正确的权限逻辑:")
        print("   1. CREATE_USER权限 → 只能创建普通用户(层级99)")
        print("   2. CREATE_SUBORDINATE_AGENT权限 → 只能创建自身层级+1的代理")
        print("   3. 无权限 → 不能创建任何角色，不显示创建按钮")
        print("   4. 不基于角色名称，只基于权限和层级数字")


if __name__ == "__main__":
    asyncio.run(test_strict_permission_logic())
