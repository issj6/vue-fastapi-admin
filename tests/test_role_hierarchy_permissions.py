#!/usr/bin/env python3
"""
全面测试角色层级权限控制系统
"""

import asyncio
import aiohttp
import json


async def test_role_hierarchy_permissions():
    """全面测试角色层级权限控制"""
    base_url = "http://localhost:9999"
    
    async with aiohttp.ClientSession() as session:
        print("🔧 测试角色层级权限控制系统...")
        
        # 测试用户列表（更新层级数字）
        test_users = [
            {"username": "admin", "password": "123456", "expected_level": -1, "role_name": "超级管理员"},
            {"username": "ag1", "password": "123456", "expected_level": 1, "role_name": "一级代理"},
            {"username": "ag2", "password": "123456", "expected_level": 2, "role_name": "二级代理"},
            {"username": "ag3", "password": "123456", "expected_level": 3, "role_name": "三级代理"}
        ]
        
        for user_info in test_users:
            print(f"\n{'='*60}")
            print(f"🧪 测试用户: {user_info['username']} ({user_info['role_name']})")
            print(f"{'='*60}")
            
            # 1. 用户登录
            print(f"\n1️⃣ {user_info['username']} 登录...")
            login_data = {"username": user_info['username'], "password": user_info['password']}
            
            try:
                async with session.post(f"{base_url}/api/v1/base/admin_access_token", json=login_data) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        token = result['data']['access_token']
                        headers = {"token": token}
                        print(f"   ✅ {user_info['username']} 登录成功")
                    else:
                        result_text = await resp.text()
                        print(f"   ❌ {user_info['username']} 登录失败: {resp.status} - {result_text}")
                        continue
            except Exception as e:
                print(f"   ❌ {user_info['username']} 登录异常: {e}")
                continue
            
            # 2. 获取可创建的角色
            print(f"\n2️⃣ 获取 {user_info['username']} 可创建的角色...")
            
            try:
                async with session.get(f"{base_url}/api/v1/role/creatable", headers=headers) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        creatable_roles = result['data']
                        
                        print(f"   ✅ 成功获取可创建角色列表 ({len(creatable_roles)}个):")
                        for role in creatable_roles:
                            level_desc = {
                                -1: "超级管理员",
                                0: "超级代理",
                                1: "一级代理",
                                2: "二级代理",
                                3: "三级代理",
                                99: "普通用户"
                            }.get(role.get('user_level'), f"未知层级({role.get('user_level')})")
                            
                            print(f"     - {role['name']} (层级 {role.get('user_level')}) - {level_desc}")
                        
                        # 分析权限控制结果
                        print(f"\n   🔍 权限控制分析:")
                        
                        # 检查是否包含不应该出现的角色
                        current_level = user_info['expected_level']
                        
                        for role in creatable_roles:
                            role_level = role.get('user_level', 99)
                            role_name = role['name']
                            
                            if role_name == "普通用户":
                                print(f"     ✅ {role_name}: 正确（所有用户都可创建普通用户）")
                            elif role_level > current_level:
                                print(f"     ✅ {role_name}: 正确（层级 {role_level} > {current_level}）")
                            elif role_level <= current_level and role_name != "管理员":
                                print(f"     ❌ {role_name}: 错误（层级 {role_level} <= {current_level}，不应该出现）")
                            elif role_name == "管理员":
                                if user_info['username'] == 'admin':
                                    print(f"     ⚠️ {role_name}: 管理员角色（超级管理员可见但不能创建）")
                                else:
                                    print(f"     ❌ {role_name}: 错误（非超级管理员不应该看到管理员角色）")
                        
                        # 特别检查三级代理
                        if user_info['username'] == 'ag3':
                            agent_roles = [r for r in creatable_roles if r.get('user_level', 99) in [0, 1, 2, 3]]
                            if agent_roles:
                                print(f"     ❌ 三级代理不应该能创建任何代理角色，但发现: {[r['name'] for r in agent_roles]}")
                            else:
                                print(f"     ✅ 三级代理正确无法创建任何代理角色")
                        
                    else:
                        result_text = await resp.text()
                        print(f"   ❌ 获取可创建角色失败: {resp.status} - {result_text}")
                        
            except Exception as e:
                print(f"   ❌ 获取可创建角色异常: {e}")
            
            # 3. 测试创建用户（仅测试关键场景）
            if user_info['username'] in ['ag2', 'ag3']:  # 只测试二级和三级代理
                print(f"\n3️⃣ 测试 {user_info['username']} 创建用户权限...")
                
                # 获取所有角色信息
                try:
                    async with session.get(f"{base_url}/api/v1/role/list?page=1&page_size=50", headers=headers) as resp:
                        if resp.status == 200:
                            result = await resp.json()
                            all_roles = {role['name']: role['id'] for role in result['data']}
                            
                            # 测试场景
                            test_scenarios = []
                            
                            if user_info['username'] == 'ag2':  # 二级代理
                                test_scenarios = [
                                    {"role_name": "一级代理", "should_succeed": False, "reason": "层级权限不足"},
                                    {"role_name": "三级代理", "should_succeed": True, "reason": "层级权限允许"},
                                ]
                            elif user_info['username'] == 'ag3':  # 三级代理
                                test_scenarios = [
                                    {"role_name": "一级代理", "should_succeed": False, "reason": "层级权限不足"},
                                    {"role_name": "二级代理", "should_succeed": False, "reason": "层级权限不足"},
                                    {"role_name": "普通用户", "should_succeed": True, "reason": "有CREATE_USER权限"},
                                ]
                            
                            for scenario in test_scenarios:
                                role_name = scenario['role_name']
                                should_succeed = scenario['should_succeed']
                                reason = scenario['reason']
                                
                                if role_name not in all_roles:
                                    print(f"     ⚠️ 跳过测试 {role_name}：角色不存在")
                                    continue
                                
                                print(f"     🧪 测试创建 {role_name} 用户...")
                                
                                import time
                                timestamp = int(time.time()) % 10000
                                create_user_data = {
                                    "username": f"test_{role_name}_{timestamp}",
                                    "email": f"test_{role_name}_{timestamp}@example.com",
                                    "password": "123456",
                                    "role_ids": [all_roles[role_name]],
                                    "school": "测试学校",
                                    "major": "测试专业"
                                }
                                
                                try:
                                    async with session.post(f"{base_url}/api/v1/user/create", json=create_user_data, headers=headers) as resp:
                                        result_text = await resp.text()
                                        
                                        if should_succeed:
                                            if resp.status == 200:
                                                print(f"       ✅ 成功创建 {role_name} 用户 ({reason})")
                                                # 清理测试用户
                                                try:
                                                    result = json.loads(result_text)
                                                    # 这里可以添加删除用户的逻辑
                                                except:
                                                    pass
                                            else:
                                                print(f"       ❌ 创建 {role_name} 用户失败，但应该成功 ({reason})")
                                                print(f"          响应: {result_text}")
                                        else:
                                            if resp.status == 403:
                                                print(f"       ✅ 正确拒绝创建 {role_name} 用户 ({reason})")
                                            else:
                                                print(f"       ❌ 创建 {role_name} 用户应该被拒绝，但状态码是 {resp.status}")
                                                print(f"          响应: {result_text}")
                                                
                                except Exception as e:
                                    print(f"       ❌ 测试创建 {role_name} 用户异常: {e}")
                        
                except Exception as e:
                    print(f"   ❌ 获取角色列表异常: {e}")
        
        print(f"\n{'='*60}")
        print("🎉 角色层级权限控制测试完成！")
        print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(test_role_hierarchy_permissions())
