/** 重置样式 */
import '@/styles/reset.css'
import 'uno.css'
import '@/styles/global.scss'

import { createApp } from 'vue'
import { setupRouter } from '@/router'
import { setupStore } from '@/store'
import App from './App.vue'
import { setupDirectives } from './directives'
import { useResize } from '@/utils'
import i18n from '~/i18n'

// 设置被动事件监听器以提高性能和消除警告
function setupPassiveEventListeners() {
  // 为常见的滚动相关事件添加被动监听器
  const passiveEvents = ['wheel', 'mousewheel', 'touchstart', 'touchmove']

  passiveEvents.forEach(eventType => {
    document.addEventListener(eventType, () => {}, { passive: true })
  })

  // 针对Naive UI的滚轮事件优化
  const originalAddEventListener = EventTarget.prototype.addEventListener
  EventTarget.prototype.addEventListener = function(type, listener, options) {
    // 只对滚轮事件进行被动处理，避免影响其他事件
    if (type === 'wheel' && typeof options !== 'object') {
      options = { passive: true }
    } else if (type === 'wheel' && typeof options === 'object' && options.passive === undefined) {
      options = { ...options, passive: true }
    }
    return originalAddEventListener.call(this, type, listener, options)
  }
}

async function setupApp() {
  // 设置被动事件监听器
  setupPassiveEventListeners()

  const app = createApp(App)

  setupStore(app)

  await setupRouter(app)
  setupDirectives(app)
  app.use(useResize)
  app.use(i18n)
  app.mount('#app')
}

setupApp()
