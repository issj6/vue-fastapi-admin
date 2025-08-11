#!/usr/bin/env python3
"""
数据库状态检查脚本
检查当前数据库连接状态和基本数据
"""

import asyncio
import sys
from tortoise import Tortoise
from app.settings import TORTOISE_ORM
from app.models.admin import User, Role, Menu, Api, Dept


async def check_database_status():
    """检查数据库状态"""
    try:
        # 初始化数据库连接
        await Tortoise.init(config=TORTOISE_ORM)
        
        print("🔗 数据库连接成功！")
        print("=" * 50)
        
        # 检查数据库配置
        connection = Tortoise.get_connection("mysql")
        print(f"📊 数据库类型: MySQL (asyncmy)")
        
        # 检查各表的数据量
        user_count = await User.all().count()
        role_count = await Role.all().count()
        menu_count = await Menu.all().count()
        api_count = await Api.all().count()
        dept_count = await Dept.all().count()
        
        print(f"👥 用户数量: {user_count}")
        print(f"🔐 角色数量: {role_count}")
        print(f"📋 菜单数量: {menu_count}")
        print(f"🔌 API数量: {api_count}")
        print(f"🏢 部门数量: {dept_count}")
        
        # 检查管理员用户
        admin_user = await User.filter(username="admin").first()
        if admin_user:
            print(f"✅ 管理员账户存在: {admin_user.username} ({admin_user.email})")
            print(f"   超级用户: {'是' if admin_user.is_superuser else '否'}")
            print(f"   账户状态: {'激活' if admin_user.is_active else '禁用'}")
        else:
            print("❌ 管理员账户不存在")
        
        # 检查角色权限
        if role_count > 0:
            print("\n🔐 角色信息:")
            roles = await Role.all()
            for role in roles:
                role_menus = await role.menus.all().count()
                role_apis = await role.apis.all().count()
                print(f"   - {role.name}: {role_menus}个菜单, {role_apis}个API权限")
        
        print("=" * 50)
        print("✅ 数据库状态检查完成！")
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False
    finally:
        await Tortoise.close_connections()
    
    return True


async def main():
    """主函数"""
    print("🔍 开始检查数据库状态...")
    success = await check_database_status()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
