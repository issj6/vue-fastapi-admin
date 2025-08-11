#!/usr/bin/env python3
"""
创建一个没有关联用户的测试角色
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.admin import Role
from app.core.init_app import init_db


async def create_empty_test_role():
    """创建一个没有关联用户的测试角色"""
    print("🔧 创建空测试角色...")
    await init_db()
    
    # 创建测试角色
    empty_role = await Role.filter(name="空测试角色").first()
    if not empty_role:
        empty_role = await Role.create(
            name="空测试角色",
            desc="没有关联用户的测试角色",
            user_level=20,
            is_agent_role=True,
            agent_permissions=["CREATE_USER"]
        )
        print(f"   ✅ 创建空测试角色: {empty_role.name} (ID: {empty_role.id})")
    else:
        print(f"   ✅ 空测试角色已存在: {empty_role.name} (ID: {empty_role.id})")
    
    print(f"\n📋 测试说明:")
    print(f"   - 角色名称: {empty_role.name}")
    print(f"   - 角色ID: {empty_role.id}")
    print(f"   - 关联用户数: 0")
    print(f"   - 删除时应该直接删除，不需要二次确认")


if __name__ == "__main__":
    asyncio.run(create_empty_test_role())
