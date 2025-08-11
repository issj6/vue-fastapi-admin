#!/usr/bin/env python3
"""
测试积分划转API接口
"""

import asyncio
import sys
import os
import httpx

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.init_app import init_db
from app.models import User


async def test_points_transfer_api():
    """测试积分划转API接口"""
    print("🧪 开始测试积分划转API接口...")
    
    # 初始化数据库
    await init_db()
    
    # 获取测试用户
    admin_user = await User.filter(username="admin").first()
    ag1_user = await User.filter(username="ag1").first()
    
    if not admin_user or not ag1_user:
        print("❌ 未找到admin或ag1用户")
        return False
    
    print(f"✅ 测试用户:")
    print(f"   - admin (ID: {admin_user.id})")
    print(f"   - ag1 (ID: {ag1_user.id})")
    
    # 模拟登录获取token（这里简化处理，实际应该通过登录接口获取）
    base_url = "http://localhost:9999"
    
    async with httpx.AsyncClient() as client:
        # 测试登录获取token
        print(f"\n📋 测试1: 管理员登录")
        try:
            login_response = await client.post(
                f"{base_url}/api/v1/base/admin_access_token",
                json={
                    "username": "admin",
                    "password": "123456"
                }
            )
            
            if login_response.status_code == 200:
                login_data = login_response.json()
                if login_data.get("code") == 200:
                    admin_token = login_data["data"]["access_token"]
                    print(f"✅ 管理员登录成功")
                else:
                    print(f"❌ 登录失败: {login_data.get('msg')}")
                    return False
            else:
                print(f"❌ 登录请求失败: {login_response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 登录异常: {str(e)}")
            return False
        
        # 测试积分划转API
        print(f"\n📋 测试2: 积分划转API")
        try:
            headers = {
                "Authorization": f"Bearer {admin_token}",
                "token": admin_token
            }
            
            # 使用用户管理接口的积分划转功能
            transfer_response = await client.post(
                f"{base_url}/api/v1/user/add_points",
                json={
                    "user_id": ag1_user.id,
                    "points": 150,
                    "description": "API测试积分划转",
                    "remark": "API接口测试"
                },
                headers=headers
            )
            
            if transfer_response.status_code == 200:
                transfer_data = transfer_response.json()
                if transfer_data.get("code") == 200:
                    print(f"✅ 积分划转API成功")
                    print(f"   - 划转ID: {transfer_data['data']['transfer_id']}")
                    print(f"   - 划转方余额: {transfer_data['data']['from_user_balance']}")
                    print(f"   - 接收方余额: {transfer_data['data']['to_user_balance']}")
                    print(f"   - 消息: {transfer_data['msg']}")
                else:
                    print(f"❌ 积分划转失败: {transfer_data.get('msg')}")
                    return False
            else:
                print(f"❌ 积分划转请求失败: {transfer_response.status_code}")
                print(f"   响应内容: {transfer_response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 积分划转API异常: {str(e)}")
            return False
        
        # 测试专用积分划转API
        print(f"\n📋 测试3: 专用积分划转API")
        try:
            transfer_response = await client.post(
                f"{base_url}/api/v1/points/transfer",
                params={
                    "to_user_id": ag1_user.id,
                    "points": 100,
                    "description": "专用API测试积分划转",
                    "remark": "专用API接口测试"
                },
                headers=headers
            )
            
            if transfer_response.status_code == 200:
                transfer_data = transfer_response.json()
                if transfer_data.get("code") == 200:
                    print(f"✅ 专用积分划转API成功")
                    print(f"   - 划转ID: {transfer_data['data']['transfer_id']}")
                    print(f"   - 消息: {transfer_data['msg']}")
                else:
                    print(f"❌ 专用积分划转失败: {transfer_data.get('msg')}")
                    return False
            else:
                print(f"❌ 专用积分划转请求失败: {transfer_response.status_code}")
                print(f"   响应内容: {transfer_response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 专用积分划转API异常: {str(e)}")
            return False
        
        # 测试权限检查
        print(f"\n📋 测试4: 权限检查")
        try:
            # 尝试ag1用户登录
            ag1_login_response = await client.post(
                f"{base_url}/api/v1/base/admin_access_token",
                json={
                    "username": "ag1",
                    "password": "123456"
                }
            )
            
            if ag1_login_response.status_code == 200:
                ag1_login_data = ag1_login_response.json()
                if ag1_login_data.get("code") == 200:
                    ag1_token = ag1_login_data["data"]["access_token"]
                    print(f"✅ ag1用户登录成功")
                    
                    # ag1尝试给admin划转积分（应该失败）
                    ag1_headers = {
                        "Authorization": f"Bearer {ag1_token}",
                        "token": ag1_token
                    }
                    unauthorized_response = await client.post(
                        f"{base_url}/api/v1/user/add_points",
                        json={
                            "user_id": admin_user.id,
                            "points": 50,
                            "description": "无权限测试",
                            "remark": "权限测试"
                        },
                        headers=ag1_headers
                    )
                    
                    if unauthorized_response.status_code == 200:
                        unauthorized_data = unauthorized_response.json()
                        if unauthorized_data.get("code") == 403:
                            print(f"✅ 权限检查正确，ag1无法给admin划转积分")
                        else:
                            print(f"❌ 权限检查失败，ag1不应该能给admin划转积分")
                            return False
                    elif unauthorized_response.status_code == 403:
                        print(f"✅ 权限检查正确，ag1无法给admin划转积分（HTTP 403）")
                    else:
                        print(f"❌ 权限检查请求失败: {unauthorized_response.status_code}")
                        return False
                else:
                    print(f"❌ ag1登录失败: {ag1_login_data.get('msg')}")
                    return False
            else:
                print(f"❌ ag1登录请求失败: {ag1_login_response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 权限检查异常: {str(e)}")
            return False
    
    print(f"\n🎉 所有API测试通过！积分划转API接口正常工作")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_points_transfer_api())
    sys.exit(0 if success else 1)
