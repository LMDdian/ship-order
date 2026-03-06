<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { apiRequest } from '@/services/http'
import { showImagePreview, showToast } from 'vant'

import PageHeader from '@/components/PageHeader.vue'

const route = useRoute()
const token = computed(() => route.params.token as string)

const order = ref<any | null>(null)
const loading = ref(true)
const error = ref('')

const slotContents = computed(() => (order.value?.slot_contents as any[]) || [])

function displayText(slot: any): string {
  return slot?.text ?? '—'
}

function slotImages(slot: any): { id: number; url: string }[] {
  return slot?.images ?? []
}

function previewImages(urls: string[], startIndex: number) {
  if (!urls?.length) return
  showImagePreview({ images: urls, startPosition: startIndex })
}

async function loadSharedOrder() {
  if (!token.value) {
    error.value = '链接无效'
    loading.value = false
    return
  }
  loading.value = true
  error.value = ''
  try {
    order.value = await apiRequest<any>(`/api/share/${token.value}/`, { auth: false })
  } catch (err: any) {
    const msg = (err as Error)?.message || '加载失败'
    error.value = msg
    if (msg.includes('过期')) {
      showToast('分享链接已过期')
    } else {
      showToast(msg)
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadSharedOrder()
})
</script>

<template>
  <div class="share-page">
    <header class="share-header">
      <h1 class="share-title">订单分享</h1>
    </header>
    <template v-if="loading">
      <div class="placeholder">加载中…</div>
    </template>
    <template v-else-if="error">
      <div class="error-msg">{{ error }}</div>
    </template>
    <template v-else-if="order">
      <div class="form">
        <PageHeader title="快递单号">
          <h2>{{ order.tracking_number || '—' }}</h2>
        </PageHeader>
        <div class="slots-block">
          <span class="slots-title">订单内容</span>
          <div v-if="!slotContents.length" class="slots-empty">暂无内容</div>
          <div v-else class="slots-list">
            <div
              v-for="(slot, i) in slotContents"
              :key="slot.slot_index + '-' + i"
              class="slot-card"
            >
              <div class="slot-label">{{ slot.name }}</div>
              <template v-if="slot.type === 'text'">
                <div class="slot-text-readonly">{{ displayText(slot) }}</div>
              </template>
              <template v-else-if="slot.type === 'image'">
                <div class="slot-images">
                  <div
                    v-for="(img, idx) in slotImages(slot)"
                    :key="img.id"
                    class="slot-image-item slot-image-clickable"
                    @click="previewImages(slotImages(slot).map((i) => i.url), idx)"
                  >
                    <img :src="img.url" class="slot-image-preview" alt="" loading="lazy" />
                  </div>
                  <span v-if="!slotImages(slot).length" class="slot-no-images">暂无图片</span>
                </div>
              </template>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.share-page {
  min-height: 100vh;
  background: #f7f8fa;
  padding: 0 0 24px;
}

.share-header {
  padding: 16px;
  background: #fff;
  border-bottom: 1px solid #eee;
}

.share-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #111827;
}

.placeholder,
.error-msg {
  padding: 24px;
  text-align: center;
  color: #64748b;
}

.error-msg {
  color: #c91f37;
}

.form {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field label {
  font-size: 14px;
  font-weight: 500;
  color: #334155;
}

.readonly-value {
  font-size: 14px;
  color: #111827;
  padding: 10px 0;
}

.slots-block {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.slots-title {
  font-size: 15px;
  font-weight: 600;
  color: #111827;
}

.slots-empty {
  padding: 16px;
  text-align: center;
  color: #94a3b8;
  font-size: 14px;
}

.slots-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.slot-card {
  padding: 14px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
}

.slot-label {
  font-size: 13px;
  font-weight: 500;
  color: #64748b;
  margin-bottom: 8px;
}

.slot-text-readonly {
  font-size: 14px;
  color: #334155;
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
}

.slot-images {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 10px;
}

.slot-image-item {
  aspect-ratio: 1;
  border-radius: 8px;
  overflow: hidden;
  background: #f1f5f9;
}

.slot-image-clickable {
  cursor: pointer;
}

.slot-image-preview {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.slot-no-images {
  font-size: 13px;
  color: #94a3b8;
}
</style>
