<script setup lang="ts">
import { useRouter } from 'vue-router'

const props = defineProps<{
  label: string
  to?: string
}>()

const emit = defineEmits<{
  (e: 'click'): void
}>()

const router = useRouter()

function handleClick() {
  if (props.to) {
    router.push(props.to)
  } else {
    emit('click')
  }
}
</script>

<template>
  <div class="menu-row" @click="handleClick">
    <span class="menu-row-text">
      <slot>{{ label }}</slot>
    </span>
    <span class="menu-row-arrow">›</span>
  </div>
</template>

<style scoped>
.menu-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
  cursor: pointer;
}
.menu-row:active {
  background: #f1f5f9;
}
.menu-row-text {
  flex: 1;
  min-width: 0;
  font-size: 14px;
  color: #111827;
}
.menu-row-arrow {
  font-size: 18px;
  color: #9ca3af;
}
</style>

