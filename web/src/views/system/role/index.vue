<script setup>
import { h, onMounted, ref, resolveDirective, withDirectives } from 'vue'
import {
  NButton,
  NCheckbox,
  NCheckboxGroup,
  NForm,
  NFormItem,
  NInput,
  NPopconfirm,
  NSelect,
  NSpace,
  NSwitch,
  NTag,
  NTree,
  NDrawer,
  NDrawerContent,
  NTabs,
  NTabPane,
  NGrid,
  NGi,
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
import { useDialog, useMessage } from 'naive-ui'

defineOptions({ name: '角色管理' })

const $table = ref(null)
const queryItems = ref({})
const vPermission = resolveDirective('permission')
const userStore = useUserStore()
const $dialog = useDialog()
const $message = useMessage()

const {
  modalVisible,
  modalAction,
  modalTitle,
  modalLoading,
  handleAdd,
  handleDelete: originalHandleDelete,
  handleEdit,
  handleSave,
  modalForm,
  modalFormRef,
} = useCRUD({
  name: '角色',
  initForm: {},
  doCreate: api.createRole,
  doDelete: api.deleteRole,
  doUpdate: api.updateRole,
  refresh: () => $table.value?.handleSearch(),
})

// 自定义删除处理函数，添加用户数量检查和二次确认
const handleDelete = async (item, needConfirm = true) => {
  const roleId = item.role_id || item.id

  try {
    // 首先检查角色关联的用户数量
    const checkResult = await api.checkRoleUsers({ role_id: roleId })

    if (checkResult.code === 200) {
      const { role_name, user_count } = checkResult.data

      if (user_count === 0) {
        // 没有关联用户，直接删除
        $dialog.warning({
          title: '确认删除',
          content: `确定删除角色 "${role_name}" 吗？`,
          positiveText: '确定',
          negativeText: '取消',
          onPositiveClick: async () => {
            try {
              await api.deleteRole({ role_id: roleId })
              $message.success('角色删除成功')
              $table.value?.handleSearch()
            } catch (error) {
              $message.error('删除失败: ' + error.message)
            }
          }
        })
      } else {
        // 有关联用户，显示二次确认对话框
        $dialog.error({
          title: '删除确认',
          content: `角色 "${role_name}" 关联了 ${user_count} 个用户。删除角色将同时删除这些用户，此操作不可恢复！`,
          positiveText: '确定删除',
          negativeText: '取消',
          onPositiveClick: () => {
            // 第二次确认
            $dialog.error({
              title: '最终确认',
              content: `您确定要删除角色 "${role_name}" 及其关联的 ${user_count} 个用户吗？此操作不可恢复！`,
              positiveText: '确定删除',
              negativeText: '取消',
              onPositiveClick: async () => {
                try {
                  await api.deleteRole({ role_id: roleId, force_delete: true })
                  $message.success(`已删除角色 "${role_name}" 及其关联的 ${user_count} 个用户`)
                  $table.value?.handleSearch()
                } catch (error) {
                  $message.error('删除失败: ' + error.message)
                }
              }
            })
          }
        })
      }
    }
  } catch (error) {
    $message.error('检查角色用户失败: ' + error.message)
  }
}

const pattern = ref('')
const menuOption = ref([]) // 菜单选项
const active = ref(false)
const menu_ids = ref([])
const role_id = ref(0)
const apiOption = ref([])
const api_ids = ref([])

// 代理权限相关
const agentPermissionsConfig = ref({
  permissions: {},
  all_permissions: []
})
const selectedAgentPermissions = ref([])
const isAgentRole = ref(false)

// 权限与菜单映射关系
const permissionMenuMapping = ref({
  permission_menu_map: {},
  super_admin_only_menus: [],
  permission_descriptions: {}
})

function buildApiTree(data) {
  const processedData = []
  const groupedData = {}

  data.forEach((item) => {
    const tags = item['tags']
    const pathParts = item['path'].split('/')
    const path = pathParts.slice(0, -1).join('/')
    const summary = tags.charAt(0).toUpperCase() + tags.slice(1)
    const unique_id = item['method'].toLowerCase() + item['path']
    if (!(path in groupedData)) {
      groupedData[path] = { unique_id: path, path: path, summary: summary, children: [] }
    }

    groupedData[path].children.push({
      id: item['id'],
      path: item['path'],
      method: item['method'],
      summary: item['summary'],
      unique_id: unique_id,
    })
  })
  processedData.push(...Object.values(groupedData))
  return processedData
}

onMounted(async () => {
  $table.value?.handleSearch()
  await loadAgentPermissionsConfig()
  await loadPermissionMenuMapping()
})

// 加载代理权限配置
async function loadAgentPermissionsConfig() {
  try {
    const response = await api.getAgentPermissionsConfig()
    agentPermissionsConfig.value = response.data
  } catch (error) {
    console.error('加载代理权限配置失败:', error)
  }
}

// 加载权限与菜单映射关系
async function loadPermissionMenuMapping() {
  try {
    const response = await api.getPermissionMenuMapping()
    permissionMenuMapping.value = response.data
  } catch (error) {
    console.error('加载权限菜单映射失败:', error)
  }
}

const columns = [
  {
    title: '角色名',
    key: 'name',
    width: 80,
    align: 'center',
    ellipsis: { tooltip: true },
    render(row) {
      return h(NTag, { type: 'info' }, { default: () => row.name })
    },
  },
  {
    title: '角色描述',
    key: 'desc',
    width: 80,
    align: 'center',
  },
  {
    title: '角色层级',
    key: 'user_level',
    width: 80,
    align: 'center',
    render(row) {
      const level = row.user_level
      let tagType = 'default'

      // 根据层级数字设置标签颜色
      if (level === -1) {
        tagType = 'error'  // 超级管理员用红色
      } else if (level === 0) {
        tagType = 'warning' // 超级代理用橙色
      } else if (level >= 1 && level <= 3) {
        tagType = 'info'    // 代理角色用蓝色
      } else if (level === 99) {
        tagType = 'default' // 普通用户用默认色
      }

      return h(NTag, { type: tagType, size: 'small' }, { default: () => level?.toString() || '99' })
    },
  },
  {
    title: '创建日期',
    key: 'created_at',
    width: 60,
    align: 'center',
    render(row) {
      return h('span', formatDate(row.created_at))
    },
  },
  {
    title: '操作',
    key: 'actions',
    width: 80,
    align: 'center',
    fixed: 'right',
    render(row) {
      const buttons = []

      // 只有超级管理员才能看到编辑按钮
      if (userStore.isSuperUser) {
        buttons.push(
          withDirectives(
            h(
              NButton,
              {
                size: 'small',
                type: 'primary',
                style: 'margin-right: 8px;',
                onClick: () => {
                  handleEdit(row)
                },
              },
              {
                default: () => '编辑',
                icon: renderIcon('material-symbols:edit-outline', { size: 16 }),
              }
            ),
            [[vPermission, 'post/api/v1/role/update']]
          )
        )
        // 只有超级管理员才能看到删除按钮
        if (userStore.isSuperUser) {
          buttons.push(
            h(
              NPopconfirm,
              {
                onPositiveClick: () => handleDelete({ role_id: row.id }, false),
                onNegativeClick: () => {},
              },
              {
                trigger: () =>
                  withDirectives(
                    h(
                      NButton,
                      {
                        size: 'small',
                        type: 'error',
                        style: 'margin-right: 8px;',
                      },
                      {
                        default: () => '删除',
                        icon: renderIcon('material-symbols:delete-outline', { size: 16 }),
                      }
                    ),
                    [[vPermission, 'delete/api/v1/role/delete']]
                  ),
                default: () => h('div', {}, '确定删除该角色吗?'),
              }
            )
          )
        }
        // 只有超级管理员才能看到权限设置按钮
        if (userStore.isSuperUser) {
          buttons.push(
            withDirectives(
              h(
                NButton,
                {
                  size: 'small',
                  type: 'primary',
                  onClick: async () => {
                    try {
                      // 使用 Promise.all 来同时发送所有请求
                      const [menusResponse, apisResponse, roleAuthorizedResponse] = await Promise.all([
                        api.getMenus({ page: 1, page_size: 9999 }),
                        api.getApis({ page: 1, page_size: 9999 }),
                        api.getRoleAuthorized({ id: row.id }),
                      ])

                      // 处理每个请求的响应
                      menuOption.value = menusResponse.data
                      apiOption.value = buildApiTree(apisResponse.data)
                      menu_ids.value = roleAuthorizedResponse.data.menus.map((v) => v.id)
                      api_ids.value = roleAuthorizedResponse.data.apis.map(
                        (v) => v.method.toLowerCase() + v.path
                      )

                      // 加载代理权限配置
                      selectedAgentPermissions.value = roleAuthorizedResponse.data.agent_permissions || []
                      isAgentRole.value = roleAuthorizedResponse.data.is_agent_role || false

                      active.value = true
                      role_id.value = row.id
                    } catch (error) {
                      // 错误处理
                      console.error('Error loading data:', error)
                    }
                  },
                },
                {
                  default: () => '设置权限',
                  icon: renderIcon('material-symbols:edit-outline', { size: 16 }),
                }
              ),
              [[vPermission, 'get/api/v1/role/authorized']]
            )
          )
        }

        return buttons
      }
    },
  },
]

async function updateRoleAuthorized() {
  try {
    // 只更新菜单权限，API权限暂时不处理
    const { code, msg } = await api.updateRoleAuthorized({
      id: role_id.value,
      menu_ids: menu_ids.value,
      api_infos: [], // 暂时传空数组，保持API兼容性
    })

    if (code === 200) {
      $message?.success('菜单权限设置成功')
      active.value = false // 关闭抽屉
      $table.value?.handleSearch() // 刷新表格
    } else {
      $message?.error(msg || '设置失败')
    }
  } catch (error) {
    console.error('更新角色权限失败:', error)
    $message?.error('设置失败，请重试')
  }
}

// 更新代理权限
async function updateAgentPermissions() {
  try {
    await api.updateRoleAgentPermissions({
      id: role_id.value,
      agent_permissions: selectedAgentPermissions.value,
      is_agent_role: isAgentRole.value,
    })
    $message.success('代理权限更新成功')
    active.value = false
    $table.value?.handleSearch()
  } catch (error) {
    console.error('代理权限更新失败:', error)
    $message.error('代理权限更新失败')
  }
}
</script>

<template>
  <CommonPage show-footer title="角色列表">
    <template #action>
      <NButton
        v-if="userStore.isSuperUser"
        v-permission="'post/api/v1/role/create'"
        type="primary"
        @click="handleAdd"
      >
        <TheIcon icon="material-symbols:add" :size="18" class="mr-5" />新建角色
      </NButton>
    </template>

    <CrudTable
      ref="$table"
      v-model:query-items="queryItems"
      :columns="columns"
      :get-data="api.getRoleList"
    >
      <template #queryBar>
        <QueryBarItem label="角色名" :label-width="50">
          <NInput
            v-model:value="queryItems.role_name"
            clearable
            type="text"
            placeholder="请输入角色名"
            @keypress.enter="$table?.handleSearch()"
          />
        </QueryBarItem>
      </template>
    </CrudTable>

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
        :disabled="modalAction === 'view'"
      >
        <NFormItem
          label="角色名"
          path="name"
          :rule="{
            required: true,
            message: '请输入角色名称',
            trigger: ['input', 'blur'],
          }"
        >
          <NInput v-model:value="modalForm.name" placeholder="请输入角色名称" />
        </NFormItem>
        <NFormItem label="角色描述" path="desc">
          <NInput v-model:value="modalForm.desc" placeholder="请输入角色描述" />
        </NFormItem>
        <NFormItem
          label="角色层级"
          path="user_level"
          :rule="{
            required: true,
            type: 'number',
            message: '请输入角色层级',
            trigger: ['input', 'blur'],
          }"
        >
          <NInputNumber
            v-model:value="modalForm.user_level"
            placeholder="请输入角色层级"
            :min="-1"
            :max="99"
            :step="1"
            style="width: 100%"
          />
          <template #feedback>
            <div class="text-12 op-60 mt-5">
              层级说明：-1=超级管理员，0-N=代理角色（数字越小权限越高），99=普通用户。只能创建层级数字大于自己的角色。
            </div>
          </template>
        </NFormItem>
      </NForm>
    </CrudModal>

    <NDrawer v-model:show="active" placement="right" :width="500"
      ><NDrawerContent>
        <NGrid x-gap="24" cols="12">
          <NGi span="8">
            <NInput
              v-model:value="pattern"
              type="text"
              placeholder="筛选"
              style="flex-grow: 1"
            ></NInput>
          </NGi>
          <NGi offset="2">
            <NButton
              v-permission="'post/api/v1/role/authorized'"
              type="info"
              @click="updateRoleAuthorized"
              >确定</NButton
            >
          </NGi>
        </NGrid>
        <NTabs>
          <NTabPane name="agent" tab="代理权限" display-directive="show">
            <NSpace vertical>
              <NFormItem label="角色类型">
                <NSwitch
                  v-model:value="isAgentRole"
                  :checked-value="true"
                  :unchecked-value="false"
                >
                  <template #checked>代理角色</template>
                  <template #unchecked>普通角色</template>
                </NSwitch>
              </NFormItem>



              <NFormItem v-if="isAgentRole" label="代理权限">
                <NCheckboxGroup v-model:value="selectedAgentPermissions">
                  <NSpace vertical>
                    <div
                      v-for="(desc, permission) in agentPermissionsConfig.permissions"
                      :key="permission"
                      class="permission-item"
                    >
                      <NCheckbox
                        :value="permission"
                        :label="desc"
                      />
                      <div v-if="permissionMenuMapping.permission_descriptions[permission]" class="permission-menu-info">
                        <NTag size="small" type="info">
                          {{ permissionMenuMapping.permission_descriptions[permission] }}
                        </NTag>
                      </div>
                    </div>
                  </NSpace>
                </NCheckboxGroup>
              </NFormItem>

              <NSpace>
                <NButton
                  v-permission="'post/api/v1/role/agent_permissions'"
                  type="primary"
                  @click="updateAgentPermissions"
                >
                  更新代理权限
                </NButton>
              </NSpace>
            </NSpace>
          </NTabPane>

          <NTabPane name="menu" tab="菜单权限" display-directive="show">
            <!-- TODO：级联 -->
            <NTree
              :data="menuOption"
              :checked-keys="menu_ids"
              :pattern="pattern"
              :show-irrelevant-nodes="false"
              key-field="id"
              label-field="name"
              checkable
              :default-expand-all="true"
              :block-line="true"
              :selectable="false"
              @update:checked-keys="(v) => (menu_ids = v)"
            />
          </NTabPane>


        </NTabs>
        <template #header> 设置权限 </template>
      </NDrawerContent>
    </NDrawer>
  </CommonPage>
</template>

<style scoped>
.permission-item {
  margin-bottom: 8px;
}

.permission-menu-info {
  margin-top: 4px;
  margin-left: 24px;
  font-size: 12px;
  color: #666;
}
</style>
