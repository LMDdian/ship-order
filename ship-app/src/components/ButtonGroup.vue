<script setup lang="ts">
/**
 * ButtonGroup - 悬浮按钮容器
 *
 * 用于放置一个或多个 FAB 按钮，整体固定在页面右侧，
 * 默认垂直位置在视口高度的约 0.618 处。
 *
 * 当前版本只负责布局，不关心内部按钮的形态，
 * 通过默认插槽传入任意按钮即可。
 *
 * 预留 props（如 direction、gap、topRatio 等）后续可扩展。
 */
import { computed } from 'vue'

const props = defineProps<{
  /** 不透明度（0–100），默认 100 表示完全不透明 */
  opacity?: number
}>()

const styleOpacity = computed(() => {
  const value = typeof props.opacity === 'number' ? props.opacity : 90
  const clamped = Math.min(100, Math.max(0, value))
  return clamped / 100
})
</script>

<template>
  <!-- 固定在页面右侧、相对视口高度 0.618 位置 -->
  <div class="button-group" :style="{ opacity: styleOpacity }">
    <slot />
  </div>
</template>

<style scoped>
/* 悬浮按钮组容器：固定在右侧，垂直方向约为视口高度 61.8% 处 */
.button-group {
  position: fixed;
  right: 20px;
  top: 55.8vh; /* 0.618 * 100vh，黄金分割位置偏上 */
  transform: translateY(-50%); /* 让按钮组整体居中对齐该位置 */
  z-index: 1000;

  display: flex;
  flex-direction: column; /* 默认垂直排列多个 FAB */
  gap: 30px; /* FAB 之间的间距 */
}
</style>

