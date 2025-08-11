#!/usr/bin/env python3
"""
数据库迁移：添加user_level字段到role表
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tortoise import Tortoise
from app.settings.config import settings


async def add_user_level_column():
    """添加user_level字段到role表"""
    print("🔄 开始添加user_level字段...")
    
    # 初始化数据库连接
    await Tortoise.init(config=settings.TORTOISE_ORM)
    
    # 获取数据库连接
    conn = Tortoise.get_connection("mysql")
    
    try:
        # 检查字段是否已存在
        print("\n1️⃣ 检查user_level字段是否存在...")
        
        check_column_sql = """
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = DATABASE() 
        AND TABLE_NAME = 'role' 
        AND COLUMN_NAME = 'user_level'
        """
        
        result = await conn.execute_query(check_column_sql)
        
        if result[1]:  # 如果有结果，说明字段已存在
            print("   ⚠️ user_level字段已存在，跳过添加")
        else:
            print("   ✅ user_level字段不存在，开始添加...")
            
            # 添加user_level字段
            add_column_sql = """
            ALTER TABLE role 
            ADD COLUMN user_level INT DEFAULT 99 COMMENT '角色层级，数字越小权限越高'
            """
            
            await conn.execute_query(add_column_sql)
            print("   ✅ 成功添加user_level字段")
            
            # 添加索引
            add_index_sql = """
            ALTER TABLE role 
            ADD INDEX idx_role_user_level (user_level)
            """
            
            await conn.execute_query(add_index_sql)
            print("   ✅ 成功添加user_level索引")
        
        # 验证字段添加
        print("\n2️⃣ 验证字段添加...")
        
        verify_sql = """
        DESCRIBE role
        """
        
        result = await conn.execute_query(verify_sql)
        
        print("   role表结构:")
        if result[1]:
            for row in result[1]:
                if isinstance(row, (list, tuple)) and len(row) >= 5:
                    field_name = row[0]
                    field_type = row[1]
                    is_null = row[2]
                    default_value = row[4]

                    if field_name == 'user_level':
                        print(f"     ✅ {field_name}: {field_type}, NULL: {is_null}, Default: {default_value}")
                    else:
                        print(f"     {field_name}: {field_type}")
                else:
                    print(f"     {row}")
        else:
            print("     无法获取表结构信息")
        
        print("\n🎉 user_level字段添加完成！")
        
    except Exception as e:
        print(f"❌ 添加字段失败: {e}")
        raise
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(add_user_level_column())
