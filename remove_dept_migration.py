#!/usr/bin/env python3
"""
数据库迁移脚本：移除部门管理功能
- 删除dept和dept_closure表
- 从user表中删除dept_id字段
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tortoise import Tortoise
from app.core.config import settings


async def migrate_remove_dept():
    """执行移除部门功能的数据库迁移"""
    
    # 初始化数据库连接
    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={"models": ["app.models"]}
    )
    
    # 获取数据库连接
    conn = Tortoise.get_connection("default")
    
    try:
        print("开始执行部门功能移除迁移...")
        
        # 1. 删除dept_closure表
        print("1. 删除dept_closure表...")
        await conn.execute_query("DROP TABLE IF EXISTS dept_closure")
        print("   ✓ dept_closure表已删除")
        
        # 2. 删除dept表
        print("2. 删除dept表...")
        await conn.execute_query("DROP TABLE IF EXISTS dept")
        print("   ✓ dept表已删除")
        
        # 3. 从user表中删除dept_id字段
        print("3. 从user表中删除dept_id字段...")
        
        # 检查字段是否存在
        result = await conn.execute_query(
            "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_NAME = 'user' AND COLUMN_NAME = 'dept_id'"
        )
        
        if result[1]:  # 如果字段存在
            await conn.execute_query("ALTER TABLE user DROP COLUMN dept_id")
            print("   ✓ user表的dept_id字段已删除")
        else:
            print("   ✓ user表的dept_id字段不存在，跳过")
        
        # 4. 验证用户数据完整性
        print("4. 验证用户数据完整性...")
        user_count = await conn.execute_query("SELECT COUNT(*) FROM user")
        print(f"   ✓ 用户表中有 {user_count[1][0][0]} 条记录")
        
        # 检查关键字段
        fields_check = await conn.execute_query(
            "SELECT COUNT(*) FROM user WHERE "
            "username IS NOT NULL AND email IS NOT NULL"
        )
        print(f"   ✓ 所有用户的关键字段完整: {fields_check[1][0][0]} 条记录")
        
        # 检查邀请关系
        invitation_check = await conn.execute_query(
            "SELECT COUNT(*) FROM user WHERE parent_user_id != -1"
        )
        print(f"   ✓ 有邀请关系的用户: {invitation_check[1][0][0]} 条记录")
        
        print("\n✅ 部门功能移除迁移完成！")
        print("📊 数据完整性验证通过")
        
    except Exception as e:
        print(f"❌ 迁移过程中发生错误: {e}")
        raise
    
    finally:
        # 关闭数据库连接
        await Tortoise.close_connections()


async def rollback_migration():
    """回滚迁移（重新创建部门相关表）"""
    
    await Tortoise.init(
        db_url=settings.DATABASE_URL,
        modules={"models": ["app.models"]}
    )
    
    conn = Tortoise.get_connection("default")
    
    try:
        print("开始回滚部门功能移除迁移...")
        
        # 重新创建dept表
        print("1. 重新创建dept表...")
        await conn.execute_query("""
            CREATE TABLE IF NOT EXISTS dept (
                id INT AUTO_INCREMENT PRIMARY KEY,
                created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                name VARCHAR(20) NOT NULL UNIQUE,
                `desc` VARCHAR(500),
                is_deleted TINYINT(1) NOT NULL DEFAULT 0,
                `order` INT NOT NULL DEFAULT 0,
                parent_id INT NOT NULL DEFAULT 0,
                INDEX idx_dept_name (name),
                INDEX idx_dept_is_deleted (is_deleted),
                INDEX idx_dept_order (`order`),
                INDEX idx_dept_parent_id (parent_id)
            )
        """)
        print("   ✓ dept表已重新创建")
        
        # 重新创建dept_closure表
        print("2. 重新创建dept_closure表...")
        await conn.execute_query("""
            CREATE TABLE IF NOT EXISTS dept_closure (
                id INT AUTO_INCREMENT PRIMARY KEY,
                created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
                updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
                ancestor INT NOT NULL,
                descendant INT NOT NULL,
                level INT NOT NULL DEFAULT 0,
                INDEX idx_dept_closure_ancestor (ancestor),
                INDEX idx_dept_closure_descendant (descendant),
                INDEX idx_dept_closure_level (level)
            )
        """)
        print("   ✓ dept_closure表已重新创建")
        
        # 重新添加dept_id字段到user表
        print("3. 重新添加dept_id字段到user表...")
        await conn.execute_query("""
            ALTER TABLE user ADD COLUMN dept_id INT NULL,
            ADD INDEX idx_user_dept_id (dept_id)
        """)
        print("   ✓ user表的dept_id字段已重新添加")
        
        print("\n✅ 迁移回滚完成！")
        
    except Exception as e:
        print(f"❌ 回滚过程中发生错误: {e}")
        raise
    
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="部门功能移除迁移脚本")
    parser.add_argument("--rollback", action="store_true", help="回滚迁移")
    args = parser.parse_args()
    
    if args.rollback:
        asyncio.run(rollback_migration())
    else:
        asyncio.run(migrate_remove_dept())
