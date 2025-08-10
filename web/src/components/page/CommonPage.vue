<template>
  <AppPage :show-footer="showFooter">
    <header v-if="showHeader" mb-15 min-h-45 flex items-center justify-between px-15>
      <slot v-if="$slots.header" name="header" />
      <template v-else>
        <h2 text-22 font-normal text-hex-333 dark:text-hex-ccc>{{ title || route.meta?.title }}</h2>
        <slot name="action" />
      </template>
    </header>

    <n-card class="common-page-card" rounded-10>
      <slot />
    </n-card>
  </AppPage>
</template>

<script setup>
defineProps({
  showFooter: {
    type: Boolean,
    default: false,
  },
  showHeader: {
    type: Boolean,
    default: true,
  },
  title: {
    type: String,
    default: undefined,
  },
})
const route = useRoute()
</script>

<style scoped>
.common-page-card {
  /* 让卡片自然扩展，根据内容自动调整高度 */
  width: 100%;
  min-height: 200px; /* 设置最小高度确保卡片可见 */
  height: auto; /* 自动高度 */
  margin-bottom: 100px; /* 为白色背景框底部添加margin */
}

.common-page-card :deep(.n-card__content) {
  /* 移除高度限制和内部滚动，让内容自然扩展 */
  padding: 16px;
  padding-bottom: 24px; /* 增加底部内边距 */
  overflow: visible;
  min-height: 0;
}
</style>
