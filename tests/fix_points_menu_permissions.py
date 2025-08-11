#!/usr/bin/env python3
"""
修复积分管理菜单权限
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.admin import Menu, User, Role
from app.core.init_app import init_db


async def fix_points_menu_permissions():
    """修复积分管理菜单权限"""
    print("🔧 初始化数据库连接...")
    await init_db()
    
    print("\n🔧 修复积分管理菜单权限...")
    
    try:
        # 1. 删除旧的积分管理菜单 (ID:10, 路径:/credits)
        old_credits_menu = await Menu.filter(path="/credits").first()
        if old_credits_menu:
            print(f"🗑️  删除旧的积分管理菜单: {old_credits_menu.name} (路径: {old_credits_menu.path})")
            await old_credits_menu.delete()
        
        # 2. 获取积分管理菜单 (路径:/points)
        points_menu = await Menu.filter(path="/points").first()
        if not points_menu:
            print("❌ 未找到积分管理菜单 (路径: /points)")
            return
        
        print(f"✅ 找到积分管理菜单: {points_menu.name} (ID: {points_menu.id})")
        
        # 3. 获取积分信息和使用记录子菜单
        points_info_menu = await Menu.filter(path="/points/info").first()
        points_usage_menu = await Menu.filter(path="/points/usage").first()
        
        if not points_info_menu or not points_usage_menu:
            print("❌ 未找到积分子菜单")
            return
        
        print(f"✅ 找到积分信息菜单: {points_info_menu.name} (ID: {points_info_menu.id})")
        print(f"✅ 找到使用记录菜单: {points_usage_menu.name} (ID: {points_usage_menu.id})")
        
        # 4. 获取所有角色
        all_roles = await Role.all()
        
        for role in all_roles:
            print(f"\n🔧 为角色 '{role.name}' 添加积分管理菜单权限...")
            
            # 添加积分管理相关菜单到角色权限
            await role.menus.add(points_menu, points_info_menu, points_usage_menu)
            print(f"   ✅ 已添加积分管理菜单权限")
        
        print("\n🎉 积分管理菜单权限修复完成！")
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(fix_points_menu_permissions())
