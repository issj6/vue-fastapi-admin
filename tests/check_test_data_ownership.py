#!/usr/bin/env python3
"""
检查测试数据的用户归属
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.admin import User
from app.models import PointsUsageRecord
from app.core.init_app import init_db


async def check_test_data_ownership():
    """检查测试数据的用户归属"""
    print("🔧 初始化数据库连接...")
    await init_db()

    print("\n🔍 检查测试数据的用户归属...")

    # 1. 查找ag1用户
    ag1_user = await User.filter(username="ag1").first()
    if not ag1_user:
        print("❌ 未找到ag1用户")
        return

    print(f"✅ ag1用户信息:")
    print(f"   - ID: {ag1_user.id}")
    print(f"   - 用户名: {ag1_user.username}")

    # 2. 查找所有测试数据
    test_records = await PointsUsageRecord.filter(remark="前端测试数据").all()
    print(f"\n📋 测试数据记录 (共{len(test_records)}条):")
    for record in test_records:
        user = await User.filter(id=record.user_id).first()
        print(f"   - 记录ID: {record.id}")
        print(f"     * 用户ID: {record.user_id}")
        print(f"     * 用户名: {user.username if user else '未知'}")
        print(f"     * 积分: {record.points}")
        print(f"     * 类型: {record.usage_type}")
        print(f"     * 描述: {record.description}")

    # 3. 检查ag1用户的所有记录
    ag1_records = await PointsUsageRecord.filter(user_id=ag1_user.id).all()
    print(f"\n📊 ag1用户的所有积分使用记录 (共{len(ag1_records)}条):")
    for record in ag1_records:
        print(f"   - 记录ID: {record.id}")
        print(f"     * 积分: {record.points}")
        print(f"     * 类型: {record.usage_type}")
        print(f"     * 描述: {record.description}")
        print(f"     * 备注: {record.remark}")
        print(f"     * 创建时间: {record.created_at}")

    # 4. 检查其他用户的记录
    all_records = await PointsUsageRecord.all()
    user_record_count = {}
    for record in all_records:
        user_id = record.user_id
        if user_id not in user_record_count:
            user_record_count[user_id] = 0
        user_record_count[user_id] += 1

    print(f"\n📈 所有用户的记录统计:")
    for user_id, count in user_record_count.items():
        user = await User.filter(id=user_id).first()
        username = user.username if user else f"用户ID:{user_id}"
        print(f"   - {username}: {count}条记录")

    print("\n✅ 测试数据归属检查完成")


if __name__ == "__main__":
    asyncio.run(check_test_data_ownership())
