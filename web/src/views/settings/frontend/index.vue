<script setup>
import { ref, onMounted } from 'vue'
import {
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NSwitch,
  NButton,
  NCard,
  NSpace,
  NAlert,
} from 'naive-ui'

import CommonPage from '@/components/page/CommonPage.vue'
import { renderIcon } from '@/utils'
import api from '@/api'

defineOptions({ name: '前台设置' })

// 全局组件
const { $message } = window

const loading = ref(false)
const formRef = ref(null)

// 表单数据
const formData = ref({
  site_name: '',
  recharge_rate: '1.0',
  maintenance_mode: false,
})

// 表单验证规则
const rules = {
  site_name: [
    { max: 100, message: '网站名称长度不能超过100个字符', trigger: 'blur' },
  ],
  recharge_rate: [
    { required: true, message: '请输入积分充值单价', trigger: 'blur' },
    { 
      pattern: /^\d+(\.\d{1,2})?$/, 
      message: '请输入有效的价格（最多保留2位小数）', 
      trigger: 'blur' 
    },
  ],
}

// 获取前台配置
async function getFrontendConfig() {
  try {
    loading.value = true
    const response = await api.getFrontendConfig()
    if (response.data) {
      formData.value = {
        site_name: response.data.site_name || '',
        recharge_rate: response.data.recharge_rate || '1.0',
        maintenance_mode: response.data.maintenance_mode || false,
      }
    }
  } catch (error) {
    console.error('获取前台配置失败:', error)
    $message?.error('获取配置失败')
  } finally {
    loading.value = false
  }
}

// 保存配置
async function handleSave() {
  try {
    await formRef.value?.validate()
    loading.value = true
    
    const updateData = {
      site_name: formData.value.site_name || '',
      recharge_rate: formData.value.recharge_rate,
      maintenance_mode: formData.value.maintenance_mode,
    }
    
    await api.updateFrontendConfig(updateData)
    $message?.success('配置保存成功')
  } catch (error) {
    console.error('保存配置失败:', error)
    if (error.errors) {
      // 表单验证错误
      return
    }
    $message?.error('保存配置失败')
  } finally {
    loading.value = false
  }
}

// 重置配置
function handleReset() {
  getFrontendConfig()
}

onMounted(() => {
  getFrontendConfig()
})
</script>

<template>
  <CommonPage show-footer title="前台设置">
    <template #action>
      <NSpace>
        <NButton @click="handleReset" :loading="loading">
          <template #icon>
            <component :is="renderIcon('material-symbols:refresh', { size: 16 })" />
          </template>
          重置
        </NButton>
        <NButton type="primary" @click="handleSave" :loading="loading">
          <template #icon>
            <component :is="renderIcon('material-symbols:save', { size: 16 })" />
          </template>
          保存配置
        </NButton>
      </NSpace>
    </template>

    <NCard title="基础配置" class="mb-4">
      <NForm
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-placement="left"
        label-width="120"
        require-mark-placement="right-hanging"
      >
        <NFormItem label="网站名称" path="site_name">
          <NInput
            v-model:value="formData.site_name"
            placeholder="请输入网站名称（可留空）"
            maxlength="100"
            show-count
            clearable
          />
        </NFormItem>

        <NFormItem label="积分充值单价" path="recharge_rate">
          <NInput
            v-model:value="formData.recharge_rate"
            placeholder="请输入前台用户积分充值单价"
            clearable
          >
            <template #suffix>元/积分</template>
          </NInput>
          <template #feedback>
            <NAlert type="info" size="small" :show-icon="false" class="mt-2">
              此价格为前台普通用户的积分充值单价，与代理价格（1元/1积分）不同
            </NAlert>
          </template>
        </NFormItem>

        <NFormItem label="维护模式">
          <NSwitch
            v-model:value="formData.maintenance_mode"
            :checked-value="true"
            :unchecked-value="false"
          >
            <template #checked>开启</template>
            <template #unchecked>关闭</template>
          </NSwitch>
          <template #feedback>
            <NAlert 
              :type="formData.maintenance_mode ? 'warning' : 'info'" 
              size="small" 
              :show-icon="false" 
              class="mt-2"
            >
              {{ formData.maintenance_mode ? '开启后前台网站将显示维护页面，用户无法正常访问' : '关闭维护模式，前台网站正常运行' }}
            </NAlert>
          </template>
        </NFormItem>
      </NForm>
    </NCard>
  </CommonPage>
</template>

<style scoped>
.mb-4 {
  margin-bottom: 16px;
}

.mt-2 {
  margin-top: 8px;
}
</style>
