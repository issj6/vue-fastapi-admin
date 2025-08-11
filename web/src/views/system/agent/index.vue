<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import {
  NButton,
  NCheckbox,
  NCheckboxGroup,
  NForm,
  NFormItem,
  NImage,
  NInput,
  NSpace,
  NSwitch,
  NTag,
  NPopconfirm,
  NTable,
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
import { useUserStore, usePermissionStore } from '@/store'

// 权限检查函数
function hasPermission(permission) {
  const userStore = useUserStore()
  const permissionStore = usePermissionStore()

  if (userStore.isSuperUser) {
    return true
  }
  return permissionStore.apis.includes(permission)
}

// 全局组件
const { $message, $dialog } = window

defineOptions({ name: '代理管理' })

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')

const {
  modalVisible,
  modalTitle,
  modalAction,
  modalLoading,
  handleSave,
  modalForm,
  modalFormRef,
  handleEdit: originalHandleEdit,
  handleDelete,
  handleAdd: originalHandleAdd,
} = useCRUD({
  name: '代理',
  initForm: {},
  doCreate: api.createUser,
  doUpdate: api.updateUser,
  doDelete: api.deleteUser,
  refresh: () => $table.value?.handleSearch(),
})

// 自定义编辑处理函数，确保正确设置角色数据
const handleEdit = (row) => {
  originalHandleEdit(row)
  // 确保 role_ids 正确设置为角色ID数组
  modalForm.value.role_ids = row.roles?.map(role => role.id) || []
  console.log('🔧 编辑用户，设置角色IDs:', modalForm.value.role_ids)
}

// 重写handleAdd函数，在打开对话框时刷新角色列表
const handleAdd = async () => {
  console.log('🆕 打开创建代理对话框，刷新角色列表...')
  await loadCreatableRoles(true) // 强制刷新角色列表
  originalHandleAdd() // 调用原始的handleAdd
}

const roleOption = ref([])
const userStore = useUserStore()

// 积分管理相关
const pointsModalVisible = ref(false)
const pointsForm = ref({
  user_id: null,
  username: '',
  current_points: 0,
  points: 0,
  operation: 'add' // 'add' 或 'deduct'
})

// 移除下级用户相关代码，因为现在通过代理管理列表直接查看

// 加载可创建的角色列表
const loadCreatableRoles = async (forceRefresh = false) => {
  try {
    console.log('🔄 加载可创建的角色列表...', forceRefresh ? '(强制刷新)' : '')
    const response = await api.getCreatableRoles()
    if (response.code === 200) {
      roleOption.value = response.data.map(role => ({
        label: `${role.name} (层级${role.user_level})`,
        value: role.id,
        user_level: role.user_level
      }))
      console.log('✅ 角色列表加载成功:', roleOption.value)
    } else {
      console.error('❌ 加载角色列表失败:', response.msg)
      roleOption.value = []
    }
  } catch (error) {
    console.error('❌ 加载角色列表异常:', error)
    roleOption.value = []
  }
}

onMounted(() => {
  $table.value?.handleSearch()
  loadCreatableRoles()
})

// 积分管理处理函数
const handlePointsManagement = (row) => {
  pointsForm.value = {
    user_id: row.id,
    username: row.username,
    current_points: row.points_balance || 0,
    points: 0,
    operation: 'add'
  }
  pointsModalVisible.value = true
}

// 积分操作提交
const handlePointsSubmit = async () => {
  try {
    const { user_id, points, operation } = pointsForm.value
    if (!points || points <= 0) {
      $message.error('请输入有效的积分数量')
      return
    }

    const apiCall = operation === 'add' ? api.addUserPoints : api.deductUserPoints
    const response = await apiCall({ user_id, points })

    if (response.code === 200) {
      $message.success(`积分${operation === 'add' ? '增加' : '扣除'}成功`)
      pointsModalVisible.value = false
      await $table.value?.handleSearch()
    } else {
      $message.error(response.msg || '操作失败')
    }
  } catch (error) {
    // axios拦截器已经处理了错误提示，这里不需要再显示
  }
}

// 重置密码功能
const handleResetPassword = (row) => {
  $dialog.warning({
    title: '确认重置密码',
    content: `确定重置代理 "${row.username}" 的密码吗？将生成新的随机密码`,
    positiveText: '确定',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        const response = await api.resetPassword({ user_id: row.id })
        if (response.code === 200) {
          const newPassword = response.data.new_password

          // 显示新密码的二次确认对话框
          $dialog.success({
            title: '密码重置成功',
            content: () => h('div', { style: 'text-align: center;' }, [
              h('p', { style: 'margin-bottom: 16px;' }, `用户 "${row.username}" 的新密码为：`),
              h('div', {
                style: 'background: #f5f5f5; padding: 12px; border-radius: 6px; margin-bottom: 16px; font-family: monospace; font-size: 16px; font-weight: bold; color: #d03050;'
              }, newPassword),
              h('p', { style: 'color: #666; font-size: 12px;' }, '请复制并安全保存此密码，关闭后将无法再次查看')
            ]),
            positiveText: '复制密码',
            negativeText: '关闭',
            onPositiveClick: () => {
              // 复制密码到剪贴板
              navigator.clipboard.writeText(newPassword).then(() => {
                $message.success('密码已复制到剪贴板')
              }).catch(() => {
                // 降级方案：创建临时输入框复制
                const textArea = document.createElement('textarea')
                textArea.value = newPassword
                document.body.appendChild(textArea)
                textArea.select()
                document.execCommand('copy')
                document.body.removeChild(textArea)
                $message.success('密码已复制到剪贴板')
              })
            }
          })
        } else {
          $message.error(response.msg || '密码重置失败')
        }
      } catch (error) {
        // axios拦截器已经处理了错误提示，这里不需要再显示
      }
    }
  })
}

// 禁用状态切换功能（与用户管理页面保持一致）
const handleStatusChange = async (row) => {
  if (!row.id) return

  // 防止重复操作
  if (row.publishing) return

  const userStore = useUserStore()
  // 防止禁用自己
  if (userStore.userId === row.id) {
    $message.error('当前登录用户不可禁用！')
    return
  }

  row.publishing = true
  // 切换状态：true变false，false变true
  const originalStatus = row.is_active
  const newStatus = row.is_active === false ? true : false
  row.is_active = newStatus

  try {
    // 构建更新数据，包含所有必填字段
    const updateData = {
      id: row.id,
      email: row.email,
      username: row.username,
      is_active: newStatus,
      role_ids: row.roles?.map(role => role.id) || [],
      // 包含其他可选字段
      parent_user_id: row.parent_user_id || -1,
      points_balance: row.points_balance || 0,
      school: row.school || "",
      major: row.major || ""
    }

    const response = await api.updateUser(updateData)

    if (response.code === 200) {
      $message.success(newStatus ? '已取消禁用该用户' : '已禁用该用户')
      // 刷新表格数据
      await $table.value?.handleSearch()
    } else {
      $message.error(response.msg || '操作失败')
      // 恢复原状态
      row.is_active = originalStatus
    }
  } catch (error) {
    // axios拦截器已经处理了错误提示，这里只需要恢复状态
    // 恢复原状态
    row.is_active = originalStatus
  } finally {
    row.publishing = false
  }
}

const columns = [
  {
    title: '名称',
    key: 'username',
    width: 60,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  {
    title: '邮箱',
    key: 'email',
    width: 60,
    align: 'center',
    ellipsis: { tooltip: true },
  },
  // 隐藏角色层级列，层级概念只用于内部开发及关系判定
  // {
  //   title: '角色层级',
  //   key: 'user_level',
  //   width: 40,
  //   align: 'center',
  //   render(row) {
  //     const level = row.user_level || 99
  //     const levelText = level === -1 ? '超级管理员' : `层级${level}`
  //     const type = level === -1 ? 'error' : level < 10 ? 'warning' : 'info'
  //     return h(
  //       NTag,
  //       { type, style: { margin: '2px 3px' } },
  //       { default: () => levelText }
  //     )
  //   },
  // },
  {
    title: '学校',
    key: 'school',
    width: 50,
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      return row.school || '-'
    },
  },
  {
    title: '专业',
    key: 'major',
    width: 50,
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      return row.major || '-'
    },
  },
  {
    title: '积分余额',
    key: 'points_balance',
    width: 40,
    align: 'center',
    render(row) {
      return h(
        NTag,
        { type: 'success', style: { margin: '2px 3px' } },
        { default: () => row.points_balance || 0 }
      )
    },
  },
  {
    title: '邀请码',
    key: 'invitation_code',
    width: 40,
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      return row.invitation_code || '-'
    },
  },
  {
    title: '角色',
    key: 'roles',
    width: 60,
    align: 'center',
    render(row) {
      return h(
        NSpace,
        { vertical: true },
        {
          default: () =>
            row.roles?.map((role) =>
              h(
                'span',
                { style: { margin: '2px 3px', color: '#666', fontSize: '13px' } },
                role.name
              )
            ) || []
        }
      )
    },
  },
  {
    title: '禁用',
    key: 'is_active',
    width: 60,
    align: 'center',
    render(row) {
      // 与用户管理页面保持一致，直接显示开关，权限由后端验证
      return h(NSwitch, {
        size: 'small',
        rubberBand: false,
        value: row.is_active,
        loading: !!row.publishing,
        checkedValue: false,  // 开关打开表示禁用
        uncheckedValue: true, // 开关关闭表示不禁用
        onUpdateValue: () => handleStatusChange(row),
      })
    },
  },
  {
    title: '创建时间',
    key: 'created_at',
    width: 60,
    align: 'center',
    render(row) {
      return formatDate(row.created_at)
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 120,
    align: 'center',
    fixed: 'right',
    hideInExcel: true,
    render(row) {
      const dropdownOptions = [
        {
          label: '编辑',
          key: 'edit',
          icon: renderIcon('material-symbols:edit', { size: 16 }),
        },
        {
          label: '删除',
          key: 'delete',
          icon: renderIcon('material-symbols:delete-outline', { size: 16 }),
        },
        {
          label: '重置密码',
          key: 'resetPassword',
          icon: renderIcon('material-symbols:lock-reset', { size: 16 }),
        },
        {
          label: '积分管理',
          key: 'points',
          icon: renderIcon('material-symbols:account-balance-wallet', { size: 16 }),
        },
      ]

      const handleDropdownSelect = (key) => {
        switch (key) {
          case 'edit':
            handleEdit(row)
            break
          case 'delete':
            $dialog.warning({
              title: '确认删除',
              content: `确定删除代理 "${row.username}" 吗？`,
              positiveText: '确定',
              negativeText: '取消',
              onPositiveClick: () => handleDelete({ user_id: row.id })
            })
            break
          case 'resetPassword':
            handleResetPassword(row)
            break
          case 'points':
            handlePointsManagement(row)
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

// 表单验证规则（简化版，角色由后端验证）
const validateAddAgent = {
  username: [
    {
      required: true,
      message: '请输入代理名称',
      trigger: ['input', 'blur'],
    },
  ],
  email: [
    {
      required: true,
      message: '请输入邮箱地址',
      trigger: ['input', 'change'],
    },
    {
      trigger: ['blur'],
      validator: (rule, value, callback) => {
        const re = /^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$/
        if (!re.test(modalForm.value.email)) {
          callback('邮箱格式错误')
          return
        }
        callback()
      },
    },
  ],
  password: [
    {
      required: true,
      message: '请输入密码',
      trigger: ['input', 'blur', 'change'],
    },
  ],
  confirmPassword: [
    {
      required: true,
      message: '请再次输入密码',
      trigger: ['input'],
    },
    {
      trigger: ['blur'],
      validator: (rule, value, callback) => {
        if (value !== modalForm.value.password) {
          callback('两次密码输入不一致')
          return
        }
        callback()
      },
    },
  ],
  role_ids: [
    {
      type: 'array',
      required: true,
      message: '请至少选择一个角色',
      trigger: ['blur', 'change'],
    },
  ],
}
</script>

<template>
  <div>
      <CommonPage show-footer title="代理用户列表">
        <template #action>
          <NButton v-permission="'post/api/v1/user/create'" type="primary" @click="handleAdd">
            <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建代理
          </NButton>
        </template>
        <!-- 表格 -->
        <CrudTable
          ref="$table"
          v-model:query-items="queryItems"
          :columns="columns"
          :get-data="api.getAgentList"
        >
          <template #queryBar>
            <QueryBarItem label="名称" :label-width="40">
              <NInput
                v-model:value="queryItems.username"
                clearable
                type="text"
                placeholder="请输入代理名称"
                @keypress.enter="$table?.handleSearch()"
              />
            </QueryBarItem>
            <QueryBarItem label="邮箱" :label-width="40">
              <NInput
                v-model:value="queryItems.email"
                clearable
                type="text"
                placeholder="请输入邮箱"
                @keypress.enter="$table?.handleSearch()"
              />
            </QueryBarItem>
          </template>
        </CrudTable>

        <!-- 新增/编辑 弹窗 -->
        <CrudModal
          v-model:visible="modalVisible"
          :title="modalTitle"
          :loading="modalLoading"
          @onSave="handleSave"
        >
          <NForm
            ref="modalFormRef"
            label-placement="left"
            label-align="left"
            :label-width="80"
            :model="modalForm"
            :rules="validateAddAgent"
          >
            <NFormItem label="代理名称" path="username">
              <NInput v-model:value="modalForm.username" clearable placeholder="请输入代理名称" />
            </NFormItem>
            <NFormItem label="邮箱" path="email">
              <NInput v-model:value="modalForm.email" clearable placeholder="请输入邮箱" />
            </NFormItem>
            <NFormItem v-if="modalAction === 'add'" label="邀请码" path="invitation_code">
              <NInput v-model:value="modalForm.invitation_code" clearable placeholder="请输入邀请码（可选）" />
            </NFormItem>
            <NFormItem label="学校" path="school">
              <NInput v-model:value="modalForm.school" clearable placeholder="请输入学校" />
            </NFormItem>
            <NFormItem label="专业" path="major">
              <NInput v-model:value="modalForm.major" clearable placeholder="请输入专业" />
            </NFormItem>
            <NFormItem v-if="modalAction === 'add'" label="密码" path="password">
              <NInput v-model:value="modalForm.password" type="password" clearable placeholder="请输入密码" />
            </NFormItem>
            <NFormItem v-if="modalAction === 'add'" label="确认密码" path="confirmPassword">
              <NInput v-model:value="modalForm.confirmPassword" type="password" clearable placeholder="请再次输入密码" />
            </NFormItem>
            <!-- 角色选择：仅在创建时显示 -->
            <NFormItem v-if="modalAction === 'add'" label="角色" path="role_ids">
              <NCheckboxGroup v-model:value="modalForm.role_ids">
                <NSpace item-style="display: flex;">
                  <NCheckbox
                    v-for="item in roleOption"
                    :key="item.value"
                    :value="item.value"
                    :label="item.label"
                  />
                </NSpace>
              </NCheckboxGroup>
            </NFormItem>

            <!-- 编辑时显示当前角色（只读） -->
            <NFormItem v-if="modalAction === 'edit'" label="当前角色">
              <NSpace>
                <NTag v-for="item in roleOption.filter(r => modalForm.role_ids?.includes(r.value))" :key="item.value" type="info">
                  {{ item.label }}
                </NTag>
                <NTag v-if="!modalForm.role_ids || modalForm.role_ids.length === 0" type="warning">
                  无角色
                </NTag>
              </NSpace>
            </NFormItem>
            <NFormItem label="状态" path="is_active">
              <NSwitch v-model:value="modalForm.is_active">
                <template #checked>启用</template>
                <template #unchecked>禁用</template>
              </NSwitch>
            </NFormItem>
          </NForm>
        </CrudModal>

        <!-- 积分管理弹窗 -->
        <CrudModal
          v-model:visible="pointsModalVisible"
          title="积分管理"
          :show-footer="true"
          @onSave="handlePointsSubmit"
        >
          <NForm label-placement="left" label-align="left" :label-width="100">
            <NFormItem label="用户名称">
              <NInput :value="pointsForm.username" readonly />
            </NFormItem>
            <NFormItem label="当前积分">
              <NInput :value="pointsForm.current_points.toString()" readonly />
            </NFormItem>
            <NFormItem label="操作类型">
              <NSpace>
                <NButton
                  :type="pointsForm.operation === 'add' ? 'primary' : 'default'"
                  @click="pointsForm.operation = 'add'"
                >
                  增加积分
                </NButton>
                <NButton
                  :type="pointsForm.operation === 'deduct' ? 'primary' : 'default'"
                  @click="pointsForm.operation = 'deduct'"
                >
                  扣除积分
                </NButton>
              </NSpace>
            </NFormItem>
            <NFormItem label="积分数量">
              <NInput
                v-model:value="pointsForm.points"
                type="number"
                :placeholder="`请输入要${pointsForm.operation === 'add' ? '增加' : '扣除'}的积分数量`"
              />
            </NFormItem>
          </NForm>
        </CrudModal>

        <!-- 移除下级用户弹窗，现在通过代理管理列表直接查看 -->
      </CommonPage>
  </div>
</template>
