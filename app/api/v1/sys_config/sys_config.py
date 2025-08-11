from fastapi import APIRouter, Depends, Query
from typing import List

from app.controllers.sys_config import sys_config_controller
from app.models import User
from app.core.dependency import DependAuth, DependSuperUser
from app.schemas.base import Success, SuccessExtra
from app.schemas.sys_config import (
    SysConfigCreate, 
    SysConfigUpdate, 
    SysConfigResponse,
    FrontendConfigUpdate,
    FrontendConfigResponse
)

router = APIRouter()


@router.get("/list", summary="查看系统配置列表", dependencies=[DependSuperUser])
async def list_sys_config(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    config_key: str = Query(None, description="配置key"),
):
    """获取系统配置列表（仅超级管理员）"""
    filters = {}
    if config_key:
        filters["config_key__icontains"] = config_key
    
    total, sys_configs = await sys_config_controller.list(page=page, page_size=page_size, search=filters)
    return SuccessExtra(data=sys_configs, total=total, page=page, page_size=page_size)


@router.get("/get", summary="查看系统配置", dependencies=[DependSuperUser])
async def get_sys_config(
    config_id: int = Query(..., description="配置id"),
):
    """获取单个系统配置（仅超级管理员）"""
    result = await sys_config_controller.get(id=config_id)
    return Success(data=result)


@router.post("/create", summary="创建系统配置", dependencies=[DependSuperUser])
async def create_sys_config(
    sys_config_in: SysConfigCreate,
    current_user: User = DependSuperUser,
):
    """创建系统配置（仅超级管理员）"""
    sys_config_dict = sys_config_in.create_dict()
    sys_config_dict["created_by_id"] = current_user.id
    await sys_config_controller.create(obj_in=sys_config_dict)
    return Success(msg="创建成功")


@router.post("/update", summary="更新系统配置", dependencies=[DependSuperUser])
async def update_sys_config(
    sys_config_in: SysConfigUpdate,
):
    """更新系统配置（仅超级管理员）"""
    await sys_config_controller.update(id=sys_config_in.id, obj_in=sys_config_in.update_dict())
    return Success(msg="更新成功")


@router.delete("/delete", summary="删除系统配置", dependencies=[DependSuperUser])
async def delete_sys_config(
    config_id: int = Query(..., description="配置id"),
):
    """删除系统配置（仅超级管理员）"""
    await sys_config_controller.remove(id=config_id)
    return Success(msg="删除成功")


@router.get("/frontend", summary="获取前台配置")
async def get_frontend_config():
    """获取前台配置（公共接口）"""
    configs = await sys_config_controller.get_frontend_configs()
    return Success(data=configs)


@router.post("/frontend/update", summary="更新前台配置", dependencies=[DependSuperUser])
async def update_frontend_config(
    config_in: FrontendConfigUpdate,
    current_user: User = DependSuperUser,
):
    """更新前台配置（仅超级管理员）"""
    config_dict = config_in.model_dump(exclude_unset=True)
    success = await sys_config_controller.update_frontend_configs(config_dict, current_user.id)
    
    if success:
        return Success(msg="配置更新成功")
    else:
        return Success(code=500, msg="配置更新失败")
