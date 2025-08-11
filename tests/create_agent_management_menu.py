#!/usr/bin/env python3
"""
创建代理管理菜单
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.admin import Menu
from app.schemas.menus import MenuType
from app.core.init_app import init_db


async def create_agent_management_menu():
    """创建代理管理菜单"""
    print("🔧 创建代理管理菜单...")
    await init_db()
    
    # 查找系统管理父菜单
    system_menu = await Menu.filter(name="系统管理", parent_id=0).first()
    if not system_menu:
        print("❌ 未找到系统管理父菜单")
        return
    
    print(f"✅ 找到系统管理菜单: {system_menu.name} (ID: {system_menu.id})")
    
    # 检查代理管理菜单是否已存在
    existing_menu = await Menu.filter(name="代理管理", parent_id=system_menu.id).first()
    if existing_menu:
        print(f"✅ 代理管理菜单已存在: {existing_menu.name} (ID: {existing_menu.id})")
        return existing_menu
    
    # 获取当前最大的order值
    max_order_menu = await Menu.filter(parent_id=system_menu.id).order_by("-order").first()
    next_order = (max_order_menu.order + 1) if max_order_menu else 1
    
    # 创建代理管理菜单
    agent_menu = await Menu.create(
        menu_type=MenuType.MENU,
        name="代理管理",
        path="agent",
        order=next_order,
        parent_id=system_menu.id,
        icon="carbon:user-multiple",
        is_hidden=False,
        component="/system/agent",
        keepalive=False,
    )
    
    print(f"✅ 代理管理菜单创建成功:")
    print(f"   - 菜单名称: {agent_menu.name}")
    print(f"   - 菜单ID: {agent_menu.id}")
    print(f"   - 路径: {agent_menu.path}")
    print(f"   - 完整路径: /system/agent")
    print(f"   - 图标: {agent_menu.icon}")
    print(f"   - 排序: {agent_menu.order}")
    print(f"   - 父菜单ID: {agent_menu.parent_id}")
    
    # 验证菜单结构
    print(f"\n📋 验证菜单结构:")
    system_children = await Menu.filter(parent_id=system_menu.id).order_by("order")
    for child in system_children:
        print(f"   - {child.name} (order: {child.order}, path: {child.path})")
    
    return agent_menu


if __name__ == "__main__":
    asyncio.run(create_agent_management_menu())
