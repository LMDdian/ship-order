<script setup lang="ts">
/**
 * 已完成订单展示卡片：上图为商品图，下为三条文字。
 * - 前两条由订单样式决定（如标题、描述等）
 * - 第三条固定为快递单号
 */
const props = defineProps<{
  /** 主图 URL（可为空，无图时占位） */
  imageUrl?: string | null
  /** 第一行文字（样式决定） */
  line1?: string | null
  /** 第二行文字（样式决定） */
  line2?: string | null
  /** 快递单号，展示在第三行 */
  trackingNumber?: string | null
  /** 该订单图片占用空间（字节），用于展示 */
  storageBytes?: number | null
}>()

function formatStorage(bytes: number | undefined | null): string {
  if (bytes == null || bytes <= 0) return '—'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
}
</script>

<template>
  <div class="order-card">
    <div class="order-card-image-wrap">
      <img
        v-if="imageUrl"
        :src="imageUrl"
        class="order-card-image"
        alt=""
        loading="lazy"
      />
      <div v-else class="order-card-image-placeholder">
        暂无图片
      </div>
    </div>
    <div class="order-card-body">
      <p v-if="line1" class="order-card-line order-card-line-1">{{ line1 }}</p>
      <p v-if="line2" class="order-card-line order-card-line-2">{{ line2 }}</p>
      <p class="order-card-line order-card-line-tracking">
        <span class="order-card-tracking">{{ trackingNumber || '—' }}</span>
      </p>
      <p v-if="props.storageBytes != null && props.storageBytes > 0" class="order-card-line order-card-storage">
        <span class="order-card-storage-label">图片占用</span>
        <span class="order-card-storage-value">{{ formatStorage(props.storageBytes) }}</span>
      </p>
    </div>
  </div>
</template>

<style scoped>
.order-card {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.08);
}

.order-card-image-wrap {
  width: 100%;
  aspect-ratio: 1;
  background: #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: center;
}

.order-card-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.order-card-image-placeholder {
  font-size: 13px;
  color: #94a3b8;
}

.order-card-body {
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.order-card-line {
  margin: 0;
  font-size: 14px;
  color: #334155;
  line-height: 1.4;
  word-break: break-all;
}

.order-card-line-1 {
  font-weight: 600;
  color: #111827;
}

.order-card-line-2 {
  color: #64748b;
}

.order-card-line-tracking {
  display: flex;
  align-items: baseline;
  gap: 6px;
  margin-top: 4px;
  padding-top: 8px;
  border-top: 1px solid #e2e8f0;
}

.order-card-label {
  flex-shrink: 0;
  font-size: 13px;
  color: #64748b;
}

.order-card-tracking {
  font-size: 13px;
  font-weight: 500;
  color: #0f172a;
}

.order-card-storage {
  margin-top: 4px;
  font-size: 12px;
  color: #64748b;
}

.order-card-storage-label {
  margin-right: 6px;
}

.order-card-storage-value {
  font-weight: 500;
  color: #475569;
}
</style>
