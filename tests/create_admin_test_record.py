#!/usr/bin/env python3
"""
为admin用户创建测试记录，验证权限隔离
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.admin import User
from app.models import PointsUsageRecord
from app.core.init_app import init_db


async def create_admin_test_record():
    """为admin用户创建测试记录"""
    print("🔧 初始化数据库连接...")
    await init_db()

    print("\n📝 为admin用户创建测试记录...")

    # 1. 查找admin用户
    admin_user = await User.filter(username="admin").first()
    if not admin_user:
        print("❌ 未找到admin用户")
        return

    print(f"✅ admin用户信息:")
    print(f"   - ID: {admin_user.id}")
    print(f"   - 用户名: {admin_user.username}")

    # 2. 创建admin的测试记录
    admin_record = await PointsUsageRecord.create(
        user_id=admin_user.id,
        points=999,
        usage_type="service_consumption",
        description="管理员专用服务消费",
        related_id=9999,
        remark="管理员测试数据"
    )

    print(f"✅ 为admin创建测试记录:")
    print(f"   - 记录ID: {admin_record.id}")
    print(f"   - 积分: {admin_record.points}")
    print(f"   - 类型: {admin_record.usage_type}")
    print(f"   - 描述: {admin_record.description}")

    # 3. 验证数据隔离
    print(f"\n🔍 验证数据隔离:")
    
    # ag1用户的记录
    ag1_user = await User.filter(username="ag1").first()
    ag1_records = await PointsUsageRecord.filter(user_id=ag1_user.id).all()
    print(f"   ag1用户记录数: {len(ag1_records)}")
    
    # admin用户的记录
    admin_records = await PointsUsageRecord.filter(user_id=admin_user.id).all()
    print(f"   admin用户记录数: {len(admin_records)}")
    
    # 所有记录
    all_records = await PointsUsageRecord.all()
    print(f"   总记录数: {len(all_records)}")

    print(f"\n🎯 现在ag1用户应该只能看到自己的{len(ag1_records)}条记录")
    print(f"   如果ag1能看到admin的记录，说明权限控制有问题")

    print("\n✅ admin测试记录创建完成")


if __name__ == "__main__":
    asyncio.run(create_admin_test_record())
