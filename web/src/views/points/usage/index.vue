<template>
  <AppPage>
    <div class="points-usage">
    <!-- 页面标题和统计 -->
    <n-card :bordered="false" class="header-card">
      <div class="header-content">
        <div class="title-section">
          <h2>积分使用记录</h2>
          <p class="subtitle">查看您的积分消耗历史</p>
        </div>
        <div class="stats-section">
          <n-statistic label="累计消耗积分" :value="totalUsedPoints">
            <template #suffix>积分</template>
          </n-statistic>
        </div>
      </div>
    </n-card>

    <!-- 筛选条件 -->
    <n-card :bordered="false" class="filter-card">
      <n-form inline :label-width="80">
        <n-form-item label="使用类型">
          <n-select
            v-model:value="filterType"
            placeholder="选择使用类型"
            :options="usageTypeOptions"
            clearable
            style="width: 200px"
          />
        </n-form-item>
        <n-form-item label="时间范围">
          <n-date-picker
            v-model:value="dateRange"
            type="daterange"
            clearable
            style="width: 300px"
          />
        </n-form-item>
        <n-form-item>
          <n-button type="primary" @click="handleSearch">
            <template #icon>
              <component :is="renderIcon('material-symbols:search')" />
            </template>
            搜索
          </n-button>
          <n-button @click="handleReset" style="margin-left: 8px">
            重置
          </n-button>
        </n-form-item>
      </n-form>
    </n-card>

    <!-- 使用记录表格 -->
    <n-card :bordered="false" class="table-card">
      <n-data-table
        ref="tableRef"
        :columns="columns"
        :data="tableData"
        :loading="loading"
        :pagination="pagination"
        :row-key="(row) => row.id"
        @update:page="handlePageChange"
        @update:page-size="handlePageSizeChange"
      />
    </n-card>
    </div>
  </AppPage>
</template>

<script setup>
import { ref, reactive, onMounted, computed, h } from 'vue'
import { useMessage } from 'naive-ui'
import { renderIcon } from '@/utils'
import api from '@/api'
import AppPage from '@/components/page/AppPage.vue'

const $message = useMessage()

// 响应式数据
const tableData = ref([])
const loading = ref(false)
const filterType = ref(null)
const dateRange = ref(null)

// 分页配置
const pagination = reactive({
  page: 1,
  pageSize: 20,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100],
  showQuickJumper: true,
  total: 0
})

// 使用类型选项
const usageTypeOptions = [
  { label: 'API调用', value: 'api_call' },
  { label: '服务费用', value: 'service_fee' },
  { label: '系统扣费', value: 'system_deduction' },
  { label: '其他', value: 'other' }
]

// 计算总消耗积分
const totalUsedPoints = computed(() => {
  return tableData.value.reduce((total, record) => total + record.points, 0)
})

// 表格列配置
const columns = [
  {
    title: '使用时间',
    key: 'created_at',
    width: 180,
    render: (row) => new Date(row.created_at).toLocaleString()
  },
  {
    title: '消耗积分',
    key: 'points',
    width: 120,
    render: (row) => {
      return h('span', {
        style: { color: '#f56565', fontWeight: 'bold' }
      }, `-${row.points}`)
    }
  },
  {
    title: '使用类型',
    key: 'usage_type',
    width: 120,
    render: (row) => {
      const typeMap = {
        'api_call': 'API调用',
        'service_fee': '服务费用',
        'system_deduction': '系统扣费',
        'other': '其他'
      }
      return typeMap[row.usage_type] || row.usage_type
    }
  },
  {
    title: '使用描述',
    key: 'description',
    ellipsis: {
      tooltip: true
    }
  },
  {
    title: '关联ID',
    key: 'related_id',
    width: 100,
    render: (row) => row.related_id || '-'
  },
  {
    title: '备注',
    key: 'remark',
    width: 150,
    ellipsis: {
      tooltip: true
    },
    render: (row) => row.remark || '-'
  }
]

// 方法
const loadUsageRecords = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      size: pagination.pageSize
    }

    // 添加筛选条件
    if (filterType.value) {
      params.usage_type = filterType.value
    }
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = new Date(dateRange.value[0]).toISOString().split('T')[0]
      params.end_date = new Date(dateRange.value[1]).toISOString().split('T')[0]
    }

    const response = await api.getPointsUsageRecords(params)
    if (response.code === 200) {
      tableData.value = response.data.records
      pagination.total = response.data.total
    } else {
      $message.error(response.msg || '获取使用记录失败')
    }
  } catch (error) {
    console.error('获取使用记录失败:', error)
    $message.error('获取使用记录失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadUsageRecords()
}

const handleReset = () => {
  filterType.value = null
  dateRange.value = null
  pagination.page = 1
  loadUsageRecords()
}

const handlePageChange = (page) => {
  pagination.page = page
  loadUsageRecords()
}

const handlePageSizeChange = (pageSize) => {
  pagination.pageSize = pageSize
  pagination.page = 1
  loadUsageRecords()
}

// 生命周期
onMounted(() => {
  loadUsageRecords()
})
</script>

<style scoped>
.points-usage {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.header-card {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-section h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: bold;
}

.subtitle {
  margin: 0;
  opacity: 0.9;
  font-size: 14px;
}

.stats-section {
  text-align: right;
}

.filter-card {
  margin: 16px 0;
}

.table-card {
  flex: 1;
}

:deep(.n-statistic .n-statistic-value) {
  color: white !important;
}

:deep(.n-statistic .n-statistic-label) {
  color: rgba(255, 255, 255, 0.8) !important;
}
</style>
