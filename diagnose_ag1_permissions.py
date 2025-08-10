#!/usr/bin/env python3
"""
诊断ag1用户权限问题
"""

import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.admin import User, Role, Api
from app.core.init_app import init_db
from app.core.menu_permissions import MenuPermissionMapping


async def diagnose_ag1_permissions():
    """诊断ag1用户权限问题"""
    print("🔧 初始化数据库连接...")
    await init_db()
    
    print("\n🔍 诊断ag1用户权限问题...")
    
    # 查找ag1用户
    ag1_user = await User.filter(username="ag1").first()
    if not ag1_user:
        print("❌ 未找到ag1用户")
        return
    
    print(f"✅ 找到用户: {ag1_user.username} (ID: {ag1_user.id})")
    print(f"   - 邮箱: {ag1_user.email}")
    print(f"   - 是否激活: {ag1_user.is_active}")
    print(f"   - 是否超级管理员: {ag1_user.is_superuser}")
    
    # 查看用户角色
    roles = await ag1_user.roles.all()
    print(f"\n👤 用户角色 (共{len(roles)}个):")
    for role in roles:
        print(f"   - {role.name} (ID: {role.id})")
        print(f"     * 是否代理角色: {role.is_agent_role}")
        print(f"     * 代理权限: {role.agent_permissions}")
        
        # 检查菜单权限
        menus = await role.menus.all()
        print(f"     * 菜单权限 (共{len(menus)}个): {[menu.name for menu in menus]}")
        
        # 检查API权限
        apis = await role.apis.all()
        print(f"     * API权限 (共{len(apis)}个):")
        for api in apis[:5]:  # 只显示前5个
            print(f"       - {api.method} {api.path}")
        if len(apis) > 5:
            print(f"       ... 还有{len(apis)-5}个API权限")
    
    # 检查创建用户相关的权限
    print(f"\n🔑 创建用户权限检查:")
    
    # 检查代理权限中是否包含CREATE_USER
    has_create_user_permission = False
    for role in roles:
        if role.is_agent_role and role.agent_permissions:
            if "CREATE_USER" in role.agent_permissions:
                has_create_user_permission = True
                print(f"   ✅ 角色 '{role.name}' 拥有CREATE_USER代理权限")
            else:
                print(f"   ❌ 角色 '{role.name}' 缺少CREATE_USER代理权限")
    
    if not has_create_user_permission:
        print("   ❌ 用户没有CREATE_USER代理权限")
    
    # 检查创建用户API权限
    create_user_api = await Api.filter(path="/api/v1/user/create", method="POST").first()
    if create_user_api:
        print(f"   📋 创建用户API: {create_user_api.method} {create_user_api.path}")
        
        # 检查用户是否有直接的API权限
        has_direct_api_permission = False
        for role in roles:
            role_apis = await role.apis.all()
            if create_user_api in role_apis:
                has_direct_api_permission = True
                print(f"   ✅ 角色 '{role.name}' 拥有直接的创建用户API权限")
        
        if not has_direct_api_permission:
            print("   ⚠️  用户没有直接的创建用户API权限（应通过代理权限映射获得）")
    else:
        print("   ❌ 未找到创建用户API")
    
    # 检查权限映射
    print(f"\n🗺️  权限映射检查:")
    if "CREATE_USER" in MenuPermissionMapping.PERMISSION_API_MAP:
        mapped_apis = MenuPermissionMapping.PERMISSION_API_MAP["CREATE_USER"]
        print(f"   CREATE_USER权限映射的API:")
        for method, path in mapped_apis:
            print(f"     - {method} {path}")
    else:
        print("   ❌ CREATE_USER权限没有API映射配置")
    
    # 检查角色列表API权限（创建用户时需要）
    role_list_api = await Api.filter(path="/api/v1/role/list", method="GET").first()
    if role_list_api:
        print(f"\n📋 角色列表API检查: {role_list_api.method} {role_list_api.path}")
        has_role_list_permission = False
        for role in roles:
            role_apis = await role.apis.all()
            if role_list_api in role_apis:
                has_role_list_permission = True
                print(f"   ✅ 角色 '{role.name}' 拥有角色列表API权限")
        
        if not has_role_list_permission:
            print("   ⚠️  用户没有角色列表API权限（创建用户时需要获取角色列表）")
    
    print("\n✅ ag1用户权限诊断完成")


if __name__ == "__main__":
    asyncio.run(diagnose_ag1_permissions())
