<script setup lang="ts">
/**
 * TabFloatSwitcher - 悬浮 Tab 切换器
 *
 * 底部固定悬浮按钮 + 下拉面板，用于在多个 Tab 间切换。
 * 父组件通过 v-model 绑定当前选中的 tab key，选择后通过 update:modelValue 回写，
 * 同时支持为每个 Tab 配置跳转路径，点击时自动使用 vue-router 跳转到对应页面。
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

/** 单个 Tab 项：
 *  - key：用于标识与 v-model 绑定，以及当前激活态判断
 *  - label：展示文案
 *  - to（可选）：点击时跳转的路由地址；未提供时默认使用 key 作为路径
 */
export interface TabItem {
  key: string
  label: string
  to?: string
}

const props = defineProps<{
  /** Tab 选项列表 */
  tabs: TabItem[]
  /** 当前选中的 Tab 的 key，与 v-model 双向绑定 */
  modelValue: string
}>()

const emit = defineEmits<{
  /** 用户选择某项时发出，传入选中的 key，父组件用 v-model 接收 */
  'update:modelValue': [value: string]
}>()

const router = useRouter()

/** 下拉面板是否展开 */
const isDropdownOpen = ref(false)
/** 悬浮容器 DOM 引用，用于判断点击是否在组件内部（点击外部时关闭下拉） */
const wrapperRef = ref<HTMLDivElement | null>(null)

/** 根据当前 modelValue 从 tabs 中取对应的 label，显示在按钮上 */
const activeLabel = computed(() => {
  const current = props.tabs.find((t: TabItem) => t.key === props.modelValue)
  return current ? current.label : ''
})

/** 点击悬浮按钮时切换下拉面板的显示/隐藏 */
const toggleDropdown = () => {
  isDropdownOpen.value = !isDropdownOpen.value
}

/** 选择某一项：
 *  - 向父组件发出新值（更新当前激活 Tab）
 *  - 若配置了 to，则使用 vue-router 跳转到对应路由；否则默认按 key 作为 path 进行跳转
 *  - 关闭下拉面板
 */
const selectTab = (tab: TabItem) => {
  emit('update:modelValue', tab.key)
  const targetPath = tab.to ?? tab.key
  if (targetPath) {
    router.push(targetPath).catch(() => {
      // 忽略重复导航等非致命错误
    })
  }
  isDropdownOpen.value = false
}

/** 点击发生在组件外时关闭下拉（用于 document 的 click 监听） */
const handleClickOutside = (e: MouseEvent) => {
  if (wrapperRef.value && !wrapperRef.value.contains(e.target as Node)) {
    isDropdownOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <!-- 固定底部居中容器，ref 用于点击外部检测 -->
  <div class="tab-float-wrapper" ref="wrapperRef">
    <!-- 主按钮：展示当前 Tab 文案 + 箭头，点击切换下拉 -->
    <button type="button" class="float-btn" @click="toggleDropdown">
      <span v-if="activeLabel">{{ activeLabel }}</span>
      <!-- 箭头：展开时旋转 180° -->
      <svg
        class="arrow-icon"
        :class="{ rotate: isDropdownOpen }"
        viewBox="0 0 1024 1024"
        width="16"
        height="16"
      >
        <path
          d="M858.5 896a32 32 0 0 1-22.6 7.4H188.1a32 32 0 0 1-22.6-9.4c-10.5-10.5-10.5-27.5 0-38l352-352a32 32 0 0 1 45.2 0l352 352c10.5 10.5 10.5 27.5 0 38a32 32 0 0 1-22.6 9.4z"
        />
      </svg>
    </button>

    <!-- 下拉选项列表，仅展开时显示；当前项高亮 -->
    <div v-show="isDropdownOpen" class="dropdown-panel">
      <div
        v-for="tab in tabs"
        :key="tab.key"
        class="dropdown-item"
        :class="{ active: modelValue === tab.key }"
        @click="selectTab(tab)"
      >
        {{ tab.label }}
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 悬浮容器：固定底部居中，保证浮在页面最上层 */
.tab-float-wrapper {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 999;
}

/* 主按钮：胶囊形，黑白灰配色 */
.float-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background-color: #ffffff;
  color: #111111;
  border: none;
  border-radius: 30px;
  font-size: 16px;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
  transition: all 0.2s ease;
}

.float-btn:hover {
  background-color: #f2f2f2;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.3);
}

/* 箭头图标：展开时旋转 */
.arrow-icon {
  transition: transform 0.2s ease;
}

.arrow-icon.rotate {
  transform: rotate(180deg);
}

/* 下拉面板：在按钮上方、水平居中，带圆角和阴影（黑白灰） */
.dropdown-panel {
  position: absolute;
  bottom: 60px;
  left: calc(50% - 90px);
  width: 180px;
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
  overflow: hidden;
  animation: fadeIn 0.2s ease;
}

/* 下拉单项 */
.dropdown-item {
  padding: 12px 16px;
  font-size: 15px;
  color: #333333;
  cursor: pointer;
  transition: background-color 0.2s, color 0.2s;
}

.dropdown-item:hover {
  background-color: #f2f2f2;
}

/* 当前选中项高亮：浅灰背景 + 深色文字 */
.dropdown-item.active {
  background-color: #e0e0e0;
  color: #111111;
  font-weight: 600;
}

/* 下拉出现时的淡入 + 上移动画 */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
