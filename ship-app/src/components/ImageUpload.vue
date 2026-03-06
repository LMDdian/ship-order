<script setup lang="ts">
/**
 * ImageUpload - 图片上传组件
 *
 * ---------- 功能概述 ----------
 * 1. 支持从摄像头拍照或从相册/文件中选择图片
 * 2. 使用预签名 URL 通过 PUT 直传 OSS（Content-Type 固定为 application/octet-stream，与后端签名一致）
 * 3. 拍照模式：点「拍照」后，每确认一张即占位并开始上传；若还有空位则自动再次拉起相机（不等待上传完成），直到拍满或用户取消
 * 4. 多张上传为并发：同一批选中的文件会同时发起 PUT，上传过程中可继续拍照/选择
 *
 * ---------- 槽位与索引 ----------
 * - 槽位索引 index 从 0 到 maxCount-1，第 i 张图片使用 presignedUrls[i] 上传
 * - usedCount：当前已“占用”的槽位数量（选完文件即占位，不等上传完成）
 * - remaining = maxCount - usedCount，为 0 时不能再添加，也不会再自动拉相机
 *
 * ---------- Props ----------
 * - maxCount: 最多可上传图片数量（即槽位总数）
 * - presignedUrls: 长度为 maxCount 的预签名 PUT URL 数组，presignedUrls[i] 对应第 i 个槽位
 * - extraHeaders: 可选，PUT 时附加的请求头，须与生成预签名 URL 时一致，否则 OSS 可能 403
 *
 * ---------- 事件 ----------
 * - uploaded({ index, url }): 单张上传成功时触发，index 为槽位索引
 * - failed({ index, url, error }): 单张上传失败时触发
 * - complete(): 本批“选择”对应的所有上传（Promise）都 settle 后触发一次；拍照连续拉相机时，每批选一张会触发一次 complete
 */
import { ref, computed, onUnmounted } from 'vue'

// ---------- Props / Emits ----------

const props = withDefaults(
  defineProps<{
    /** 最多可上传图片数量（槽位总数） */
    maxCount: number
    /** 与 maxCount 等长的预签名 PUT URL 数组，下标 i 对应槽位 i */
    presignedUrls: string[]
    /** 可选：PUT 请求附加头，须与后端生成预签名时一致 */
    extraHeaders?: Record<string, string>
  }>(),
  { extraHeaders: () => ({}) }
)

const emit = defineEmits<{
  (e: 'uploaded', payload: { index: number; url: string }): void
  (e: 'failed', payload: { index: number; url: string; error: unknown }): void
  (e: 'complete'): void
}>()

// ---------- 状态 ----------

/** 已占用的槽位数量（0..maxCount）。选完文件即增加，不等待上传完成；用于计算 remaining、是否继续拉相机 */
const usedCount = ref(0)
/** 当前是否有任意一张处于“上传请求进行中”。用于展示“上传中…”；不影响 canAdd，上传中也可继续拍照 */
const uploading = ref(false)
/** 每个槽位的展示状态：idle | uploading | done | error。由 uploadFile 内根据成功/失败更新 */
const slotStatus = ref<('idle' | 'uploading' | 'done' | 'error')[]>([])
/** 每个槽位的本地预览 URL（URL.createObjectURL(file)），用于显示缩略图；组件卸载时需 revoke 防止内存泄漏 */
const slotPreviewUrls = ref<(string | null)[]>([])

/** 剩余可上传数量 = maxCount - usedCount。为 0 时不能继续添加、不会自动拉相机 */
const remaining = computed(() => Math.max(0, props.maxCount - usedCount.value))
/** 是否允许点击「拍照」/「从相册选择」：仅看 remaining > 0，与 uploading 无关 */
const canAdd = computed(() => remaining.value > 0)

/** 拍照用 <input type="file" capture="environment"> 的 ref，用于 programmatic click 拉相机 */
const cameraInputRef = ref<HTMLInputElement | null>(null)
/** 相册/文件用 <input type="file" multiple> 的 ref，用于 programmatic click 打开选择器 */
const fileInputRef = ref<HTMLInputElement | null>(null)

// ---------- 方法 ----------

/** 确保 slotStatus / slotPreviewUrls 数组长度至少为 maxCount，避免按 index 赋值时越界 */
function ensureSlotStatus() {
  while (slotStatus.value.length < props.maxCount) {
    slotStatus.value.push('idle')
  }
  while (slotPreviewUrls.value.length < props.maxCount) {
    slotPreviewUrls.value.push(null)
  }
}

/** 打开相机：先确保槽位数组、若有空位则触发 cameraInputRef 的 click，移动端会调起摄像头 */
function openCamera() {
  ensureSlotStatus()
  if (!canAdd.value) return
  cameraInputRef.value?.click()
}

/** 打开相册/文件选择：先确保槽位数组、若有空位则触发 fileInputRef 的 click */
function openFilePicker() {
  ensureSlotStatus()
  if (!canAdd.value) return
  fileInputRef.value?.click()
}

defineExpose({
  openCamera,
})

/**
 * 单文件上传：向 signedUrl 发 PUT，body 为 file，请求头含 Content-Type: application/octet-stream 与 extraHeaders。
 * 成功时：emit('uploaded', { index, url })，slotStatus[index] = 'done'
 * 失败时：emit('failed', { index, url, error })，slotStatus[index] = 'error'
 */
async function uploadFile(signedUrl: string, file: File, index: number): Promise<void> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/octet-stream',
    ...props.extraHeaders,
  }

  try {
    const res = await fetch(signedUrl, { method: 'PUT', body: file, headers })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)
    emit('uploaded', { index, url: signedUrl })
    slotStatus.value[index] = 'done'
  } catch (err) {
    slotStatus.value[index] = 'error'
    emit('failed', { index, url: signedUrl, error: err })
  }
}

/** 判断触发 change 的 input 是否为拍照用的那个，用于决定是否在占位后再次拉相机（仅拍照模式连续拉） */
function isCameraInput(input: HTMLInputElement): boolean {
  return input === cameraInputRef.value
}

/**
 * 用户通过相机或相册选择文件后，<input> 的 change 会触发此函数。
 *
 * 步骤简述：
 *  1. 无文件时清空 input 并 return
 *  2. 计算本批可用的槽位数 toUse（受 remaining、本批文件数、presignedUrls 剩余数量限制）
 *  3. 立即占位：usedCount = startIndex + toUse（remaining 立刻减少，便于“继续拉相机”判断）
 *  4. 将本批每个文件对应槽位 slotStatus[index] = 'uploading'，并并发执行 uploadFile（不 await 单张），收集 Promise
 *  5. 清空 input.value，以便同一 input 再次触发 change
 *  6. 若来自相机且占位后 stillHasSlot，则 setTimeout 后再次 openCamera（不等待本批上传完成）
 *  7. await Promise.allSettled(本批)，然后在 finally 里 uploading = false 并 emit('complete')
 */
async function onFileSelected(e: Event) {
  const input = e.target as HTMLInputElement
  const files = input.files
  if (!files?.length) {
    input.value = ''
    return
  }

  ensureSlotStatus()
  /** 是否由“拍照” input 触发（拍照时会根据空位再拉一次相机） */
  const fromCamera = isCameraInput(input)

  /** 本批开始占用的槽位起始下标（即当前 usedCount 的值） */
  const startIndex = usedCount.value
  const urls = props.presignedUrls
  const maxSlots = props.maxCount

  /** 本批最多可用槽位数 = 总槽位 - 已占用；再与文件数、剩余 URL 数取 min 得到本批实际使用数 */
  const availableSlots = Math.max(0, maxSlots - startIndex)
  const toUse = Math.min(availableSlots, files.length, urls.length - startIndex)

  if (toUse <= 0) {
    input.value = ''
    emit('complete')
    return
  }

  /** 占位：本批占用 [reservedStart, reservedEnd)，usedCount 立即增加，remaining 立即减少 */
  const reservedStart = startIndex
  const reservedEnd = reservedStart + toUse
  usedCount.value = reservedEnd

  uploading.value = true

  /** 本批并发上传：为每个槽位生成本地预览 URL（用于展示缩略图及后续“保存到设备”），并并发上传 */
  const uploadPromises: Promise<void>[] = []
  for (let i = 0; i < toUse; i++) {
    const index = reservedStart + i
    slotStatus.value[index] = 'uploading'
    slotPreviewUrls.value[index] = URL.createObjectURL(files[i])
    uploadPromises.push(uploadFile(urls[index], files[i], index))
  }

  /** 清空 input，否则同一 input 再次选择时 change 可能不触发（尤其部分浏览器/机型） */
  input.value = ''

  /** 拍照模式且占位后仍有空位：延迟后“再次拉相机”。 */
  const stillHasSlot = remaining.value > 0
  if (fromCamera && stillHasSlot) {
      document.getElementById('btn-camera')?.click()

  }

  /** 等待本批所有上传结束（成功或失败都算），然后关闭“上传中”状态并通知 complete */
  try {
    await Promise.allSettled(uploadPromises)
  } finally {
    uploading.value = false
    emit('complete')
  }
}

onUnmounted(() => {
  slotPreviewUrls.value.forEach((url: string | null) => {
    if (url) URL.revokeObjectURL(url)
  })
})
</script>

<template>
  <div class="image-upload">
    <!-- 拍照用 input：通过 ref 触发 click，capture 在移动端调起后摄 -->
    <input
      ref="cameraInputRef"
      type="file"
      accept="image/*"
      capture="environment"
      class="hidden-input"
      @change="onFileSelected"
    />
    <!-- 相册/文件用 input：无 capture，支持 multiple；同一 change 可能多张，按槽位顺序并发上传 -->
    <input
      ref="fileInputRef"
      type="file"
      accept="image/*"
      multiple
      class="hidden-input"
      @change="onFileSelected"
    />

    <!-- 已选图片槽位列表：上传中显示占位，上传完成显示缩略图 + 保存到本地按钮 -->
    <div class="slot-list" v-if="usedCount > 0">
      <div
        v-for="(_, index) in usedCount"
        :key="index"
        class="slot-item"
        :class="slotStatus[index]"
      >
        <template v-if="slotStatus[index] === 'uploading'">
          <div class="slot-placeholder">
            <span class="slot-placeholder-text">上传中…</span>
          </div>
        </template>
        <template v-else-if="slotStatus[index] === 'done' && slotPreviewUrls[index]">
          <img :src="slotPreviewUrls[index]" class="slot-image" alt="" />
        </template>
        <template v-else-if="slotStatus[index] === 'error'">
          <div class="slot-placeholder slot-error">
            <span class="slot-placeholder-text">上传失败</span>
          </div>
        </template>
      </div>
    </div>

    <!-- 操作区：canAdd 为 false（无剩余槽位）时按钮禁用 -->
    <div class="actions">
      <button id="btn-camera" type="button" class="btn btn-camera" :disabled="!canAdd" @click="openCamera">
        拍照
      </button>
      <button type="button" class="btn btn-gallery" :disabled="!canAdd" @click="openFilePicker">
        从相册选择
      </button>
    </div>

    <!-- 已占用槽位数量与上传中状态：remaining < maxCount 时显示“已用 x / maxCount”；uploading 为 true 时追加“，上传中…” -->
    <p v-if="remaining < maxCount" class="hint">
      已用 {{ usedCount }} / {{ maxCount }} 个位置
      <span v-if="uploading">，上传中…</span>
    </p>
  </div>
</template>

<style scoped>
/* 隐藏两个 file input，由下方按钮通过 ref 触发 click，避免露出原生控件 */
.hidden-input {
  position: absolute;
  width: 0;
  height: 0;
  opacity: 0;
  pointer-events: none;
}

.image-upload {
  padding: 12px 0;
}

/* 已选图片槽位列表：网格展示，每项为占位或缩略图 */
.slot-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.slot-item {
  position: relative;
  aspect-ratio: 1;
  border-radius: 8px;
  overflow: hidden;
  background: #f0f0f0;
}

.slot-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
}

.slot-placeholder-text {
  font-size: 12px;
}

.slot-item.uploading .slot-placeholder {
  background: #e8e8e8;
}

.slot-error .slot-placeholder {
  background: #ffebee;
  color: #c91f37;
}

.slot-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

/* 拍照 / 相册 两个按钮的容器 */
.actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.btn {
  padding: 10px 20px;
  border-radius: 8px;
  border: 1px solid #ddd;
  background: #fff;
  color: #111;
  font-size: 15px;
  cursor: pointer;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-camera {
  background: #f5f5f5;
}

.btn-gallery {
  background: #f5f5f5;
}

.btn-save-all {
  background: #4caf50;
  color: #fff;
  border-color: #4caf50;
}

/* 底部“已用 x / maxCount”及“上传中…”的提示文案 */
.hint {
  margin-top: 8px;
  font-size: 13px;
  color: #666;
}
</style>
