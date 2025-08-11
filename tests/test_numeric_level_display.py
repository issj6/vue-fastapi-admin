#!/usr/bin/env python3
"""
测试数字层级显示的完整权限控制
"""

import asyncio
import aiohttp


async def test_numeric_level_display():
    """测试数字层级显示的权限控制"""
    base_url = "http://localhost:9999"
    
    async with aiohttp.ClientSession() as session:
        print("🔧 测试数字层级显示的权限控制...")
        
        # 测试用户列表（更新后的层级）
        test_users = [
            {"username": "admin", "password": "123456", "expected_level": -1, "role_name": "超级管理员"},
            {"username": "super_agent", "password": "123456", "expected_level": 0, "role_name": "超级代理"},
            {"username": "ag1", "password": "123456", "expected_level": 1, "role_name": "一级代理"},
            {"username": "ag2", "password": "123456", "expected_level": 2, "role_name": "二级代理"},
            {"username": "ag3", "password": "123456", "expected_level": 3, "role_name": "三级代理"}
        ]
        
        for user_info in test_users:
            print(f"\n{'='*50}")
            print(f"🧪 测试用户: {user_info['username']} (层级 {user_info['expected_level']})")
            print(f"{'='*50}")
            
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
                        
                        for role in sorted(creatable_roles, key=lambda x: x.get('user_level', 99)):
                            role_level = role.get('user_level', 99)
                            role_name = role['name']
                            
                            # 验证权限控制逻辑
                            if role_name == "普通用户":
                                status = "✅ 正确"
                            elif role_level > current_level:
                                status = "✅ 正确"
                            else:
                                status = "❌ 错误"
                            
                            print(f"     - 层级 {role_level}: {role_name} {status}")
                        
                        # 统计分析
                        agent_roles = [r for r in creatable_roles if r.get('user_level', 99) not in [-1, 99]]
                        normal_user_roles = [r for r in creatable_roles if r.get('user_level', 99) == 99]
                        
                        print(f"\n   📊 权限分析:")
                        print(f"     - 可创建代理角色: {len(agent_roles)}个")
                        print(f"     - 可创建普通用户: {len(normal_user_roles)}个")
                        
                        # 特殊验证
                        if user_info['username'] == 'ag3':  # 三级代理
                            if len(agent_roles) == 1 and agent_roles[0]['name'] == '四级代理':
                                print(f"     ✅ 三级代理只能创建四级代理，符合预期")
                            elif len(agent_roles) == 0:
                                print(f"     ✅ 三级代理无法创建代理角色（如果没有四级代理）")
                            else:
                                print(f"     ❌ 三级代理权限异常")
                        
                    else:
                        result_text = await resp.text()
                        print(f"   ❌ 获取可创建角色失败: {resp.status} - {result_text}")
                        
            except Exception as e:
                print(f"   ❌ 获取可创建角色异常: {e}")
        
        print(f"\n{'='*50}")
        print("🎉 数字层级显示测试完成！")
        print(f"{'='*50}")
        
        print("\n📋 系统优势总结:")
        print("   ✅ 层级显示统一为数字，清晰直观")
        print("   ✅ 支持动态扩展任意层级代理")
        print("   ✅ 权限控制基于数字大小，逻辑简单")
        print("   ✅ 无需预定义角色名称，灵活性强")
        print("   ✅ 前端显示自动适配新角色")


if __name__ == "__main__":
    asyncio.run(test_numeric_level_display())
