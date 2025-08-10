#!/usr/bin/env python3
"""
重置ag1用户密码
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.admin import User
from app.core.init_app import init_db
from app.utils.password import get_password_hash


async def reset_ag1_password():
    """重置ag1用户密码"""
    print("🔧 初始化数据库连接...")
    await init_db()
    
    print("\n🔑 重置ag1用户密码...")
    
    # 查找ag1用户
    ag1_user = await User.filter(username="ag1").first()
    if not ag1_user:
        print("❌ 未找到ag1用户")
        return
    
    print(f"✅ 找到用户: {ag1_user.username} (ID: {ag1_user.id})")
    
    # 重置密码为123456
    new_password = "123456"
    hashed_password = get_password_hash(new_password)
    
    await User.filter(id=ag1_user.id).update(password=hashed_password)
    
    print(f"✅ ag1用户密码已重置为: {new_password}")
    print("   现在可以使用新密码登录了")


if __name__ == "__main__":
    asyncio.run(reset_ag1_password())
