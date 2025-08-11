#!/usr/bin/env python3
"""
修复积分管理菜单的组件路径
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.admin import Menu
from app.core.init_app import init_db


async def fix_points_component_paths():
    """修复积分管理菜单的组件路径"""
    print("🔧 初始化数据库连接...")
    await init_db()
    
    print("\n🔧 修复积分管理菜单的组件路径...")
    
    try:
        # 1. 修复积分管理主菜单
        points_menu = await Menu.filter(path="/points").first()
        if points_menu:
            points_menu.component = "Layout"
            await points_menu.save()
            print(f"✅ 修复积分管理主菜单组件路径: {points_menu.component}")
        
        # 2. 修复积分信息子菜单
        points_info_menu = await Menu.filter(path="/points/info").first()
        if points_info_menu:
            points_info_menu.component = "/points/info"
            await points_info_menu.save()
            print(f"✅ 修复积分信息菜单组件路径: {points_info_menu.component}")
        
        # 3. 修复使用记录子菜单
        points_usage_menu = await Menu.filter(path="/points/usage").first()
        if points_usage_menu:
            points_usage_menu.component = "/points/usage"
            await points_usage_menu.save()
            print(f"✅ 修复使用记录菜单组件路径: {points_usage_menu.component}")
        
        print("\n🎉 积分管理菜单组件路径修复完成！")
        
        # 4. 验证修复结果
        print("\n📋 验证修复结果:")
        all_points_menus = await Menu.filter(path__startswith="/points").all()
        for menu in all_points_menus:
            print(f"   - {menu.name}: 路径={menu.path}, 组件={menu.component}")
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(fix_points_component_paths())
