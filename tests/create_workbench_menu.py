#!/usr/bin/env python3
"""
创建工作台菜单
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.admin import Menu, Role
from app.core.init_app import init_db


async def create_workbench_menu():
    """创建工作台菜单"""
    print("🔧 初始化数据库连接...")
    await init_db()
    
    print("\n🏠 创建工作台菜单...")
    
    # 检查是否已存在工作台菜单
    existing_workbench = await Menu.filter(path="/workbench").first()
    if existing_workbench:
        print(f"✅ 工作台菜单已存在: {existing_workbench.name}")
        return existing_workbench
    
    # 创建工作台菜单
    workbench_menu = await Menu.create(
        name="工作台",
        path="/workbench",
        component="workbench/index",
        icon="icon-park-outline:workbench",
        order=1,
        parent_id=0,
        is_hidden=False,
        keepalive=True
    )
    
    print(f"✅ 工作台菜单创建成功: {workbench_menu.name} (ID: {workbench_menu.id})")
    
    # 为所有代理角色添加工作台菜单权限
    print("\n🔑 为代理角色添加工作台菜单权限...")
    
    agent_roles = await Role.filter(is_agent_role=True).all()
    for role in agent_roles:
        await role.menus.add(workbench_menu)
        print(f"   ✅ 已为角色 '{role.name}' 添加工作台菜单权限")
    
    print("\n✅ 工作台菜单创建完成")
    return workbench_menu


if __name__ == "__main__":
    asyncio.run(create_workbench_menu())
