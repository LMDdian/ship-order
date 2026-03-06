<script setup lang="ts">
import { computed, ref } from 'vue'
import TabFloatSwitcher from '@/components/TabFloatSwitcher.vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const tabs = [
  { key: '/main', label: '我的订单', to: '/main' },
  { key: '/orders', label: '待发订单', to: '/orders' },
  { key: '/profile', label: '个人中心', to: '/profile' },
]

const isMobileLike = computed(() => {
  if (typeof navigator === 'undefined') return false
  const ua = navigator.userAgent || ''
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(ua)
})

const isTabPage = computed(() => {
  const path = route.path
  return path === '/main' || path === '/orders' || path === '/profile'
})

const swipeStartX = ref(0)
const swipeStartY = ref(0)
const swipeStartTime = ref(0)

function handleTouchStart(e: TouchEvent) {
  if (!isMobileLike.value) return
  if (!isTabPage.value) return
  if (e.touches.length !== 1) return
  const t = e.touches[0]
  if (!t) return
  swipeStartX.value = t.clientX
  swipeStartY.value = t.clientY
  swipeStartTime.value = Date.now()
}

function handleTouchEnd(e: TouchEvent) {
  if (!isMobileLike.value) return
  if (!isTabPage.value) return
  const t = e.changedTouches[0]
  if (!t) return
  const dx = t.clientX - swipeStartX.value
  const dy = t.clientY - swipeStartY.value
  const dt = Date.now() - swipeStartTime.value
  // 水平快速滑动：位移足够、横向位移大于纵向且时间不超过 500ms
  if (Math.abs(dx) < 60 || Math.abs(dx) < Math.abs(dy) || dt > 500) return

  const path = route.path
  if (dx > 0) {
    // 右滑：在三个 Tab 内向左切换（profile -> orders -> main）
    if (path === '/profile') router.push('/orders')
    else if (path === '/orders') router.push('/main')
  } else {
    // 左滑：在三个 Tab 内向右切换（main -> orders -> profile）
    if (path === '/main') router.push('/orders')
    else if (path === '/orders') router.push('/profile')
  }
}
</script>

<template>
  <div
    class="main-layout-root"
    @touchstart.passive="handleTouchStart"
    @touchend.passive="handleTouchEnd"
  >
    <van-nav-bar title="打单发货" />
    <main class="main-layout">
      <TabFloatSwitcher :model-value="route.path" :tabs="tabs" />
      <div class="page-content">
        <router-view style="height: 100%" />
      </div>
    </main>
  </div>
</template>

<style scoped>
.main-layout-root {
  min-height: 100dvh;
  background: #f7f8fa;
}

.main-layout {
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
}

/* 所有子页统一：满宽高、内边距、背景色 */
.page-content {
  flex: 1;
  min-width: 100%;
  min-height: 100%;
  padding: 24px 16px 32px;
  box-sizing: border-box;
}
</style>