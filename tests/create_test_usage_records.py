#!/usr/bin/env python3
"""
为ag1用户创建测试积分使用记录
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.init_app import init_db
from app.models import User, PointsUsageRecord


async def create_test_usage_records():
    """为ag1用户创建测试积分使用记录"""
    print("📝 为ag1用户创建测试积分使用记录...")
    
    # 初始化数据库
    await init_db()
    
    # 获取ag1用户
    ag1_user = await User.filter(username="ag1").first()
    if not ag1_user:
        print("❌ 未找到ag1用户")
        return
    
    print(f"✅ 找到ag1用户 (ID: {ag1_user.id})")
    
    # 创建测试数据
    test_records = [
        {
            "user_id": ag1_user.id,
            "points": 50,
            "usage_type": "service_consumption",
            "description": "API调用服务消费",
            "related_id": 1001,
            "remark": "前端测试数据"
        },
        {
            "user_id": ag1_user.id,
            "points": 100,
            "usage_type": "transfer_to_others",
            "description": "给用户user123划转积分",
            "related_id": 1002,
            "remark": "前端测试数据"
        },
        {
            "user_id": ag1_user.id,
            "points": 200,
            "usage_type": "generate_exchange_code",
            "description": "生成兑换码CODE123",
            "related_id": 1003,
            "remark": "前端测试数据"
        },
        {
            "user_id": ag1_user.id,
            "points": 75,
            "usage_type": "other",
            "description": "系统维护费用",
            "related_id": None,
            "remark": "前端测试数据"
        },
        {
            "user_id": ag1_user.id,
            "points": 30,
            "usage_type": "service_consumption",
            "description": "文档生成服务",
            "related_id": 1004,
            "remark": "前端测试数据"
        }
    ]
    
    # 清理之前的测试数据
    await PointsUsageRecord.filter(user_id=ag1_user.id, remark="前端测试数据").delete()
    print("🧹 清理之前的测试数据")
    
    # 创建测试记录
    created_records = []
    for record_data in test_records:
        record = await PointsUsageRecord.create(**record_data)
        created_records.append(record)
        print(f"✅ 创建测试记录: {record.usage_type} - {record.points}积分 - {record.description}")
    
    print(f"\n🎉 成功创建 {len(created_records)} 条测试记录！")
    print("现在可以在前端测试筛选功能了。")


if __name__ == "__main__":
    asyncio.run(create_test_usage_records())
