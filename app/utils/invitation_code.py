"""
邀请码生成和验证工具
"""
import random
import string
from typing import Optional

from app.models.admin import User


def generate_invitation_code() -> str:
    """
    生成6位大写字母数字混合邀请码
    
    Returns:
        str: 6位邀请码
    """
    # 使用大写字母和数字
    characters = string.ascii_uppercase + string.digits
    # 生成6位随机码
    code = ''.join(random.choices(characters, k=6))
    return code


async def generate_unique_invitation_code() -> str:
    """
    生成唯一的邀请码，确保不与现有邀请码重复
    
    Returns:
        str: 唯一的6位邀请码
    """
    max_attempts = 100  # 最大尝试次数，避免无限循环
    
    for _ in range(max_attempts):
        code = generate_invitation_code()
        # 检查邀请码是否已存在
        existing_user = await User.filter(invitation_code=code).first()
        if not existing_user:
            return code
    
    # 如果100次都没有生成唯一码，抛出异常
    raise ValueError("无法生成唯一邀请码，请稍后重试")


async def validate_invitation_code(invitation_code: str) -> Optional[User]:
    """
    验证邀请码是否有效
    
    Args:
        invitation_code: 邀请码
        
    Returns:
        User: 邀请人用户对象，如果邀请码无效则返回None
    """
    if not invitation_code or len(invitation_code) != 6:
        return None
    
    # 查找拥有该邀请码的用户
    inviter = await User.filter(
        invitation_code=invitation_code,
        is_active=True  # 只有激活的用户的邀请码才有效
    ).first()
    
    return inviter


async def get_subordinate_users(user_id: int) -> list[User]:
    """
    获取指定用户的所有下级用户
    
    Args:
        user_id: 用户ID
        
    Returns:
        list[User]: 下级用户列表
    """
    subordinates = await User.filter(parent_user_id=user_id).all()
    return subordinates


async def get_subordinate_user_ids(user_id: int) -> list[int]:
    """
    获取指定用户的所有下级用户ID列表
    
    Args:
        user_id: 用户ID
        
    Returns:
        list[int]: 下级用户ID列表
    """
    subordinates = await User.filter(parent_user_id=user_id).values_list('id', flat=True)
    return list(subordinates)


async def check_circular_reference(parent_id: int, child_id: int) -> bool:
    """
    检查是否会形成循环引用
    
    Args:
        parent_id: 父级用户ID
        child_id: 子级用户ID
        
    Returns:
        bool: True表示会形成循环引用，False表示不会
    """
    if parent_id == child_id:
        return True
    
    # 向上查找，检查parent_id是否是child_id的下级
    current_id = parent_id
    visited = set()
    
    while current_id != -1 and current_id not in visited:
        visited.add(current_id)
        user = await User.filter(id=current_id).first()
        if not user:
            break
        
        if user.parent_user_id == child_id:
            return True
        
        current_id = user.parent_user_id
    
    return False



