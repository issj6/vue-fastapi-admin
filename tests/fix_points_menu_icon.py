#!/usr/bin/env python3
"""
为积分管理菜单添加图标
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.admin import Menu
from app.core.init_app import init_db


async def fix_points_menu_icon():
    """为积分管理菜单添加图标"""
    print("🔧 初始化数据库连接...")
    await init_db()
    
    print("\n🔧 为积分管理菜单添加图标...")
    
    try:
        # 修复积分管理主菜单图标
        points_menu = await Menu.filter(path="/points").first()
        if points_menu:
            points_menu.icon = "CreditCardOutlined"
            await points_menu.save()
            print(f"✅ 为积分管理主菜单添加图标: {points_menu.icon}")
        
        print("\n🎉 积分管理菜单图标修复完成！")
        
        # 验证修复结果
        print("\n📋 验证修复结果:")
        all_points_menus = await Menu.filter(name__in=["积分管理", "积分信息", "使用记录"]).all()
        for menu in all_points_menus:
            print(f"   - {menu.name}: 图标={menu.icon}, 路径={menu.path}")
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(fix_points_menu_icon())
