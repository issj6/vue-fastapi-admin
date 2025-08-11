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
// import { loginTypeMap, loginTypeOptions } from '@/constant/data'
import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'
import { useUserStore } from '@/store'

defineOptions({ name: '用户管理' })

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
  handleEdit,
  handleDelete,
  handleAdd: originalHandleAdd,
} = useCRUD({
  name: '用户',
  initForm: {},
  doCreate: api.createUser,
  doUpdate: api.updateUser,
  doDelete: api.deleteUser,
  refresh: () => $table.value?.handleSearch(),
})

// 重写handleAdd函数，在打开对话框时刷新角色列表
const handleAdd = async () => {
  console.log('🆕 打开创建用户对话框，刷新角色列表...')
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

// 下级用户相关
const subordinatesModalVisible = ref(false)
const subordinatesData = ref([])
const subordinatesLoading = ref(false)

// 加载可创建的角色列表
const loadCreatableRoles = async (forceRefresh = false) => {
  try {
    console.log('🔄 加载可创建角色列表...', { isSuperUser: userStore.isSuperUser, forceRefresh })

    // 如果是超级管理员，获取所有角色
    if (userStore.isSuperUser) {
      const res = await api.getRoleList({ page: 1, page_size: 9999 })
      roleOption.value = res.data
      console.log('👑 超级管理员可创建角色:', res.data.map(r => r.name))
    } else {
      // 普通用户只能获取可创建的角色
      const res = await api.getCreatableRoles()
      roleOption.value = res.data
      console.log('👤 当前用户可创建角色:', res.data.map(r => r.name))
    }
  } catch (error) {
    console.error('❌ 加载角色列表失败:', error)
    roleOption.value = []
  }
}

onMounted(() => {
  $table.value?.handleSearch()
  loadCreatableRoles()
})

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
    width: 120,
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      return h(
        NTag,
        { type: 'warning', style: { margin: '2px 3px' } },
        { default: () => row.invitation_code || '-' }
      )
    },
  },
  // 用户管理页面隐藏角色和超级用户列，因为都是普通用户
  // {
  //   title: '用户角色',
  //   key: 'role',
  //   width: 60,
  //   align: 'center',
  //   render(row) {
  //     const roles = row.roles ?? []
  //     const group = []
  //     for (let i = 0; i < roles.length; i++)
  //       group.push(
  //         h(NTag, { type: 'info', style: { margin: '2px 3px' } }, { default: () => roles[i].name })
  //       )
  //     return h('span', group)
  //   },
  // },

  // {
  //   title: '超级用户',
  //   key: 'is_superuser',
  //   align: 'center',
  //   width: 40,
  //   render(row) {
  //     return h(
  //       NTag,
  //       { type: 'info', style: { margin: '2px 3px' } },
  //       { default: () => (row.is_superuser ? '是' : '否') }
  //     )
  //   },
  // },
  {
    title: '上次登录时间',
    key: 'last_login',
    align: 'center',
    width: 80,
    ellipsis: { tooltip: true },
    render(row) {
      return h(
        NButton,
        { size: 'small', type: 'text', ghost: true },
        {
          default: () => (row.last_login !== null ? formatDate(row.last_login) : null),
          icon: renderIcon('mdi:update', { size: 16 }),
        }
      )
    },
  },
  {
    title: '禁用',
    key: 'is_active',
    width: 50,
    align: 'center',
    render(row) {
      return h(NSwitch, {
        size: 'small',
        rubberBand: false,
        value: row.is_active,
        loading: !!row.publishing,
        checkedValue: false,
        uncheckedValue: true,
        onUpdateValue: () => handleUpdateDisable(row),
      })
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 80,
    align: 'center',
    fixed: 'right',
    render(row) {
      // 构建下拉菜单选项
      const dropdownOptions = []

      // 编辑选项
      dropdownOptions.push({
        label: '编辑',
        key: 'edit',
        icon: renderIcon('material-symbols:edit', { size: 16 }),
      })

      // 删除选项
      dropdownOptions.push({
        label: '删除',
        key: 'delete',
        icon: renderIcon('material-symbols:delete-outline', { size: 16 }),
      })

      // 重置密码选项（非超级用户才显示）
      if (!row.is_superuser) {
        dropdownOptions.push({
          label: '重置密码',
          key: 'reset-password',
          icon: renderIcon('material-symbols:lock-reset', { size: 16 }),
        })
      }

      // 积分管理选项
      dropdownOptions.push({
        label: '积分管理',
        key: 'points',
        icon: renderIcon('material-symbols:monetization-on', { size: 16 }),
      })

      // 下级用户选项
      dropdownOptions.push({
        label: '下级用户',
        key: 'subordinates',
        icon: renderIcon('material-symbols:group', { size: 16 }),
      })

      // 处理下拉菜单选择
      const handleDropdownSelect = (key) => {
        switch (key) {
          case 'edit':
            handleEdit(row)
            // 编辑时保存角色信息用于显示，但不设置role_ids（避免编辑时修改角色）
            modalForm.value.roles = row.roles || []
            console.log('🔧 编辑用户，当前角色:', modalForm.value.roles.map(r => r.name))
            break
          case 'delete':
            $dialog.warning({
              title: '确认删除',
              content: '确定删除该用户吗？',
              positiveText: '确定',
              negativeText: '取消',
              onPositiveClick: () => {
                handleDelete({ user_id: row.id }, false)
              }
            })
            break
          case 'reset-password':
            $dialog.warning({
              title: '确认重置密码',
              content: `确定重置用户 "${row.username}" 的密码吗？将生成新的随机密码`,
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
                    await $table.value?.handleSearch()
                  } else {
                    $message.error(response.msg || '密码重置失败')
                  }
                } catch (error) {
                  $message.error('重置密码失败: ' + error.message)
                }
              }
            })
            break
          case 'points':
            handlePointsManagement(row)
            break
          case 'subordinates':
            handleViewSubordinates(row)
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

// 修改用户禁用状态
async function handleUpdateDisable(row) {
  if (!row.id) return
  const userStore = useUserStore()
  if (userStore.userId === row.id) {
    $message.error('当前登录用户不可禁用！')
    return
  }
  row.publishing = true
  row.is_active = row.is_active === false ? true : false
  row.publishing = false
  const role_ids = []
  row.roles.forEach((e) => {
    role_ids.push(e.id)
  })
  row.role_ids = role_ids
  try {
    await api.updateUser(row)
    $message?.success(row.is_active ? '已取消禁用该用户' : '已禁用该用户')
    $table.value?.handleSearch()
  } catch (err) {
    // 有异常恢复原来的状态
    row.is_active = row.is_active === false ? true : false
  } finally {
    row.publishing = false
  }
}



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

    if (operation === 'add') {
      await api.addUserPoints({ user_id, points })
      $message.success('积分增加成功')
    } else {
      await api.deductUserPoints({ user_id, points })
      $message.success('积分扣除成功')
    }

    pointsModalVisible.value = false
    $table.value?.handleSearch()
  } catch (error) {
    $message.error('操作失败: ' + (error.response?.data?.msg || error.message))
  }
}

// 查看下级用户处理函数
const handleViewSubordinates = async (row) => {
  subordinatesLoading.value = true
  subordinatesModalVisible.value = true

  try {
    const res = await api.getSubordinateUsers({ page: 1, page_size: 100 })
    subordinatesData.value = res.data || []
  } catch (error) {
    $message.error('获取下级用户失败: ' + (error.response?.data?.msg || error.message))
    subordinatesData.value = []
  } finally {
    subordinatesLoading.value = false
  }
}

// 动态验证规则：创建时角色必选，编辑时角色不验证
const validateAddUser = computed(() => ({
  username: [
    {
      required: true,
      message: '请输入名称',
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
  role_ids: modalAction.value === 'add' ? [
    {
      type: 'array',
      required: true,
      message: '请至少选择一个角色',
      trigger: ['blur', 'change'],
    },
  ] : [],
}))
</script>

<template>
  <div>
      <CommonPage show-footer title="用户列表">
        <template #action>
          <NButton v-permission="'post/api/v1/user/create'" type="primary" @click="handleAdd">
            <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建用户
          </NButton>
        </template>
        <!-- 表格 -->
        <CrudTable
          ref="$table"
          v-model:query-items="queryItems"
          :columns="columns"
          :get-data="api.getUserList"
        >
          <template #queryBar>
            <QueryBarItem label="名称" :label-width="40">
              <NInput
                v-model:value="queryItems.username"
                clearable
                type="text"
                placeholder="请输入用户名称"
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
            :rules="validateAddUser"
          >
            <NFormItem label="用户名称" path="username">
              <NInput v-model:value="modalForm.username" clearable placeholder="请输入用户名称" />
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
              <NInput
                v-model:value="modalForm.password"
                show-password-on="mousedown"
                type="password"
                clearable
                placeholder="请输入密码"
              />
            </NFormItem>
            <NFormItem v-if="modalAction === 'add'" label="确认密码" path="confirmPassword">
              <NInput
                v-model:value="modalForm.confirmPassword"
                show-password-on="mousedown"
                type="password"
                clearable
                placeholder="请确认密码"
              />
            </NFormItem>
            <!-- 角色选择：仅在创建时显示 -->
            <NFormItem v-if="modalAction === 'add'" label="角色" path="role_ids">
              <NCheckboxGroup v-model:value="modalForm.role_ids">
                <NSpace item-style="display: flex;">
                  <NCheckbox
                    v-for="item in roleOption"
                    :key="item.id"
                    :value="item.id"
                    :label="item.name"
                  />
                </NSpace>
              </NCheckboxGroup>
            </NFormItem>

            <!-- 编辑时显示当前角色（只读） -->
            <NFormItem v-if="modalAction === 'edit'" label="当前角色">
              <NSpace>
                <NTag v-for="role in modalForm.roles || []" :key="role.id" type="info">
                  {{ role.name }}
                </NTag>
                <NTag v-if="!modalForm.roles || modalForm.roles.length === 0" type="warning">
                  无角色
                </NTag>
              </NSpace>
            </NFormItem>
            <NFormItem v-if="userStore.isSuperUser" label="超级用户" path="is_superuser">
              <NSwitch
                v-model:value="modalForm.is_superuser"
                size="small"
                :checked-value="true"
                :unchecked-value="false"
              ></NSwitch>
            </NFormItem>
            <NFormItem label="禁用" path="is_active">
              <NSwitch
                v-model:value="modalForm.is_active"
                :checked-value="false"
                :unchecked-value="true"
                :default-value="true"
              />
            </NFormItem>
          </NForm>
        </CrudModal>

        <!-- 积分管理弹窗 -->
        <CrudModal
          v-model:visible="pointsModalVisible"
          title="积分管理"
          @onSave="handlePointsSubmit"
        >
          <NForm
            label-placement="left"
            label-align="left"
            :label-width="100"
            :model="pointsForm"
          >
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
                placeholder="请输入积分数量"
                clearable
              />
            </NFormItem>
          </NForm>
        </CrudModal>

        <!-- 下级用户弹窗 -->
        <CrudModal
          v-model:visible="subordinatesModalVisible"
          title="下级用户列表"
          :show-footer="false"
          width="800px"
        >
          <NTable :loading="subordinatesLoading">
            <thead>
              <tr>
                <th>用户名</th>
                <th>邮箱</th>
                <th>学校</th>
                <th>专业</th>
                <th>积分余额</th>
                <th>邀请码</th>
                <th>创建时间</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in subordinatesData" :key="user.id">
                <td>{{ user.username }}</td>
                <td>{{ user.email }}</td>
                <td>{{ user.school || '-' }}</td>
                <td>{{ user.major || '-' }}</td>
                <td>{{ user.points_balance || 0 }}</td>
                <td>{{ user.invitation_code || '-' }}</td>
                <td>{{ formatDate(user.created_at) }}</td>
              </tr>
              <tr v-if="subordinatesData.length === 0 && !subordinatesLoading">
                <td colspan="7" style="text-align: center; color: #999;">暂无下级用户</td>
              </tr>
            </tbody>
          </NTable>
        </CrudModal>
      </CommonPage>
  </div>
  <!-- 业务页面 -->
</template>
