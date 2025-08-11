<template>
  <AppPage>
    <div class="points-info">
    <!-- 积分余额卡片 -->
    <n-card class="balance-card" :bordered="false">
      <div class="balance-content">
        <div class="balance-info">
          <h2 class="balance-title">当前积分余额</h2>
          <div class="balance-amount">{{ pointsInfo?.stats?.current_balance || 0 }}</div>
          <div class="balance-subtitle">积分</div>
        </div>
        <div class="balance-icon">
          <component :is="renderIcon('mdi:wallet', { size: 80, color: '#18a058' })" />
        </div>
      </div>
    </n-card>

    <!-- 功能操作区 -->
    <n-grid :cols="2" :x-gap="16" class="action-grid">
      <!-- 兑换码兑换 -->
      <n-gi>
        <n-card title="兑换码兑换" :bordered="false">
          <div class="exchange-section">
            <n-input
              v-model:value="exchangeCode"
              placeholder="请输入兑换码"
              :maxlength="50"
              clearable
            />
            <n-button
              type="primary"
              :loading="exchangeLoading"
              @click="handleExchange"
              class="exchange-btn"
            >
              立即兑换
            </n-button>
          </div>
        </n-card>
      </n-gi>

      <!-- 积分充值 -->
      <n-gi>
        <n-card title="积分充值" :bordered="false">
          <div class="recharge-section">
            <div class="recharge-info">
              <p class="exchange-rate" style="">兑换比例：1元 = 1积分</p>
              <p class="min-amount">最低充值：100元</p>
            </div>
            <n-input-number
              v-model:value="rechargeAmount"
              :min="100"
              :step="100"
              placeholder="充值金额"
              class="amount-input"
            >
              <template #suffix>元</template>
            </n-input-number>
            <div class="payment-methods">
              <n-radio-group v-model:value="paymentMethod">
                <n-radio value="alipay">
                  <div class="payment-option">
                    <component :is="renderIcon('ant-design:alipay-circle-filled', { size: 20, color: '#1677ff' })" />
                    支付宝
                  </div>
                </n-radio>
                <n-radio value="wechat">
                  <div class="payment-option">
                    <component :is="renderIcon('ri:wechat-pay-fill', { size: 20, color: '#07c160' })" />
                    微信支付
                  </div>
                </n-radio>
              </n-radio-group>
            </div>
            <n-button
              type="primary"
              :loading="rechargeLoading"
              :disabled="!canRecharge"
              @click="handleRecharge"
              class="recharge-btn"
            >
              立即充值
            </n-button>
          </div>
        </n-card>
      </n-gi>
    </n-grid>

    <!-- 统计信息 -->
    <n-card title="积分统计" :bordered="false" class="stats-card">
      <n-grid :cols="4" :x-gap="16">
        <n-gi>
          <n-statistic label="历史充值总额" :value="pointsInfo?.stats?.total_recharged_amount || 0">
            <template #suffix>元</template>
          </n-statistic>
        </n-gi>
        <n-gi>
          <n-statistic label="历史充值积分" :value="pointsInfo?.stats?.total_recharged_points || 0">
            <template #suffix>积分</template>
          </n-statistic>
        </n-gi>
        <n-gi>
          <n-statistic label="历史消耗积分" :value="pointsInfo?.stats?.total_used_points || 0">
            <template #suffix>积分</template>
          </n-statistic>
        </n-gi>
        <n-gi>
          <n-statistic label="充值次数" :value="pointsInfo?.stats?.recharge_records_count || 0">
            <template #suffix">次</template>
          </n-statistic>
        </n-gi>
      </n-grid>
    </n-card>

    <!-- 充值记录 -->
    <n-card title="最近充值记录" :bordered="false" class="records-card">
      <n-data-table
        :columns="rechargeColumns"
        :data="pointsInfo?.recent_recharge_records || []"
        :pagination="false"
        :max-height="400"
      />
    </n-card>
    </div>
  </AppPage>
</template>

<script setup>
import { ref, computed, onMounted, h } from 'vue'
import { useMessage } from 'naive-ui'
import { renderIcon } from '@/utils'
import api from '@/api'
import AppPage from '@/components/page/AppPage.vue'

const $message = useMessage()

// 响应式数据
const pointsInfo = ref(null)
const exchangeCode = ref('')
const exchangeLoading = ref(false)
const rechargeAmount = ref(100)
const paymentMethod = ref('alipay')
const rechargeLoading = ref(false)

// 计算属性
const canRecharge = computed(() => {
  return rechargeAmount.value >= 100 && paymentMethod.value
})

// 充值记录表格列
const rechargeColumns = [
  {
    title: '充值时间',
    key: 'created_at',
    render: (row) => new Date(row.created_at).toLocaleString()
  },
  {
    title: '充值金额',
    key: 'amount',
    render: (row) => `¥${row.amount}`
  },
  {
    title: '获得积分',
    key: 'points',
    render: (row) => `${row.points}积分`
  },
  {
    title: '支付方式',
    key: 'payment_method',
    render: (row) => {
      const methods = {
        'alipay': '支付宝',
        'wechat': '微信支付',
        'exchange_code': '兑换码'
      }
      return methods[row.payment_method] || row.payment_method
    }
  },
  {
    title: '状态',
    key: 'status',
    render: (row) => {
      const statusMap = {
        'completed': '已完成',
        'pending': '处理中',
        'failed': '失败'
      }
      return statusMap[row.status] || row.status
    }
  }
]

// 方法
const loadPointsInfo = async () => {
  try {
    const response = await api.getPointsInfo()
    if (response.code === 200) {
      pointsInfo.value = response.data
    } else {
      $message.error(response.msg || '获取积分信息失败')
    }
  } catch (error) {
    console.error('获取积分信息失败:', error)
    $message.error('获取积分信息失败')
  }
}

const handleExchange = async () => {
  if (!exchangeCode.value.trim()) {
    $message.warning('请输入兑换码')
    return
  }

  exchangeLoading.value = true
  try {
    const response = await api.exchangePoints({ code: exchangeCode.value.trim() })
    if (response.code === 200) {
      $message.success(response.msg)
      exchangeCode.value = ''
      await loadPointsInfo() // 刷新积分信息
    } else {
      $message.error(response.msg || '兑换失败')
    }
  } catch (error) {
    console.error('兑换失败:', error)
    $message.error('兑换失败')
  } finally {
    exchangeLoading.value = false
  }
}

const handleRecharge = async () => {
  if (!canRecharge.value) {
    return
  }

  rechargeLoading.value = true
  try {
    const response = await api.rechargePoints({
      amount: rechargeAmount.value,
      payment_method: paymentMethod.value
    })
    if (response.code === 200) {
      $message.success(response.msg)
      await loadPointsInfo() // 刷新积分信息
    } else {
      $message.error(response.msg || '充值失败')
    }
  } catch (error) {
    console.error('充值失败:', error)
    $message.error('充值失败')
  } finally {
    rechargeLoading.value = false
  }
}

// 生命周期
onMounted(() => {
  loadPointsInfo()
})
</script>

<style scoped>
.points-info {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.balance-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.balance-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.balance-info {
  flex: 1;
}

.balance-title {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: normal;
  opacity: 0.9;
}

.balance-amount {
  font-size: 48px;
  font-weight: bold;
  margin: 8px 0;
}

.balance-subtitle {
  font-size: 16px;
  opacity: 0.8;
}

.balance-icon {
  opacity: 0.3;
}

.action-grid {
  margin: 16px 0;
}

.exchange-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.exchange-btn {
  width: 100%;
}

.recharge-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.recharge-info {
  font-size: 14px;
  color: #666;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.recharge-info p {
  margin: 0;
}

.exchange-rate {
  color: #18a058;
  font-weight: 500;
}

.min-amount {
  color: #f0a020;
}

.amount-input {
  width: 100%;
}

.payment-methods {
  margin: 8px 0;
}

.payment-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.recharge-btn {
  width: 100%;
}

.stats-card,
.records-card {
  margin-top: 16px;
}
</style>
