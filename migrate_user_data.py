#!/usr/bin/env python3
"""
用户数据迁移脚本
为现有用户生成邀请码
"""

import asyncio
import sys
from tortoise import Tortoise
from app.settings import TORTOISE_ORM
from app.models.admin import User
from app.utils.invitation_code import generate_unique_invitation_code


async def migrate_user_invitation_codes():
    """为现有用户生成邀请码"""
    try:
        # 初始化数据库连接
        await Tortoise.init(config=TORTOISE_ORM)
        
        print("🔄 开始为现有用户生成邀请码...")
        
        # 查找没有邀请码的用户
        users_without_code = await User.filter(invitation_code__isnull=True).all()
        users_with_empty_code = await User.filter(invitation_code="").all()
        
        all_users_need_code = users_without_code + users_with_empty_code
        
        if not all_users_need_code:
            print("✅ 所有用户都已有邀请码")
            return
        
        print(f"📊 找到 {len(all_users_need_code)} 个用户需要生成邀请码")
        
        success_count = 0
        for user in all_users_need_code:
            try:
                # 生成唯一邀请码
                invitation_code = await generate_unique_invitation_code()
                user.invitation_code = invitation_code
                await user.save()
                
                print(f"✅ 用户 {user.username} 生成邀请码: {invitation_code}")
                success_count += 1
                
            except Exception as e:
                print(f"❌ 用户 {user.username} 生成邀请码失败: {e}")
        
        print(f"🎉 成功为 {success_count}/{len(all_users_need_code)} 个用户生成邀请码")
        
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        return False
    finally:
        await Tortoise.close_connections()
    
    return True


async def check_user_data():
    """检查用户数据状态"""
    try:
        await Tortoise.init(config=TORTOISE_ORM)
        
        print("📊 用户数据统计:")
        print("=" * 40)
        
        total_users = await User.all().count()
        users_with_invitation_code = await User.filter(invitation_code__not="").count()
        users_with_parent = await User.filter(parent_user_id__not=-1).count()
        total_points = await User.all().values_list('points_balance', flat=True)
        total_points_sum = sum(total_points) if total_points else 0
        
        print(f"总用户数: {total_users}")
        print(f"有邀请码的用户: {users_with_invitation_code}")
        print(f"有上级用户的用户: {users_with_parent}")
        print(f"总积分: {total_points_sum}")
        
        # 显示一些示例用户
        print("\n👥 用户示例:")
        users = await User.all().limit(5)
        for user in users:
            print(f"  - {user.username}: 邀请码={user.invitation_code}, 上级ID={user.parent_user_id}, 积分={user.points_balance}")
        
        print("=" * 40)
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
    finally:
        await Tortoise.close_connections()


async def main():
    """主函数"""
    print("🚀 开始用户数据迁移...")
    
    # 检查当前状态
    await check_user_data()
    
    # 执行迁移
    success = await migrate_user_invitation_codes()
    
    if success:
        print("\n✅ 迁移完成，检查最终状态:")
        await check_user_data()
    else:
        print("❌ 迁移失败")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
