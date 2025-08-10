#!/usr/bin/env python3
"""
检查菜单数据
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.admin import Menu, User, Role
from app.core.init_app import init_db


async def check_menu_data():
    """检查菜单数据"""
    print("🔧 初始化数据库连接...")
    await init_db()
    
    print("\n📋 检查菜单数据...")
    
    # 查看所有菜单
    all_menus = await Menu.all()
    print(f"📝 数据库中的所有菜单 (共{len(all_menus)}个):")
    for menu in all_menus:
        print(f"   - ID:{menu.id} | 名称:{menu.name} | 路径:{menu.path} | 组件:{menu.component} | 父级ID:{menu.parent_id}")
    
    # 查看test001用户的角色和菜单权限
    print(f"\n👤 test001用户的权限分析:")
    user = await User.filter(username="test001").first()
    if user:
        roles = await user.roles.all()
        print(f"   角色: {[role.name for role in roles]}")
        
        for role in roles:
            print(f"\n   角色 '{role.name}' 的详细信息:")
            print(f"     - 是否代理角色: {role.is_agent_role}")
            print(f"     - 代理权限: {role.agent_permissions}")
            
            # 获取角色的菜单权限
            menus = await role.menus.all()
            print(f"     - 菜单权限 (共{len(menus)}个):")
            for menu in menus:
                print(f"       * {menu.name} (路径: {menu.path})")
    
    # 检查工作台菜单是否存在
    print(f"\n🏠 工作台菜单检查:")
    workbench_menu = await Menu.filter(path="/workbench").first()
    if workbench_menu:
        print(f"   ✅ 找到工作台菜单: {workbench_menu.name}")
    else:
        print(f"   ❌ 未找到工作台菜单 (路径: /workbench)")
        
        # 查找可能的工作台相关菜单
        workbench_like = await Menu.filter(name__icontains="工作").all()
        if workbench_like:
            print(f"   🔍 找到相关菜单:")
            for menu in workbench_like:
                print(f"     - {menu.name} (路径: {menu.path})")
    
    print("\n✅ 菜单数据检查完成")


if __name__ == "__main__":
    asyncio.run(check_menu_data())
