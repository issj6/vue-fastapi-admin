#!/usr/bin/env python3
"""
修复子菜单路径为相对路径
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.admin import Menu
from app.core.init_app import init_db


async def fix_submenu_paths():
    """修复子菜单路径为相对路径"""
    print("🔧 初始化数据库连接...")
    await init_db()
    
    print("\n🔧 修复积分管理子菜单路径...")
    
    try:
        # 修复积分信息子菜单路径
        points_info_menu = await Menu.filter(path="/points/info").first()
        if points_info_menu:
            points_info_menu.path = "info"
            await points_info_menu.save()
            print(f"✅ 修复积分信息菜单路径: {points_info_menu.path}")
        
        # 修复使用记录子菜单路径
        points_usage_menu = await Menu.filter(path="/points/usage").first()
        if points_usage_menu:
            points_usage_menu.path = "usage"
            await points_usage_menu.save()
            print(f"✅ 修复使用记录菜单路径: {points_usage_menu.path}")
        
        print("\n🎉 子菜单路径修复完成！")
        
        # 验证修复结果
        print("\n📋 验证修复结果:")
        all_points_menus = await Menu.filter(name__in=["积分管理", "积分信息", "使用记录"]).all()
        for menu in all_points_menus:
            print(f"   - {menu.name}: 路径={menu.path}, 父级ID={menu.parent_id}")
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(fix_submenu_paths())
