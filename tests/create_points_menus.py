#!/usr/bin/env python3
"""
创建积分管理菜单
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tortoise import Tortoise
from app.models.admin import Menu


async def create_points_menus():
    """创建积分管理菜单"""
    
    # 初始化数据库连接
    from app.settings import settings
    await Tortoise.init(config=settings.TORTOISE_ORM)
    
    print("🔧 开始创建积分管理菜单...")
    
    try:
        # 1. 创建积分管理主菜单
        points_main_menu = await Menu.filter(path="/points").first()
        if not points_main_menu:
            points_main_menu = await Menu.create(
                name="积分管理",
                path="/points",
                component="",
                redirect="/points/info",
                icon="CreditCardOutlined",
                parent_id=0,
                sort=4,
                is_hidden=False,
                meta={
                    "title": "积分管理",
                    "icon": "CreditCardOutlined",
                    "keepAlive": True
                }
            )
            print("✅ 创建积分管理主菜单")
        else:
            print("⚠️  积分管理主菜单已存在")
        
        # 2. 创建积分信息子菜单
        points_info_menu = await Menu.filter(path="/points/info").first()
        if not points_info_menu:
            await Menu.create(
                name="积分信息",
                path="/points/info",
                component="points/info/index",
                icon="WalletOutlined",
                parent_id=points_main_menu.id,
                sort=1,
                is_hidden=False,
                meta={
                    "title": "积分信息",
                    "icon": "WalletOutlined",
                    "keepAlive": True
                }
            )
            print("✅ 创建积分信息子菜单")
        else:
            print("⚠️  积分信息子菜单已存在")
        
        # 3. 创建使用记录子菜单
        points_usage_menu = await Menu.filter(path="/points/usage").first()
        if not points_usage_menu:
            await Menu.create(
                name="使用记录",
                path="/points/usage",
                component="points/usage/index",
                icon="HistoryOutlined",
                parent_id=points_main_menu.id,
                sort=2,
                is_hidden=False,
                meta={
                    "title": "使用记录",
                    "icon": "HistoryOutlined",
                    "keepAlive": True
                }
            )
            print("✅ 创建使用记录子菜单")
        else:
            print("⚠️  使用记录子菜单已存在")
        
        print("🎉 积分管理菜单创建完成！")
        
    except Exception as e:
        print(f"❌ 创建菜单失败: {e}")
        
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(create_points_menus())
