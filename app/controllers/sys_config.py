from typing import Optional, Dict, Any

from app.core.crud import CRUDBase
from app.models.sys_config import SysConfig
from app.schemas.sys_config import SysConfigCreate, SysConfigUpdate


class SysConfigController(CRUDBase[SysConfig, SysConfigCreate, SysConfigUpdate]):
    def __init__(self):
        super().__init__(model=SysConfig)

    async def get_by_key(self, config_key: str) -> Optional[SysConfig]:
        """根据配置key获取配置"""
        return await self.model.filter(config_key=config_key, is_enabled=True).first()

    async def get_value_by_key(self, config_key: str, default_value: str = "") -> str:
        """根据配置key获取配置值"""
        config = await self.get_by_key(config_key)
        return config.config_value if config else default_value

    async def set_config(self, config_key: str, config_value: str, config_name: str, created_by: int) -> SysConfig:
        """设置配置项（如果存在则更新，不存在则创建）"""
        existing_config = await self.model.filter(config_key=config_key).first()
        
        if existing_config:
            # 更新现有配置
            existing_config.config_value = config_value
            existing_config.config_name = config_name
            existing_config.is_enabled = True
            await existing_config.save()
            return existing_config
        else:
            # 创建新配置
            return await self.model.create(
                config_key=config_key,
                config_value=config_value,
                config_name=config_name,
                created_by_id=created_by,
                is_enabled=True
            )

    async def get_frontend_configs(self) -> Dict[str, Any]:
        """获取前台配置"""
        configs = await self.model.filter(
            config_key__in=["site_name", "recharge_rate", "maintenance_mode"],
            is_enabled=True
        ).all()
        
        result = {
            "site_name": "",
            "recharge_rate": "1.0",
            "maintenance_mode": False
        }
        
        for config in configs:
            if config.config_key == "maintenance_mode":
                result[config.config_key] = config.config_value.lower() == "true"
            else:
                result[config.config_key] = config.config_value
        
        return result

    async def update_frontend_configs(self, configs: Dict[str, Any], created_by: int) -> bool:
        """批量更新前台配置"""
        config_mappings = {
            "site_name": "网站名称",
            "recharge_rate": "积分充值单价",
            "maintenance_mode": "维护模式"
        }
        
        try:
            for key, value in configs.items():
                if key in config_mappings and value is not None:
                    # 转换布尔值为字符串
                    str_value = str(value).lower() if isinstance(value, bool) else str(value)
                    await self.set_config(
                        config_key=key,
                        config_value=str_value,
                        config_name=config_mappings[key],
                        created_by=created_by
                    )
            return True
        except Exception:
            return False


sys_config_controller = SysConfigController()
