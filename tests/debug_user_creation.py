#!/usr/bin/env python3
"""
调试用户创建功能
"""

import asyncio
import sys
import os
import traceback

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.admin import User
from app.core.init_app import init_db
from app.controllers.user import user_controller
from app.schemas.users import UserCreate


async def debug_user_creation():
    """调试用户创建功能"""
    print("🔧 初始化数据库连接...")
    await init_db()
    
    print("\n🔍 调试用户创建功能...")
    
    try:
        # 创建测试用户数据
        user_data = UserCreate(
            username="debug_test_user",
            email="debug_test_user@example.com",
            password="123456",
            is_active=True,
            school="测试学校",
            major="测试专业"
        )
        
        print(f"📋 用户数据: {user_data}")
        print(f"📋 create_dict(): {user_data.create_dict()}")
        
        # 检查邮箱是否已存在
        existing_user = await user_controller.get_by_email(user_data.email)
        if existing_user:
            print(f"⚠️  邮箱已存在，删除现有用户...")
            await User.filter(email=user_data.email).delete()
        
        # 尝试创建用户
        print(f"🔨 开始创建用户...")
        new_user = await user_controller.create_user(obj_in=user_data)
        print(f"✅ 用户创建成功: {new_user.username} (ID: {new_user.id})")
        
        # 尝试更新角色
        print(f"🔨 开始更新用户角色...")
        await user_controller.update_roles(new_user, [1])  # 管理员角色
        print(f"✅ 角色更新成功")
        
        print(f"🎉 用户创建和角色分配完成！")
        
    except Exception as e:
        print(f"❌ 用户创建失败: {str(e)}")
        print(f"📋 错误详情:")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_user_creation())
