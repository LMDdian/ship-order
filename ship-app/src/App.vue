<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const isMobileLike = computed(() => {
  if (typeof navigator === 'undefined') return false
  const ua = navigator.userAgent || ''
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(ua)
})

const startX = ref(0)
const startY = ref(0)
const startTime = ref(0)
const hasActiveSwipe = ref(false)

const disableGlobalSwipe = computed(() => {
  const path = router.currentRoute.value.path
  // 在主页 / 订单 / 个人 三个页面内，使用各自页面的局部手势，不启用全局前进/后退
  return path === '/main' || path === '/orders' || path === '/profile'
})

function onTouchStart(e: TouchEvent) {
  if (!isMobileLike.value) return
  if (disableGlobalSwipe.value) return
  if (e.touches.length !== 1) return
  const t = e.touches[0]
  if (!t) return
  startX.value = t.clientX
  startY.value = t.clientY
  startTime.value = Date.now()
  hasActiveSwipe.value = true
}

function onTouchEnd(e: TouchEvent) {
  if (!isMobileLike.value) return
  if (disableGlobalSwipe.value) return
  if (!hasActiveSwipe.value) return
  const t = e.changedTouches[0]
  if (!t) return

  const dx = t.clientX - startX.value
  const dy = t.clientY - startY.value
  const dt = Date.now() - startTime.value

  // 水平滑动判定：位移足够、横向位移大于纵向，且滑动时间不过长（避免慢拖动误触）
  if (Math.abs(dx) < 60 || Math.abs(dx) < Math.abs(dy) || dt > 500) return

  if (dx > 0) {
    // 右滑：后退
    router.back()
  } else {
    // 左滑：前进（若无前进历史则不会有变化）
    router.forward()
  }
  hasActiveSwipe.value = false
}
</script>

<template>
  <div class="app-root" @touchstart.passive="onTouchStart" @touchend.passive="onTouchEnd">
    <router-view />
  </div>
</template>
