<template>
  <AppPage :show-footer="false">
    <div flex-1>
      <n-card rounded-10>
        <div flex items-center justify-between>
          <div flex items-center>
            <img rounded-full width="60" :src="userStore.avatar" />
            <div ml-10>
              <p text-20 font-semibold>
                {{ $t('views.workbench.text_hello', { username: userStore.name }) }}
              </p>
              <p mt-5 text-14 op-60>{{ $t('views.workbench.text_welcome') }}</p>
            </div>
          </div>
          <!-- 统计数据区域已清除 -->
        </div>
      </n-card>

      <!-- 新增：公告卡片 -->
      <n-card rounded-10 mt-4 v-if="announcements.length > 0">
        <template #header>
          <div flex items-center>
            <TheIcon icon="material-symbols:campaign-outline" class="mr-2 text-blue-500" />
            <span font-semibold>公告通知</span>
          </div>
        </template>
        <div>
          <template v-for="(announcement, index) in announcements" :key="announcement.id">
            <div class="announcement-item mb-10">
              <h4 class="announcement-title mb-4 text-gray-800" style="font-size: 14px !important; font-weight: 400 !important; line-height: 1.2;">
                {{ announcement.title }}
              </h4>
              <div 
                class="announcement-content text-gray-600 leading-relaxed mb-3" 
                style="font-size: 16px !important; line-height: 1.6;"
                v-html="announcement.content"
              ></div>
              <div class="announcement-meta flex items-center justify-between text-lg text-gray-600 mt-3">
                <span class="text-gray-700" style="font-size: 14px !important; font-weight: 400 !important;">{{ formatDate(announcement.created_at) }}</span>
                <n-tag 
                  size="large" 
                  :type="announcement.announcement_type === 'agent' ? 'info' : 'default'"
                  class="px-4 py-2"
                  style="font-size: 14px !important; font-weight: 400 !important;"
                >
                  {{ announcement.announcement_type === 'agent' ? '代理公告' : '系统公告' }}
                </n-tag>
              </div>
            </div>
            
            <!-- 虚线分割线 -->
            <div 
              v-if="index < announcements.length - 1" 
              class="border-t border-dashed border-gray-300 my-12"
            ></div>
          </template>
        </div>
      </n-card>

      <!-- 项目展示区域已清除 -->
    </div>
  </AppPage>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useUserStore } from '@/store'
import { useI18n } from 'vue-i18n'
import { formatDate } from '@/utils'
import api from '@/api'
import TheIcon from '@/components/icon/TheIcon.vue'

const { t } = useI18n({ useScope: 'global' })

const userStore = useUserStore()
const announcements = ref([])

// 获取公告
const fetchAnnouncements = async () => {
  try {
    const res = await api.getActiveAnnouncements()
    if (res.code === 200) {
      announcements.value = res.data || []
    }
  } catch (error) {
    console.error('获取公告失败:', error)
    // 静默处理错误，不影响其他功能
  }
}

onMounted(() => {
  fetchAnnouncements()
})
</script>
