#!/usr/bin/env python3
"""
清理测试用户
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.admin import User
from app.core.init_app import init_db


async def cleanup_test_users():
    """清理测试用户"""
    print("🧹 清理测试用户...")
    await init_db()
    
    test_usernames = ["test_level1_user", "test_level3_user"]
    test_emails = ["test_level1@example.com", "test_level3@example.com"]
    
    for username in test_usernames:
        user = await User.filter(username=username).first()
        if user:
            await user.delete()
            print(f"   🗑️ 删除测试用户: {username}")
    
    for email in test_emails:
        user = await User.filter(email=email).first()
        if user:
            await user.delete()
            print(f"   🗑️ 删除测试用户: {email}")
    
    print("✅ 测试用户清理完成！")


if __name__ == "__main__":
    asyncio.run(cleanup_test_users())
