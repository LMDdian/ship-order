<script setup lang="ts">
defineProps<{
  title: string
  hint?: string
}>()
</script>

<template>
  <header class="page-header">
    <div class='header'>
      <h1 class="page-header-title">{{ title }}</h1>
      <slot />
    </div>

    <p v-if="hint" class="page-header-hint">{{ hint }}</p>
  </header>
</template>

<style scoped>
.page-header {
  margin-bottom: 16px;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.page-header-title {
  margin: 0 0 4px;
  font-size: 20px;
  font-weight: 600;
  color: #111827;
}

.page-header-hint {
  margin: 4px 0 0;
  font-size: 14px;
  color: #666;
}
</style>
