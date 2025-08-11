#!/usr/bin/env python3
"""
创建积分管理相关的数据库表
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tortoise import Tortoise
from app.models.points import PointsRechargeRecord, PointsUsageRecord, ExchangeCode


async def create_points_tables():
    """创建积分管理相关的数据库表"""
    
    # 初始化数据库连接（使用项目配置）
    from app.settings import settings
    await Tortoise.init(config=settings.TORTOISE_ORM)
    
    print("🔧 开始创建积分管理相关数据库表...")
    
    try:
        # 生成表结构
        await Tortoise.generate_schemas()
        
        print("✅ 积分管理数据库表创建成功！")
        print("📋 创建的表包括：")
        print("   - points_recharge_record (积分充值记录表)")
        print("   - points_usage_record (积分使用记录表)")
        print("   - exchange_code (兑换码表)")
        
        # 创建一些测试兑换码
        await create_test_exchange_codes()
        
    except Exception as e:
        print(f"❌ 创建数据库表失败: {e}")
        
    finally:
        await Tortoise.close_connections()


async def create_test_exchange_codes():
    """创建一些测试兑换码"""
    from datetime import datetime, timedelta
    
    test_codes = [
        {"code": "TEST100", "points": 100, "remark": "测试兑换码 - 100积分"},
        {"code": "TEST500", "points": 500, "remark": "测试兑换码 - 500积分"},
        {"code": "WELCOME50", "points": 50, "remark": "新用户欢迎积分"},
    ]
    
    for code_data in test_codes:
        # 检查兑换码是否已存在
        existing_code = await ExchangeCode.filter(code=code_data["code"]).first()
        if not existing_code:
            await ExchangeCode.create(
                code=code_data["code"],
                points=code_data["points"],
                expires_at=datetime.now() + timedelta(days=365),  # 1年后过期
                remark=code_data["remark"]
            )
            print(f"   ✅ 创建测试兑换码: {code_data['code']} ({code_data['points']}积分)")
        else:
            print(f"   ⚠️  兑换码已存在: {code_data['code']}")


if __name__ == "__main__":
    asyncio.run(create_points_tables())
