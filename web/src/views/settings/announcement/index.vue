<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import {
  NButton,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NSelect,
  NSwitch,
  NTag,
  NPopconfirm,
  NDatePicker,
  NSpace,
  NDropdown,
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import QueryBarItem from '@/components/query-bar/QueryBarItem.vue'
import CrudModal from '@/components/table/CrudModal.vue'
import CrudTable from '@/components/table/CrudTable.vue'

import { formatDate, renderIcon } from '@/utils'
import { useCRUD } from '@/composables'
import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'
import { useUserStore } from '@/store'

defineOptions({ name: '公告设置' })

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')
const $dialog = window.$dialog

// 设置默认时间
const now = new Date()
const defaultEndDate = new Date(now)
defaultEndDate.setDate(defaultEndDate.getDate() + 30) // 默认30天后结束

const {
  modalVisible,
  modalTitle,
  modalAction,
  modalLoading,
  handleSave: originalHandleSave,
  modalForm,
  modalFormRef,
  handleEdit: originalHandleEdit,
  handleDelete,
  handleAdd: originalHandleAdd,
} = useCRUD({
  name: '公告',
  initForm: {
    title: '',
    content: '',
    announcement_type: 'agent',
    is_active: true,
    priority: 0,
    start_date: now.getTime(),
    end_date: defaultEndDate.getTime(),
  },
  doCreate: api.createAnnouncement,
  doUpdate: api.updateAnnouncement,
  doDelete: api.deleteAnnouncement,
  refresh: () => $table.value?.handleSearch(),
})

// 使用原始的handleSave，因为时间戳会自动转换
const handleSave = originalHandleSave

const userStore = useUserStore()

// 公告类型选项
const announcementTypeOptions = [
  { label: '前台公告', value: 'frontend' },
  { label: '代理公告', value: 'agent' },
]

// 状态选项
const statusOptions = [
  { label: '全部', value: null },
  { label: '启用', value: true },
  { label: '禁用', value: false },
]

const columns = [
  {
    title: '标题',
    key: 'title',
    width: 200,
    ellipsis: { tooltip: true },
  },
  {
    title: '内容',
    key: 'content',
    width: 300,
    ellipsis: { tooltip: true },
    render: (row) => {
      // 去除HTML标签并限制长度
      const text = row.content.replace(/<[^>]*>/g, '')
      return text.length > 50 ? text.substring(0, 50) + '...' : text
    },
  },
  {
    title: '类型',
    key: 'announcement_type',
    width: 100,
    render: (row) => {
      const typeMap = {
        frontend: { label: '前台公告', type: 'default' },
        agent: { label: '代理公告', type: 'info' },
      }
      const config = typeMap[row.announcement_type] || { label: '未知', type: 'default' }
      return h(NTag, { type: config.type, size: 'small' }, { default: () => config.label })
    },
  },
  {
    title: '状态',
    key: 'is_active',
    width: 80,
    render: (row) => {
      return h(NTag, 
        { type: row.is_active ? 'success' : 'error', size: 'small' }, 
        { default: () => row.is_active ? '启用' : '禁用' }
      )
    },
  },
  {
    title: '优先级',
    key: 'priority',
    width: 80,
  },
  {
    title: '开始时间',
    key: 'start_date',
    width: 160,
    render: (row) => formatDate(row.start_date),
  },
  {
    title: '结束时间',
    key: 'end_date',
    width: 160,
    render: (row) => formatDate(row.end_date),
  },
  {
    title: '创建者',
    key: 'created_by_name',
    width: 100,
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 160,
    render: (row) => formatDate(row.created_at),
  },
  {
    title: '操作',
    key: 'actions',
    width: 80,
    align: 'center',
    fixed: 'right',
    hideInExcel: true,
    render: (row) => {
      // 构建下拉菜单选项
      const dropdownOptions = [
        {
          label: '查看',
          key: 'view',
          icon: renderIcon('material-symbols:visibility', { size: 16 }),
        },
        {
          label: '编辑',
          key: 'edit',
          icon: renderIcon('material-symbols:edit-outline', { size: 16 }),
        },
        {
          label: row.is_active ? '禁用' : '启用',
          key: 'toggle',
          icon: renderIcon(row.is_active ? 'material-symbols:block' : 'material-symbols:check-circle-outline', { size: 16 }),
        },
        {
          label: '删除',
          key: 'delete',
          icon: renderIcon('material-symbols:delete-outline', { size: 16 }),
        },
      ]

      // 处理下拉菜单选择
      const handleDropdownSelect = (key) => {
        switch (key) {
          case 'view':
            handleView(row)
            break
          case 'edit':
            handleEdit(row)
            break
          case 'toggle':
            handleToggleStatus(row)
            break
          case 'delete':
            $dialog.warning({
              title: '确认删除',
              content: `确定删除公告 "${row.title}" 吗？`,
              positiveText: '确定',
              negativeText: '取消',
              onPositiveClick: () => handleDelete({ announcement_id: row.id })
            })
            break
        }
      }

      return h(
        NDropdown,
        {
          trigger: 'hover',
          options: dropdownOptions,
          onSelect: handleDropdownSelect
        },
        {
          default: () => h(
            NButton,
            {
              size: 'small',
              type: 'primary',
              quaternary: true,
            },
            {
              default: () => '操作',
              icon: renderIcon('material-symbols:more-vert', { size: 16 }),
            }
          )
        }
      )
    },
  },
]

async function handleSearch() {
  $table.value?.handleSearch()
}

// 使用原始的handleAdd，因为initForm已经设置了默认时间
const handleAdd = originalHandleAdd

// 编辑公告
function handleEdit(row) {
  // 转换日期格式为时间戳
  const convertToTimestamp = (dateStr) => {
    if (!dateStr) return null
    return new Date(dateStr).getTime()
  }
  
  modalForm.value = {
    ...row,
    start_date: convertToTimestamp(row.start_date),
    end_date: convertToTimestamp(row.end_date),
  }
  modalAction.value = 'edit'
  modalTitle.value = '编辑公告'
  modalVisible.value = true
}

// 查看公告详情
function handleView(row) {
  // 转换日期格式为时间戳以便在DatePicker中显示
  const convertToTimestamp = (dateStr) => {
    if (!dateStr) return null
    return new Date(dateStr).getTime()
  }
  
  modalForm.value = {
    ...row,
    start_date: convertToTimestamp(row.start_date),
    end_date: convertToTimestamp(row.end_date),
  }
  modalAction.value = 'view'
  modalTitle.value = '查看公告'
  modalVisible.value = true
}

// 切换公告状态
async function handleToggleStatus(row) {
  try {
    const result = await api.toggleAnnouncementStatus({ announcement_id: row.id })
    if (result.code === 200) {
      window.$message?.success(result.msg || '操作成功')
      handleSearch()
    } else {
      window.$message?.error(result.msg || '操作失败')
    }
  } catch (error) {
    window.$message?.error('操作失败')
    console.error('切换公告状态失败:', error)
  }
}

// 表单验证规则
const rules = {
  title: [
    { required: false },
    { max: 200, message: '标题长度不能超过200个字符', trigger: 'blur' },
  ],
  content: [
    { required: true, message: '请输入公告内容', trigger: 'blur' },
  ],
  announcement_type: [
    { required: true, message: '请选择公告类型', trigger: 'change' },
  ],
  start_date: [
    { 
      required: true, 
      message: '请选择开始时间', 
      trigger: ['change', 'blur'],
      validator: (rule, value) => {
        if (!value && value !== 0) {
          return new Error('请选择开始时间')
        }
        return true
      }
    },
  ],
  end_date: [
    { 
      required: true, 
      message: '请选择结束时间', 
      trigger: ['change', 'blur'],
      validator: (rule, value) => {
        if (!value && value !== 0) {
          return new Error('请选择结束时间')
        }
        return true
      }
    },
  ],
}

onMounted(() => {
  handleSearch()
})
</script>

<template>
  <CommonPage show-footer title="公告设置">
    <template #action>
      <div>
        <NButton
          v-permission="'post/api/v1/announcement/create'"
          type="primary"
          secondary
          @click="handleAdd"
        >
          <TheIcon icon="material-symbols:add" :size="18" class="mr-1" />
          添加公告
        </NButton>
      </div>
    </template>

    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :extra-params="{ }"
      :scroll-x="1450"
      :columns="columns"
      :get-data="api.getAnnouncementList"
    >
      <template #queryBar>
        <QueryBarItem label="标题" :label-width="50">
          <NInput
            v-model:value="queryItems.title"
            type="text"
            placeholder="请输入标题搜索"
            clearable
            @keydown.enter="handleSearch"
          />
        </QueryBarItem>
        <QueryBarItem label="类型" :label-width="50">
          <NSelect
            v-model:value="queryItems.announcement_type"
            :options="[{ label: '全部', value: null }, ...announcementTypeOptions]"
            placeholder="请选择公告类型"
            clearable
          />
        </QueryBarItem>
        <QueryBarItem label="状态" :label-width="50">
          <NSelect
            v-model:value="queryItems.is_active"
            :options="statusOptions"
            placeholder="请选择状态"
            clearable
          />
        </QueryBarItem>
      </template>
    </CrudTable>

    <!-- 添加/编辑公告弹窗 -->
    <CrudModal
      v-model:visible="modalVisible"
      :title="modalTitle"
      :loading="modalLoading"
      :show-footer="modalAction !== 'view'"
      @on-save="handleSave"
    >
      <NForm
        ref="modalFormRef"
        label-placement="left"
        label-align="left"
        :label-width="120"
        :model="modalForm"
        :rules="rules"
        :disabled="modalAction === 'view'"
      >
        <NFormItem label="公告标题" path="title">
          <NInput
            v-model:value="modalForm.title"
            placeholder="请输入公告标题"
            maxlength="200"
            show-count
          />
        </NFormItem>
        <NFormItem label="公告内容" path="content">
          <NInput
            v-model:value="modalForm.content"
            type="textarea"
            placeholder="请输入公告内容，支持HTML格式"
            :rows="5"
            maxlength="5000"
            show-count
          />
        </NFormItem>
        <NFormItem label="公告类型" path="announcement_type">
          <NSelect
            v-model:value="modalForm.announcement_type"
            :options="announcementTypeOptions"
            placeholder="请选择公告类型"
          />
        </NFormItem>
        <NFormItem label="优先级" path="priority">
          <NInputNumber
            v-model:value="modalForm.priority"
            placeholder="数字越大优先级越高"
            :min="0"
            :max="999"
          />
        </NFormItem>
        <NFormItem label="开始时间" path="start_date">
          <NDatePicker
            v-model:value="modalForm.start_date"
            type="datetime"
            placeholder="请选择开始时间"
            style="width: 100%"
          />
        </NFormItem>
        <NFormItem label="结束时间" path="end_date">
          <NDatePicker
            v-model:value="modalForm.end_date"
            type="datetime"
            placeholder="请选择结束时间"
            style="width: 100%"
          />
        </NFormItem>
        <NFormItem label="是否启用" path="is_active">
          <NSwitch v-model:value="modalForm.is_active" />
        </NFormItem>
      </NForm>
    </CrudModal>
  </CommonPage>
</template>

<style scoped>
:deep(.n-data-table .n-data-table-td) {
  white-space: nowrap;
}

:deep(.announcement-content) {
  max-height: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 确保表格容器能够显示横向滚动条 */
:deep(.n-data-table) {
  overflow-x: auto;
}

:deep(.n-data-table-wrapper) {
  overflow-x: auto;
}
</style>
