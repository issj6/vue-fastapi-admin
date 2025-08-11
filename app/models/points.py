from tortoise import fields
from tortoise.models import Model


class PointsRechargeRecord(Model):
    """积分充值记录表"""
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="recharge_records", description="用户")
    amount = fields.DecimalField(max_digits=10, decimal_places=2, description="充值金额(元)")
    points = fields.IntField(description="获得积分数量")
    payment_method = fields.CharField(max_length=20, description="支付方式", null=True)  # alipay, wechat, exchange_code
    exchange_code = fields.CharField(max_length=50, description="兑换码", null=True)
    status = fields.CharField(max_length=20, default="completed", description="状态")  # pending, completed, failed
    transaction_id = fields.CharField(max_length=100, description="交易ID", null=True)
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    remark = fields.TextField(description="备注", null=True)

    class Meta:
        table = "points_recharge_record"
        table_description = "积分充值记录表"


class PointsUsageRecord(Model):
    """积分使用记录表"""
    id = fields.IntField(pk=True)
    user = fields.ForeignKeyField("models.User", related_name="usage_records", description="用户")
    points = fields.IntField(description="消耗积分数量")
    usage_type = fields.CharField(max_length=50, description="使用类型")  # api_call, service_fee, etc.
    description = fields.CharField(max_length=200, description="使用描述")
    related_id = fields.IntField(description="关联ID", null=True)  # 关联的业务ID
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    remark = fields.TextField(description="备注", null=True)

    class Meta:
        table = "points_usage_record"
        table_description = "积分使用记录表"


class ExchangeCode(Model):
    """兑换码表"""
    id = fields.IntField(pk=True)
    code = fields.CharField(max_length=50, unique=True, description="兑换码")
    points = fields.IntField(description="积分数量")
    is_used = fields.BooleanField(default=False, description="是否已使用")
    used_by = fields.ForeignKeyField("models.User", related_name="used_codes", description="使用者", null=True)
    used_at = fields.DatetimeField(description="使用时间", null=True)
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    expires_at = fields.DatetimeField(description="过期时间", null=True)
    created_by = fields.ForeignKeyField("models.User", related_name="created_codes", description="创建者", null=True)
    remark = fields.TextField(description="备注", null=True)

    class Meta:
        table = "exchange_code"
        table_description = "兑换码表"
