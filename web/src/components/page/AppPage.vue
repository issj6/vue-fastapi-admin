<template>
  <transition name="fade-slide" mode="out-in" appear>
    <section class="app-page-container cus-scroll-y wh-full flex-col bg-[#f5f6fb] p-15 pb-30 dark:bg-hex-121212">
      <slot />
      <AppFooter v-if="showFooter" mt-15 />
      <n-back-top :bottom="20" />
    </section>
  </transition>
</template>

<script setup>
defineProps({
  showFooter: {
    type: Boolean,
    default: false,
  },
})
</script>

<style scoped>
.app-page-container {
  /* 确保容器有明确的高度和滚动行为 */
  height: 100%;
  max-height: 100vh;
  overflow-y: auto;
  overflow-x: hidden;
  /* 确保内容可以完全显示，包括底部空间 */
  box-sizing: border-box;
}

/* 确保滚动容器内的内容有足够的空间 */
.app-page-container > * {
  flex-shrink: 0;
}
</style>
