#!/usr/bin/env python3
"""
积分划转功能全面测试
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.init_app import init_db
from app.models import User, PointsUsageRecord, PointsRechargeRecord
from app.controllers.points import points_transfer_controller


async def test_comprehensive_points_transfer():
    """全面测试积分划转功能"""
    print("🧪 开始积分划转功能全面测试...")
    
    # 初始化数据库
    await init_db()
    
    # 获取测试用户
    admin_user = await User.filter(username="admin").first()
    ag1_user = await User.filter(username="ag1").first()
    
    if not admin_user or not ag1_user:
        print("❌ 未找到admin或ag1用户")
        return False
    
    print(f"✅ 测试用户:")
    print(f"   - admin (ID: {admin_user.id}, 余额: {admin_user.points_balance})")
    print(f"   - ag1 (ID: {ag1_user.id}, 余额: {ag1_user.points_balance})")
    
    # 记录初始状态
    initial_admin_balance = admin_user.points_balance
    initial_ag1_balance = ag1_user.points_balance
    
    # 确保admin有足够的积分进行测试
    if admin_user.points_balance < 1000:
        admin_user.points_balance = 2000
        await admin_user.save()
        print(f"🔧 为admin用户设置积分余额: {admin_user.points_balance}")
    
    test_results = []
    
    # 测试1: 正常积分划转
    print(f"\n📋 测试1: 正常积分划转")
    try:
        transfer_points = 300
        result = await points_transfer_controller.transfer_points(
            from_user_id=admin_user.id,
            to_user_id=ag1_user.id,
            points=transfer_points,
            description="测试正常积分划转",
            remark="全面测试"
        )
        
        print(f"✅ 积分划转成功!")
        print(f"   - 划转ID: {result['transfer_id']}")
        print(f"   - 划转方余额: {result['from_user_balance']}")
        print(f"   - 接收方余额: {result['to_user_balance']}")
        
        # 验证余额变化
        expected_admin_balance = admin_user.points_balance - transfer_points
        expected_ag1_balance = ag1_user.points_balance + transfer_points
        
        if (result['from_user_balance'] == expected_admin_balance and 
            result['to_user_balance'] == expected_ag1_balance):
            print("✅ 余额变化正确")
            test_results.append(("正常积分划转", True))
        else:
            print("❌ 余额变化不正确")
            test_results.append(("正常积分划转", False))
            
        # 验证记录创建
        usage_record = await PointsUsageRecord.filter(id=result['usage_record_id']).first()
        recharge_record = await PointsRechargeRecord.filter(id=result['recharge_record_id']).first()
        
        if (usage_record and recharge_record and 
            usage_record.related_id == result['transfer_id'] and
            usage_record.points == transfer_points and
            recharge_record.points == transfer_points):
            print("✅ 记录创建正确")
        else:
            print("❌ 记录创建不正确")
            test_results.append(("记录创建", False))
            
        # 更新用户余额用于后续测试
        admin_user.points_balance = result['from_user_balance']
        ag1_user.points_balance = result['to_user_balance']
        
    except Exception as e:
        print(f"❌ 测试1失败: {str(e)}")
        test_results.append(("正常积分划转", False))
    
    # 测试2: 余额不足
    print(f"\n📋 测试2: 余额不足")
    try:
        await points_transfer_controller.transfer_points(
            from_user_id=ag1_user.id,
            to_user_id=admin_user.id,
            points=99999,
            description="测试余额不足",
            remark="全面测试"
        )
        print("❌ 应该抛出余额不足异常")
        test_results.append(("余额不足检查", False))
    except Exception as e:
        if "积分余额不足" in str(e):
            print(f"✅ 正确捕获余额不足异常: {str(e)}")
            test_results.append(("余额不足检查", True))
        else:
            print(f"❌ 异常类型不正确: {str(e)}")
            test_results.append(("余额不足检查", False))
    
    # 测试3: 自己给自己划转
    print(f"\n📋 测试3: 自己给自己划转")
    try:
        await points_transfer_controller.transfer_points(
            from_user_id=admin_user.id,
            to_user_id=admin_user.id,
            points=100,
            description="测试自己给自己划转",
            remark="全面测试"
        )
        print("❌ 应该抛出不能给自己划转异常")
        test_results.append(("自己给自己划转检查", False))
    except Exception as e:
        if "不能给自己划转积分" in str(e):
            print(f"✅ 正确捕获自己给自己划转异常: {str(e)}")
            test_results.append(("自己给自己划转检查", True))
        else:
            print(f"❌ 异常类型不正确: {str(e)}")
            test_results.append(("自己给自己划转检查", False))
    
    # 测试4: 无效积分数量
    print(f"\n📋 测试4: 无效积分数量")
    try:
        await points_transfer_controller.transfer_points(
            from_user_id=admin_user.id,
            to_user_id=ag1_user.id,
            points=0,
            description="测试无效积分数量",
            remark="全面测试"
        )
        print("❌ 应该抛出积分数量无效异常")
        test_results.append(("无效积分数量检查", False))
    except Exception as e:
        if "划转积分数量必须大于0" in str(e):
            print(f"✅ 正确捕获无效积分数量异常: {str(e)}")
            test_results.append(("无效积分数量检查", True))
        else:
            print(f"❌ 异常类型不正确: {str(e)}")
            test_results.append(("无效积分数量检查", False))
    
    # 测试5: 数据一致性检查
    print(f"\n📋 测试5: 数据一致性检查")
    try:
        # 再次获取用户最新数据
        admin_user_fresh = await User.filter(id=admin_user.id).first()
        ag1_user_fresh = await User.filter(id=ag1_user.id).first()
        
        print(f"   - admin最新余额: {admin_user_fresh.points_balance}")
        print(f"   - ag1最新余额: {ag1_user_fresh.points_balance}")
        
        # 检查积分总量是否守恒（除了我们手动设置的部分）
        total_change = (admin_user_fresh.points_balance + ag1_user_fresh.points_balance) - (initial_admin_balance + initial_ag1_balance)
        manual_addition = 2000 - initial_admin_balance if initial_admin_balance < 1000 else 0
        
        if abs(total_change - manual_addition) < 1:  # 允许1积分的误差
            print("✅ 积分总量守恒")
            test_results.append(("积分总量守恒", True))
        else:
            print(f"❌ 积分总量不守恒，变化: {total_change}, 预期: {manual_addition}")
            test_results.append(("积分总量守恒", False))
            
    except Exception as e:
        print(f"❌ 数据一致性检查失败: {str(e)}")
        test_results.append(("数据一致性检查", False))
    
    # 输出测试结果
    print(f"\n🎯 测试结果汇总:")
    print("=" * 50)
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print("=" * 50)
    print(f"总计: {passed}/{total} 项测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！积分划转功能正常工作")
        return True
    else:
        print("⚠️  部分测试失败，需要检查积分划转功能")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_comprehensive_points_transfer())
    sys.exit(0 if success else 1)
