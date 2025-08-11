#!/usr/bin/env python3
"""
检查数据库中的实际角色名称
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.admin import Role
from app.core.init_app import init_db


async def check_role_names():
    """检查数据库中的实际角色名称"""
    print("🔧 初始化数据库连接...")
    await init_db()
    
    print("\n🔍 检查数据库中的实际角色名称...")
    all_roles = await Role.all()
    
    print(f"数据库中共有 {len(all_roles)} 个角色:")
    for role in all_roles:
        print(f"   ID: {role.id}, 名称: '{role.name}', 是否代理角色: {role.is_agent_role}")


if __name__ == "__main__":
    asyncio.run(check_role_names())
