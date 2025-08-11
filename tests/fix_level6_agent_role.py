#!/usr/bin/env python3
"""
修复六级代理角色的is_agent_role字段和ag5用户密码
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.admin import User, Role
from app.core.init_app import init_db
from app.utils.password import get_password_hash


async def fix_level6_agent_role():
    """修复六级代理角色和ag5用户"""
    print("🔄 修复六级代理角色和ag5用户...")
    await init_db()
    
    # 1. 修复六级代理角色的is_agent_role字段
    level6_role = await Role.filter(user_level=6).first()
    if level6_role:
        print(f"   找到六级代理角色: {level6_role.name}")
        print(f"   当前is_agent_role: {level6_role.is_agent_role}")
        
        if not level6_role.is_agent_role:
            level6_role.is_agent_role = True
            await level6_role.save()
            print(f"   ✅ 已修复六级代理角色的is_agent_role字段为True")
        else:
            print(f"   ✅ 六级代理角色的is_agent_role字段已正确")
    else:
        print(f"   ❌ 未找到六级代理角色")
    
    # 2. 修复ag5用户密码
    ag5_user = await User.filter(username="ag5").first()
    if ag5_user:
        print(f"   找到ag5用户，重置密码...")
        ag5_user.password = get_password_hash("123456")
        await ag5_user.save()
        print(f"   ✅ ag5用户密码已重置为: 123456")
        
        # 确保用户有五级代理角色
        level5_role = await Role.filter(user_level=5).first()
        if level5_role:
            await ag5_user.roles.clear()
            await ag5_user.roles.add(level5_role)
            print(f"   ✅ ag5用户已分配五级代理角色")
        else:
            print(f"   ❌ 未找到五级代理角色")
    else:
        print(f"   ❌ 未找到ag5用户")
    
    # 3. 验证修复结果
    print(f"\n📊 验证修复结果:")
    all_roles = await Role.all().order_by('user_level')
    for role in all_roles:
        if role.user_level in [5, 6]:
            print(f"   - {role.name} (层级 {role.user_level}, is_agent_role: {role.is_agent_role})")
    
    print("\n🎉 修复完成！")


if __name__ == "__main__":
    asyncio.run(fix_level6_agent_role())
