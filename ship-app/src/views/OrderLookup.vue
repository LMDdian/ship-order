<script setup lang="ts">
import { computed, ref } from 'vue'
import { apiRequest } from '@/services/http'
import { showImagePreview, showToast } from 'vant'

const keyInput = ref('')
const trackingInput = ref('')
const order = ref<any | null>(null)
const loading = ref(false)
const error = ref('')
const searched = ref(false)

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

async function search() {
  const key = keyInput.value.trim()
  const tracking = trackingInput.value.trim()
  if (!key || !tracking) {
    showToast('请填写密钥和快递单号')
    return
  }
  loading.value = true
  error.value = ''
  order.value = null
  searched.value = true
  try {
    const params = new URLSearchParams({ key, tracking_number: tracking })
    order.value = await apiRequest<any>(`/api/public/order-by-tracking/?${params}`, {
      auth: false,
    })
  } catch (err: any) {
    const msg = (err as Error)?.message || '查询失败'
    error.value = msg
    showToast(msg)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="lookup-page">
    <header class="lookup-header">
      <h1 class="lookup-title">快递单号查询</h1>
      <p class="lookup-desc">请输入对方提供的密钥与完整快递单号查看订单（只读）</p>
    </header>

    <div class="form">
      <div class="field">
        <label class="label">密钥</label>
        <input v-model="keyInput" type="text" class="input" placeholder="请输入密钥" />
      </div>
      <div class="field">
        <label class="label">快递单号</label>
        <input v-model="trackingInput" type="text" class="input" placeholder="请输入完整快递单号" />
      </div>
      <button type="button" class="btn-query" :disabled="loading" @click="search">
        {{ loading ? '查询中…' : '查询' }}
      </button>
    </div>

    <template v-if="searched && !loading">
      <div v-if="error" class="error-msg">{{ error }}</div>
      <template v-else-if="order">
        <div class="result-block">
          <div class="result-header">快递单号：{{ order.tracking_number || '—' }}</div>
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
    </template>
  </div>
</template>

<style scoped>
.lookup-page {
  min-height: 100vh;
  background: #f7f8fa;
  padding: 0 0 24px;
}

.lookup-header {
  padding: 20px 16px;
  background: #fff;
  border-bottom: 1px solid #eee;
}

.lookup-title {
  margin: 0 0 8px;
  font-size: 18px;
  font-weight: 600;
  color: #111827;
}

.lookup-desc {
  margin: 0;
  font-size: 13px;
  color: #64748b;
}

.form {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.label {
  font-size: 14px;
  font-weight: 500;
  color: #334155;
}

.input {
  padding: 10px 12px;
  font-size: 14px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #fff;
  box-sizing: border-box;
}

.btn-query {
  padding: 12px 16px;
  font-size: 16px;
  font-weight: 500;
  color: #fff;
  background: #111827;
  border: none;
  border-radius: 10px;
  cursor: pointer;
}

.btn-query:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-query:active:not(:disabled) {
  background: #000;
}

.error-msg {
  padding: 16px;
  margin: 0 16px;
  text-align: center;
  color: #c91f37;
  font-size: 14px;
  background: #fef2f2;
  border-radius: 8px;
}

.result-block {
  padding: 16px;
  margin: 0 16px;
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.result-header {
  font-size: 15px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 12px;
}

.slots-block {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.slots-title {
  font-size: 14px;
  font-weight: 600;
  color: #64748b;
}

.slots-empty {
  padding: 12px 0;
  font-size: 13px;
  color: #94a3b8;
}

.slots-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.slot-card {
  padding: 12px;
  background: #f8fafc;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
}

.slot-label {
  font-size: 13px;
  font-weight: 500;
  color: #64748b;
  margin-bottom: 6px;
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
  grid-template-columns: repeat(auto-fill, minmax(80px, 1fr));
  gap: 8px;
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
