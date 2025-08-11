from datetime import datetime
from typing import List, Optional

from tortoise.expressions import Q
from fastapi.exceptions import HTTPException

from app.core.crud import CRUDBase
from app.models.announcement import Announcement
from app.models.enums import AnnouncementType
from app.schemas.announcement import AnnouncementCreate, AnnouncementUpdate


class AnnouncementController(CRUDBase[Announcement, AnnouncementCreate, AnnouncementUpdate]):
    def __init__(self):
        super().__init__(model=Announcement)

    async def create_announcement(self, obj_in: AnnouncementCreate, created_by: int) -> Announcement:
        """创建公告"""
        # 验证时间逻辑
        if obj_in.end_date <= obj_in.start_date:
            raise HTTPException(status_code=400, detail="结束时间必须大于开始时间")

        # 创建公告数据
        announcement_data = obj_in.create_dict()
        announcement_data["created_by_id"] = created_by

        return await self.create(obj_in=announcement_data)

    async def update_announcement(self, announcement_id: int, obj_in: AnnouncementUpdate) -> Announcement:
        """更新公告"""
        # 检查公告是否存在
        announcement = await self.get(id=announcement_id)
        if not announcement:
            raise HTTPException(status_code=404, detail="公告不存在")

        # 验证时间逻辑
        update_data = obj_in.update_dict()
        if "start_date" in update_data or "end_date" in update_data:
            start_date = update_data.get("start_date", announcement.start_date)
            end_date = update_data.get("end_date", announcement.end_date)
            
            if end_date <= start_date:
                raise HTTPException(status_code=400, detail="结束时间必须大于开始时间")

        return await self.update(id=announcement_id, obj_in=update_data)

    async def get_active_announcements(self, announcement_type: AnnouncementType) -> List[Announcement]:
        """获取当前有效的公告"""
        current_time = datetime.now()
        
        announcements = await self.model.filter(
            announcement_type=announcement_type,
            is_active=True,
            start_date__lte=current_time,
            end_date__gte=current_time
        ).order_by("-priority", "-created_at")
        
        return announcements

    async def get_announcements_by_type(
        self, 
        announcement_type: Optional[AnnouncementType] = None,
        is_active: Optional[bool] = None,
        page: int = 1,
        page_size: int = 10
    ) -> tuple[int, List[Announcement]]:
        """根据条件获取公告列表"""
        q = Q()
        
        if announcement_type:
            q &= Q(announcement_type=announcement_type)
        
        if is_active is not None:
            q &= Q(is_active=is_active)

        return await self.list(page=page, page_size=page_size, search=q)

    async def toggle_announcement_status(self, announcement_id: int) -> Announcement:
        """切换公告启用状态"""
        announcement = await self.get(id=announcement_id)
        if not announcement:
            raise HTTPException(status_code=404, detail="公告不存在")

        announcement.is_active = not announcement.is_active
        await announcement.save()
        return announcement

    async def delete_announcement(self, announcement_id: int) -> bool:
        """删除公告"""
        announcement = await self.get(id=announcement_id)
        if not announcement:
            raise HTTPException(status_code=404, detail="公告不存在")

        await self.remove(id=announcement_id)
        return True


# 创建全局实例
announcement_controller = AnnouncementController()
