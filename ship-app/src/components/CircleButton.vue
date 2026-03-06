<script setup lang="ts">
/**
 * CircleButton - 通用圆形 FAB 按钮
 *
 * 用途：
 *  - 作为悬浮操作按钮使用（放在 ButtonGroup 等容器中）
 *  - 通过插槽自定义中间的文字或图标（例如 “退”）
 *
 * 配色：
 *  - color = "black"（默认）：黑底白字
 *  - color = "red"：红底白字
 */
import { computed } from 'vue'

const props = defineProps<{
  /** 按钮背景色：黑色或红色，默认黑色 */
  color?: 'black' | 'red'
}>()

const emit = defineEmits<{
  (e: 'click', event: MouseEvent): void
}>()

/** 根据 color 计算背景色 */
const backgroundColor = computed(() => {
  if (props.color === 'red') {
    return '#c91f37' // 赭红
  }
  return '#000000'
})

const handleClick = (e: MouseEvent) => {
  emit('click', e)
}
</script>

<template>
  <button
    type="button"
    class="circle-btn"
    :style="{ backgroundColor }"
    @click="handleClick"
  >
    <slot />
  </button>
</template>

<style scoped>
/* 圆形 FAB 按钮，居中显示插槽内容（文字/图标） */
.circle-btn {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  border: none;
  outline: none;

  color: #ffffff;
  font-size: 20px;
  font-weight: 600;

  display: flex;
  align-items: center;
  justify-content: center;

  cursor: pointer;
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3);
  transition: transform 0.1s ease, box-shadow 0.1s ease;
}

.circle-btn:active {
  transform: scale(0.96);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}
</style>

