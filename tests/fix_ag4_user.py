#!/usr/bin/env python3
"""
修复ag4用户
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.admin import User, Role
from app.core.init_app import init_db
from app.utils.password import get_password_hash


async def fix_ag4_user():
    """修复ag4用户"""
    print("🔄 修复ag4用户...")
    await init_db()
    
    # 查找ag4用户
    ag4_user = await User.filter(username="ag4").first()
    
    if ag4_user:
        print(f"   找到ag4用户，重置密码...")
        ag4_user.password = get_password_hash("123456")
        await ag4_user.save()
        print(f"   ✅ ag4用户密码已重置为: 123456")
        
        # 确保用户有四级代理角色
        level4_role = await Role.filter(user_level=4).first()
        if level4_role:
            await ag4_user.roles.clear()
            await ag4_user.roles.add(level4_role)
            print(f"   ✅ ag4用户已分配四级代理角色")
        else:
            print(f"   ❌ 未找到四级代理角色")
    else:
        print("   ❌ 未找到ag4用户")
    
    print("\n🎉 ag4用户修复完成！")


if __name__ == "__main__":
    asyncio.run(fix_ag4_user())
