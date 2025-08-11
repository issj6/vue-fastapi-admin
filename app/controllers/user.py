from datetime import datetime
from typing import List, Optional

from fastapi.exceptions import HTTPException

from app.core.crud import CRUDBase
from app.models.admin import User
from app.schemas.login import CredentialsSchema
from app.schemas.users import UserCreate, UserUpdate
from app.utils.password import get_password_hash, verify_password
from app.utils.invitation_code import (
    generate_unique_invitation_code,
    validate_invitation_code,
    check_circular_reference,
    get_subordinate_user_ids
)

from .role import role_controller


class UserController(CRUDBase[User, UserCreate, UserUpdate]):
    def __init__(self):
        super().__init__(model=User)

    async def get_by_email(self, email: str) -> Optional[User]:
        return await self.model.filter(email=email).first()

    async def get_by_username(self, username: str) -> Optional[User]:
        return await self.model.filter(username=username).first()

    async def create_user(self, obj_in: UserCreate) -> User:
        # 处理邀请码逻辑
        parent_user_id = -1
        if obj_in.invitation_code:
            inviter = await validate_invitation_code(obj_in.invitation_code)
            if inviter:
                parent_user_id = inviter.id
            else:
                raise HTTPException(status_code=400, detail="邀请码无效或已失效")

        # 生成唯一邀请码
        invitation_code = await generate_unique_invitation_code()

        # 创建用户数据
        user_data = obj_in.create_dict()
        user_data["password"] = get_password_hash(password=obj_in.password)
        user_data["parent_user_id"] = parent_user_id
        user_data["invitation_code"] = invitation_code
        user_data["school"] = obj_in.school or ""
        user_data["major"] = obj_in.major or ""

        obj = await self.model.create(**user_data)
        return obj

    async def update_last_login(self, id: int) -> None:
        user = await self.model.get(id=id)
        user.last_login = datetime.now()
        await user.save()

    async def authenticate(self, credentials: CredentialsSchema) -> Optional["User"]:
        """前台客户端登录验证（允许所有用户）"""
        user = await self.model.filter(username=credentials.username).first()
        if not user:
            raise HTTPException(status_code=400, detail="无效的用户名")
        verified = verify_password(credentials.password, user.password)
        if not verified:
            raise HTTPException(status_code=400, detail="密码错误!")
        if not user.is_active:
            raise HTTPException(status_code=400, detail="用户已被禁用")
        return user

    async def authenticate_admin(self, credentials: CredentialsSchema) -> Optional["User"]:
        """管理平台登录验证（禁止普通用户）"""
        user = await self.model.filter(username=credentials.username).first()
        if not user:
            raise HTTPException(status_code=400, detail="无效的用户名")
        verified = verify_password(credentials.password, user.password)
        if not verified:
            raise HTTPException(status_code=400, detail="密码错误!")
        if not user.is_active:
            raise HTTPException(status_code=400, detail="用户已被禁用")

        # 检查用户角色，禁止普通用户登录管理平台
        if not user.is_superuser:
            roles = await user.roles.all()
            if not roles:
                raise HTTPException(status_code=403, detail="普通用户无法登录管理平台")

            # 检查是否只有普通用户角色
            role_names = [role.name for role in roles]
            if "普通用户" in role_names and len(role_names) == 1:
                raise HTTPException(status_code=403, detail="普通用户无法登录管理平台")

        return user

    async def update_roles(self, user: User, role_ids: List[int]) -> None:
        await user.roles.clear()
        for role_id in role_ids:
            role_obj = await role_controller.get(id=role_id)
            await user.roles.add(role_obj)

    async def reset_password(self, user_id: int) -> str:
        """重置用户密码，返回新密码"""
        import random
        import string

        user_obj = await self.get(id=user_id)
        if user_obj.is_superuser:
            raise HTTPException(status_code=403, detail="不允许重置超级管理员密码")

        # 生成8位随机密码（包含大小写字母和数字）
        characters = string.ascii_letters + string.digits
        new_password = ''.join(random.choice(characters) for _ in range(8))

        user_obj.password = get_password_hash(password=new_password)
        await user_obj.save()

        return new_password

    async def get_subordinate_users(self, user_id: int) -> List[User]:
        """获取指定用户的下级用户列表"""
        subordinates = await self.model.filter(parent_user_id=user_id).all()
        return subordinates

    async def update_user_with_validation(self, user_id: int, obj_in: UserUpdate) -> User:
        """更新用户信息，包含上级用户关系验证"""
        user = await self.get(id=user_id)

        # 如果要修改上级用户关系，需要验证循环引用
        if hasattr(obj_in, 'parent_user_id') and obj_in.parent_user_id != user.parent_user_id:
            if obj_in.parent_user_id != -1:
                # 检查循环引用
                if await check_circular_reference(obj_in.parent_user_id, user_id):
                    raise HTTPException(status_code=400, detail="不能设置循环引用的上级用户关系")

                # 检查上级用户是否存在
                parent_user = await self.get(id=obj_in.parent_user_id)
                if not parent_user:
                    raise HTTPException(status_code=400, detail="指定的上级用户不存在")

        # 更新用户信息
        update_data = obj_in.model_dump(exclude_unset=True, exclude={"id", "role_ids"})
        for field, value in update_data.items():
            setattr(user, field, value)

        await user.save()
        return user

    async def add_points(self, user_id: int, points: int) -> User:
        """为用户增加积分"""
        user = await self.get(id=user_id)
        user.points_balance += points
        await user.save()
        return user

    async def deduct_points(self, user_id: int, points: int) -> User:
        """扣除用户积分"""
        user = await self.get(id=user_id)
        if user.points_balance < points:
            raise HTTPException(status_code=400, detail="积分余额不足")
        user.points_balance -= points
        await user.save()
        return user


user_controller = UserController()
