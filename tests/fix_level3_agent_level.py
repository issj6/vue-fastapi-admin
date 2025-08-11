#!/usr/bin/env python3
"""
修正三级代理的层级数字
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.admin import Role
from app.core.init_app import init_db


async def fix_level3_agent_level():
    """修正三级代理的层级数字"""
    print("🔄 修正三级代理的层级数字...")
    await init_db()
    
    # 查找三级代理角色
    level3_role = await Role.filter(name="三级代理").first()
    
    if level3_role:
        print(f"   找到三级代理角色，当前层级: {level3_role.user_level}")
        
        if level3_role.user_level != 3:
            level3_role.user_level = 3
            await level3_role.save()
            print(f"   ✅ 已修正三级代理层级为: 3")
        else:
            print(f"   ✅ 三级代理层级已正确: 3")
    else:
        print("   ❌ 未找到三级代理角色")
    
    # 验证所有角色层级
    print("\n📊 验证所有角色层级:")
    all_roles = await Role.all().order_by('user_level')
    
    for role in all_roles:
        print(f"   {role.name}: 层级 {role.user_level}")
    
    print("\n🎉 三级代理层级修正完成！")


if __name__ == "__main__":
    asyncio.run(fix_level3_agent_level())
