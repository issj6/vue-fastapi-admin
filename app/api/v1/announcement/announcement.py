import logging
from datetime import datetime
from typing import Optional, List
import jwt

from fastapi import APIRouter, Body, Query, Request
from tortoise.expressions import Q

from app.controllers.announcement import announcement_controller
from app.core.ctx import CTX_USER_ID
from app.core.dependency import DependAuth
from app.models.admin import User
from app.models.enums import AnnouncementType
from app.schemas.base import Fail, Success, SuccessExtra
from app.schemas.announcement import AnnouncementCreate, AnnouncementUpdate, AnnouncementResponse
from app.settings.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_optional_current_user_id(request: Request) -> Optional[int]:
    """
    可选的用户认证，不会抛出异常
    返回用户ID或None
    """
    try:
        # 检查token header（项目使用的认证方式）
        token = request.headers.get("token")
        if not token:
            # 备用：检查Authorization header
            authorization = request.headers.get("Authorization")
            if authorization:
                token = authorization.replace("Bearer ", "")
            else:
                return None
            
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("user_id")
        return user_id if user_id else None
    except Exception as e:
        logger.debug(f"Token解析失败: {e}")
        return None


@router.get("/active", summary="获取当前有效公告")
async def get_active_announcements(request: Request):
    """
    根据用户认证状态和角色层级智能返回公告
    - 未登录用户：返回前台公告
    - 普通用户(层级99)：返回前台公告  
    - 代理/管理员(层级<99)：返回代理公告
    """
    announcement_type = AnnouncementType.FRONTEND  # 默认返回前台公告
    
    # 尝试获取当前用户信息（可选认证）
    try:
        user_id = await get_optional_current_user_id(request)
        
        if user_id:
            # 用户已登录，检查角色层级
            user = await User.filter(id=user_id).first()
            if user:
                # 获取用户最小角色层级
                roles = await user.roles.all()
                min_level = min([role.user_level for role in roles], default=99)
                
                # 如果是代理或管理员（层级 < 99），返回代理公告
                if min_level < 99:
                    announcement_type = AnnouncementType.AGENT
                    
        logger.info(f"用户 {user_id} 获取公告，类型: {announcement_type.value}")
    except Exception as e:
        # JWT解析失败或其他错误，使用默认的前台公告
        logger.debug(f"获取用户信息失败: {e}")
    
    try:
        # 查询当前有效的公告
        announcements = await announcement_controller.get_active_announcements(announcement_type)
        
        # 转换为响应格式
        announcement_list = []
        for announcement in announcements:
            announcement_dict = await announcement.to_dict(exclude_fields=["created_by_id"])
            announcement_list.append(announcement_dict)
        
        return Success(data=announcement_list)
    except Exception as e:
        logger.error(f"获取公告失败: {e}")
        return Fail(code=500, msg=f"获取公告失败: {str(e)}")


@router.get("/list", summary="获取公告列表", dependencies=[DependAuth])
async def list_announcements(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    announcement_type: Optional[AnnouncementType] = Query(None, description="公告类型"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    title: str = Query("", description="标题搜索")
):
    """获取公告列表（管理员使用）"""
    try:
        current_user_id = CTX_USER_ID.get()
        
        # 检查用户权限（只有管理员可以访问）
        user = await User.filter(id=current_user_id).first()
        if not user or not user.is_superuser:
            # 检查是否为管理员角色
            roles = await user.roles.all()
            is_admin = any(role.name in ["管理员", "系统管理员"] for role in roles)
            if not is_admin:
                return Fail(code=403, msg="权限不足，只有管理员可以管理公告")

        # 构建查询条件
        q = Q()
        if title:
            q &= Q(title__contains=title)
        if announcement_type:
            q &= Q(announcement_type=announcement_type)
        if is_active is not None:
            q &= Q(is_active=is_active)

        total, announcements = await announcement_controller.list(
            page=page, 
            page_size=page_size, 
            search=q
        )

        # 转换为响应格式
        announcement_list = []
        for announcement in announcements:
            announcement_dict = await announcement.to_dict(m2m=True, exclude_fields=["created_by_id"])
            # 添加创建者信息
            try:
                created_by = await announcement.created_by
                announcement_dict['created_by_name'] = created_by.username if created_by else "未知"
            except:
                announcement_dict['created_by_name'] = "未知"
            announcement_list.append(announcement_dict)

        return SuccessExtra(data=announcement_list, total=total, page=page, page_size=page_size)
    
    except Exception as e:
        logger.error(f"获取公告列表失败: {e}")
        return Fail(code=500, msg=f"获取公告列表失败: {str(e)}")


@router.post("/create", summary="创建公告", dependencies=[DependAuth])
async def create_announcement(announcement_in: AnnouncementCreate):
    """创建公告（管理员使用）"""
    try:
        current_user_id = CTX_USER_ID.get()
        
        # 检查用户权限（只有管理员可以创建）
        user = await User.filter(id=current_user_id).first()
        if not user or not user.is_superuser:
            # 检查是否为管理员角色
            roles = await user.roles.all()
            is_admin = any(role.name in ["管理员", "系统管理员"] for role in roles)
            if not is_admin:
                return Fail(code=403, msg="权限不足，只有管理员可以创建公告")

        # 创建公告
        announcement = await announcement_controller.create_announcement(
            obj_in=announcement_in,
            created_by=current_user_id
        )
        
        logger.info(f"用户 {current_user_id} 创建公告: {announcement.title}")
        return Success(msg="公告创建成功")
        
    except Exception as e:
        logger.error(f"创建公告失败: {e}")
        return Fail(code=500, msg=f"创建公告失败: {str(e)}")


@router.put("/update", summary="更新公告", dependencies=[DependAuth])
async def update_announcement(announcement_in: AnnouncementUpdate):
    """更新公告（管理员使用）"""
    try:
        current_user_id = CTX_USER_ID.get()
        
        # 检查用户权限（只有管理员可以更新）
        user = await User.filter(id=current_user_id).first()
        if not user or not user.is_superuser:
            # 检查是否为管理员角色
            roles = await user.roles.all()
            is_admin = any(role.name in ["管理员", "系统管理员"] for role in roles)
            if not is_admin:
                return Fail(code=403, msg="权限不足，只有管理员可以更新公告")

        # 更新公告
        announcement = await announcement_controller.update_announcement(
            announcement_id=announcement_in.id,
            obj_in=announcement_in
        )
        
        logger.info(f"用户 {current_user_id} 更新公告: {announcement.title}")
        return Success(msg="公告更新成功")
        
    except Exception as e:
        logger.error(f"更新公告失败: {e}")
        return Fail(code=500, msg=f"更新公告失败: {str(e)}")


@router.post("/toggle_status", summary="切换公告状态", dependencies=[DependAuth])
async def toggle_announcement_status(announcement_id: int = Body(..., embed=True)):
    """切换公告启用状态（管理员使用）"""
    try:
        current_user_id = CTX_USER_ID.get()
        
        # 检查用户权限（只有管理员可以操作）
        user = await User.filter(id=current_user_id).first()
        if not user or not user.is_superuser:
            # 检查是否为管理员角色
            roles = await user.roles.all()
            is_admin = any(role.name in ["管理员", "系统管理员"] for role in roles)
            if not is_admin:
                return Fail(code=403, msg="权限不足，只有管理员可以操作公告")

        # 切换状态
        announcement = await announcement_controller.toggle_announcement_status(announcement_id)
        
        status_text = "启用" if announcement.is_active else "禁用"
        logger.info(f"用户 {current_user_id} {status_text}公告: {announcement.title}")
        return Success(msg=f"公告已{status_text}")
        
    except Exception as e:
        logger.error(f"切换公告状态失败: {e}")
        return Fail(code=500, msg=f"切换公告状态失败: {str(e)}")


@router.delete("/delete", summary="删除公告", dependencies=[DependAuth])
async def delete_announcement(announcement_id: int = Query(..., description="公告ID")):
    """删除公告（管理员使用）"""
    try:
        current_user_id = CTX_USER_ID.get()
        
        # 检查用户权限（只有管理员可以删除）
        user = await User.filter(id=current_user_id).first()
        if not user or not user.is_superuser:
            # 检查是否为管理员角色
            roles = await user.roles.all()
            is_admin = any(role.name in ["管理员", "系统管理员"] for role in roles)
            if not is_admin:
                return Fail(code=403, msg="权限不足，只有管理员可以删除公告")

        # 删除公告
        success = await announcement_controller.delete_announcement(announcement_id)
        
        if success:
            logger.info(f"用户 {current_user_id} 删除公告 ID: {announcement_id}")
            return Success(msg="公告删除成功")
        else:
            return Fail(code=500, msg="删除公告失败")
        
    except Exception as e:
        logger.error(f"删除公告失败: {e}")
        return Fail(code=500, msg=f"删除公告失败: {str(e)}")


@router.get("/get", summary="获取单个公告详情", dependencies=[DependAuth])
async def get_announcement(announcement_id: int = Query(..., description="公告ID")):
    """获取单个公告详情（管理员使用）"""
    try:
        current_user_id = CTX_USER_ID.get()
        
        # 检查用户权限（只有管理员可以查看详情）
        user = await User.filter(id=current_user_id).first()
        if not user or not user.is_superuser:
            # 检查是否为管理员角色
            roles = await user.roles.all()
            is_admin = any(role.name in ["管理员", "系统管理员"] for role in roles)
            if not is_admin:
                return Fail(code=403, msg="权限不足，只有管理员可以查看公告详情")

        # 获取公告
        announcement = await announcement_controller.get(id=announcement_id)
        if not announcement:
            return Fail(code=404, msg="公告不存在")

        # 转换为响应格式
        announcement_dict = await announcement.to_dict(exclude_fields=["created_by_id"])
        try:
            created_by = await announcement.created_by
            announcement_dict['created_by_name'] = created_by.username if created_by else "未知"
        except:
            announcement_dict['created_by_name'] = "未知"
        
        return Success(data=announcement_dict)
        
    except Exception as e:
        logger.error(f"获取公告详情失败: {e}")
        return Fail(code=500, msg=f"获取公告详情失败: {str(e)}")
