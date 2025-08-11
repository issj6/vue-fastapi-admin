#!/usr/bin/env python3
"""
测试重置密码API功能
"""

import asyncio
import requests
import json

async def test_reset_password_api():
    """测试重置密码API"""
    print("🧪 测试重置密码API功能...")
    
    # 1. 先登录获取ag1的token
    login_url = "http://localhost:9999/api/v1/base/admin_access_token"
    login_data = {
        "username": "ag1",
        "password": "123456"
    }
    
    print("🔐 登录ag1用户...")
    login_response = requests.post(login_url, json=login_data)
    
    if login_response.status_code != 200:
        print(f"❌ 登录失败: {login_response.status_code} - {login_response.text}")
        return
    
    token = login_response.json()["data"]["access_token"]
    print(f"✅ 登录成功，获取token: {token[:20]}...")
    
    # 2. 测试重置密码API
    reset_url = "http://localhost:9999/api/v1/user/reset_password"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "token": token
    }
    
    # 测试重置ag1ag2的密码（不再需要提供new_password，由后端生成）
    reset_data = {
        "user_id": 24  # ag1ag2的用户ID
    }
    
    print("🔄 测试重置ag1ag2的密码...")
    reset_response = requests.post(reset_url, json=reset_data, headers=headers)
    
    print(f"📊 重置密码API响应:")
    print(f"   状态码: {reset_response.status_code}")
    print(f"   响应内容: {reset_response.text}")
    
    if reset_response.status_code == 200:
        response_data = reset_response.json()
        new_password = response_data.get("data", {}).get("new_password", "")

        print("✅ 重置密码成功！权限修复生效！")
        print(f"🔑 生成的新密码: {new_password}")

        # 验证密码格式
        if len(new_password) == 8:
            print("✅ 密码长度正确（8位）")
        else:
            print(f"❌ 密码长度错误：{len(new_password)}位")

        # 验证密码包含字母和数字
        has_letter = any(c.isalpha() for c in new_password)
        has_digit = any(c.isdigit() for c in new_password)

        if has_letter and has_digit:
            print("✅ 密码包含字母和数字")
        else:
            print(f"❌ 密码格式错误：包含字母={has_letter}, 包含数字={has_digit}")

    elif reset_response.status_code == 403:
        print("❌ 重置密码失败：权限不足")
    else:
        print(f"❌ 重置密码失败：{reset_response.status_code}")
    
    print("\n✅ 重置密码API测试完成")

if __name__ == "__main__":
    asyncio.run(test_reset_password_api())
