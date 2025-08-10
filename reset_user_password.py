#!/usr/bin/env python3
"""
重置用户密码
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.admin import User
from app.utils.password import get_password_hash
from app.core.init_app import init_db


async def reset_password():
    """重置用户密码"""
    print("🔧 初始化数据库连接...")
    await init_db()
    
    print("\n🔑 重置用户密码...")
    
    # 重置test001用户密码为123456
    user = await User.filter(username="test001").first()
    if user:
        user.password = get_password_hash("123456")
        await user.save()
        print(f"✅ 用户 {user.username} 密码已重置为 123456")
    else:
        print("❌ 未找到用户 test001")
    
    print("\n✅ 密码重置完成")


if __name__ == "__main__":
    asyncio.run(reset_password())
