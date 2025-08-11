#!/usr/bin/env python3
"""
测试积分使用记录的类型筛选功能
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.init_app import init_db
from app.models import User, PointsUsageRecord
from app.controllers.points import PointsUsageController


async def test_usage_type_filter():
    """测试积分使用记录的类型筛选功能"""
    print("🧪 测试积分使用记录的类型筛选功能...")
    
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
            "points": 10,
            "usage_type": "service_consumption",
            "description": "测试服务消费记录",
            "related_id": None,
            "remark": "测试数据"
        },
        {
            "user_id": ag1_user.id,
            "points": 20,
            "usage_type": "transfer_to_others",
            "description": "测试给他人划转记录",
            "related_id": None,
            "remark": "测试数据"
        },
        {
            "user_id": ag1_user.id,
            "points": 30,
            "usage_type": "generate_exchange_code",
            "description": "测试生成兑换码记录",
            "related_id": None,
            "remark": "测试数据"
        },
        {
            "user_id": ag1_user.id,
            "points": 40,
            "usage_type": "other",
            "description": "测试其他类型记录",
            "related_id": None,
            "remark": "测试数据"
        }
    ]
    
    # 清理之前的测试数据
    await PointsUsageRecord.filter(user_id=ag1_user.id, remark="测试数据").delete()
    print("🧹 清理之前的测试数据")
    
    # 创建测试记录
    created_records = []
    for record_data in test_records:
        record = await PointsUsageRecord.create(**record_data)
        created_records.append(record)
        print(f"✅ 创建测试记录: {record.usage_type} - {record.points}积分")
    
    # 测试筛选功能
    controller = PointsUsageController()
    
    print("\n🔍 测试筛选功能:")
    
    # 测试1: 无筛选条件
    records, total = await controller.get_user_usage_records(ag1_user.id)
    print(f"  无筛选条件: 找到 {len(records)} 条记录，总数 {total}")
    
    # 测试2: 筛选服务消费
    records, total = await controller.get_user_usage_records(
        ag1_user.id, usage_type="service_consumption"
    )
    print(f"  服务消费筛选: 找到 {len(records)} 条记录，总数 {total}")
    assert len(records) == 1, f"期望1条记录，实际{len(records)}条"
    assert records[0].usage_type == "service_consumption"
    
    # 测试3: 筛选给他人划转
    records, total = await controller.get_user_usage_records(
        ag1_user.id, usage_type="transfer_to_others"
    )
    print(f"  给他人划转筛选: 找到 {len(records)} 条记录，总数 {total}")
    assert len(records) == 1, f"期望1条记录，实际{len(records)}条"
    assert records[0].usage_type == "transfer_to_others"
    
    # 测试4: 筛选生成兑换码
    records, total = await controller.get_user_usage_records(
        ag1_user.id, usage_type="generate_exchange_code"
    )
    print(f"  生成兑换码筛选: 找到 {len(records)} 条记录，总数 {total}")
    assert len(records) == 1, f"期望1条记录，实际{len(records)}条"
    assert records[0].usage_type == "generate_exchange_code"
    
    # 测试5: 筛选其他
    records, total = await controller.get_user_usage_records(
        ag1_user.id, usage_type="other"
    )
    print(f"  其他类型筛选: 找到 {len(records)} 条记录，总数 {total}")
    assert len(records) == 1, f"期望1条记录，实际{len(records)}条"
    assert records[0].usage_type == "other"
    
    # 测试6: 筛选不存在的类型
    records, total = await controller.get_user_usage_records(
        ag1_user.id, usage_type="non_existent_type"
    )
    print(f"  不存在类型筛选: 找到 {len(records)} 条记录，总数 {total}")
    assert len(records) == 0, f"期望0条记录，实际{len(records)}条"
    
    print("\n✅ 所有筛选测试通过！")
    
    # 清理测试数据
    await PointsUsageRecord.filter(user_id=ag1_user.id, remark="测试数据").delete()
    print("🧹 清理测试数据完成")
    
    print("\n🎉 积分使用记录类型筛选功能测试完成！")


if __name__ == "__main__":
    asyncio.run(test_usage_type_filter())
