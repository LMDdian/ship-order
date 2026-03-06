<script setup lang="ts">
/**
 * BarcodeScanner (Quagga 版) - Code128 条形码扫码弹窗
 * - open=true 时初始化 Quagga + 打开摄像头
 * - 扫到条码后触发 @scanned，并自动 @close
 */
import { ref, watch, onUnmounted, nextTick } from 'vue'
import QuaggaLib from 'quagga'  // 对应 quagga 包

// 兼容 quagga 在 CJS / ESM 下的不同导出方式
const Quagga: any = (QuaggaLib as any).default || QuaggaLib

const props = defineProps<{
  /** 是否显示扫码界面 */
  open: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'scanned', code: string): void
}>()

const containerRef = ref<HTMLDivElement | null>(null)
const errorMessage = ref('')
const scanning = ref(false)

// 用于做多帧稳定识别（同一个码识别多次才算成功）
const detectionBuffer: Record<string, number> = {}

function resetDetectionBuffer() {
  Object.keys(detectionBuffer).forEach((k) => {
    delete detectionBuffer[k]
  })
}

function isMediaError(msg: string): boolean {
  return msg.includes('getUseMedia') || msg.includes('getUserMedia')
}

function initQuagga() {
  if (!containerRef.value) return

  errorMessage.value = ''
  scanning.value = true
  resetDetectionBuffer()

  Quagga.init(
    {
      inputStream: {
        name: 'Live',
        type: 'LiveStream',
        target: containerRef.value,      // 使用容器 div 承载 video/canvas
        constraints: {
          facingMode: 'environment',     // 后置摄像头
          focusMode: "continuous",
          // width: { min: 640, ideal: 1024 },
          // height: { min: 480, ideal: 720 },
        },
      },
      locator: {
        halfSample: true,
        halfSampleThreshold: 0.7,
        patchSize: 'medium', // 官方推荐：medium + halfSample，兼顾速度和准确率

      },
      decoder: {
        // 只识别 Code128
        readers: ['code_128_reader'],
        multiple: false,
      },
      locate: true,
      numOfWorkers: typeof navigator !== 'undefined' && (navigator as any).hardwareConcurrency
        ? (navigator as any).hardwareConcurrency
        : 2,
      frequency: 10,
    },
    (err) => {
      if (err) {
        console.error(err)
        const msg = (err && (err as Error).message) ? String((err as Error).message) : ''
        errorMessage.value = msg || '初始化摄像头失败'
        scanning.value = false
        if (isMediaError(msg)) {
          emit('close')
        }
        return
      }
      try {
        attachOnDetected()
        Quagga.start()
      } catch (e) {
        const msg = (e && (e as Error).message) ? String((e as Error).message) : ''
        errorMessage.value = msg || '启动摄像头失败'
        scanning.value = false
        if (isMediaError(msg)) {
          emit('close')
        }
      }
    },
  )
}

function attachOnDetected() {
  Quagga.onDetected((result) => {
    const code = result?.codeResult?.code
    if (!code) return

    const count = (detectionBuffer[code] || 0) + 1
    detectionBuffer[code] = count

    console.log('[BarcodeScanner] candidate code:', code, 'x', count)

    // 需要多帧识别到同一个码才算成功（2 帧即可），兼顾短码和长码
    if (count < 2) return

    // 只取第一次识别结果，立即停止
    stopQuagga()
    emit('scanned', code)
    emit('close')
  })
}

function stopQuagga() {
  try {
    Quagga.offDetected()  // 清理回调
  } catch {}
  try {
    Quagga.stop()
  } catch {}
  resetDetectionBuffer()
  scanning.value = false
}

function onGlobalError(event: ErrorEvent) {
  const msg = String(event?.message || (event as any)?.error?.message || '')
  if (!isMediaError(msg)) return
  stopQuagga()
  emit('close')
  if (typeof window !== 'undefined') {
    window.removeEventListener('error', onGlobalError)
  }
}

watch(
  () => props.open,
  (open: boolean) => {
    if (open) {
      if (typeof window !== 'undefined') {
        window.addEventListener('error', onGlobalError)
      }
      nextTick(() => {
        initQuagga()
      })
    } else {
      if (typeof window !== 'undefined') {
        window.removeEventListener('error', onGlobalError)
      }
      stopQuagga()
    }
  },
  { immediate: true },
)

onUnmounted(() => {
  if (typeof window !== 'undefined') {
    window.removeEventListener('error', onGlobalError)
  }
  stopQuagga()
})

function handleClose() {
  emit('close')
}
</script>

<template>
  <Teleport to="body">
    <div v-if="open" class="scanner-overlay">
      <div class="scanner-backdrop" @click="handleClose" />
      <div class="scanner-box">
        <div class="scanner-header">
          <span>扫描快递单条码 (Code128)</span>
          <button type="button" class="btn-close" @click="handleClose">关闭</button>
        </div>
        <div v-if="errorMessage" class="scanner-error">{{ errorMessage }}</div>
        <div v-else ref="containerRef" class="scanner-video-wrap">
          <div v-if="scanning" class="scanner-mask">
            <div class="scanner-focus-rect" />
            <div class="scanner-tip">请将条形码放在中间区域内</div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.scanner-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}
.scanner-backdrop {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
}
.scanner-box {
  position: relative;
  width: 100%;
  max-width: 400px;
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}
.scanner-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #333;
  color: #fff;
  font-size: 14px;
}
.btn-close {
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  background: #555;
  color: #fff;
  font-size: 13px;
  cursor: pointer;
}
.btn-close:hover {
  background: #666;
}
.scanner-error {
  padding: 24px;
  color: #c91f37;
  font-size: 14px;
  text-align: center;
}
.scanner-video-wrap {
  position: relative;
  width: 100%;
  aspect-ratio: 4/3;
  background: #000;
  overflow: hidden;
}

/* 让 Quagga 注入的 video / canvas 充满容器 */
.scanner-video-wrap video,
.scanner-video-wrap canvas {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.scanner-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.scanner-mask {
  position: absolute;
  inset: 0;
  pointer-events: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  /* 上下有半透明遮罩，只留中间可视区域 */
  background: linear-gradient(
    to bottom,
    rgba(0, 0, 0, 0.5) 0%,
    rgba(0, 0, 0, 0.5) 25%,
    transparent 25%,
    transparent 75%,
    rgba(0, 0, 0, 0.5) 75%,
    rgba(0, 0, 0, 0.5) 100%
  );
}

.scanner-focus-rect {
  width: 80%;
  height: 30%;
  border: 2px solid rgba(0, 255, 0, 0.8);
  border-radius: 8px;
  box-shadow: 0 0 12px rgba(0, 255, 0, 0.6);
}

.scanner-tip {
  margin-top: 12px;
  padding: 4px 8px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  font-size: 12px;
}
</style>
