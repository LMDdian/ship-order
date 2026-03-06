/**
 * 统一请求工具：apiRequest
 *
 * 使用方式：
 *  - GET（默认带上登录态并自动尝试 refresh）：
 *      const data = await apiRequest<any>('/api/order-styles/')
 *
 *  - POST / PUT：
 *      const data = await apiRequest('/api/order-styles/', {
 *        method: 'POST',
 *        body: { name: '测试', description: '备注' },
 *      })
 *
 *  - 不需要登录态的接口（如登录本身）：
 *      const data = await apiRequest('/api/public', { auth: false })
 *
 * 特性：
 *  - 自动附带 Authorization: Bearer <access>
 *  - 遇到 401 时自动使用 refresh 换新 access，并重试一次
 *  - 非 2xx 时优先读取响应中的 data.detail 作为错误信息抛出
 */
import router from '@/router'
import { useAuthStore } from '@/stores/auth'

export interface ApiRequestOptions {
  method?: string
  body?: any
  headers?: Record<string, string>
  /** 是否自动附带并刷新登录信息，默认 true */
  auth?: boolean
}

export async function apiRequest<T = any>(
  url: string,
  options: ApiRequestOptions = {},
): Promise<T> {
  const auth = useAuthStore()
  const method = options.method ?? 'GET'
  const needAuth = options.auth !== false

  async function doFetch(): Promise<Response> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    }
    if (needAuth && auth.token) {
      headers.Authorization = `Bearer ${auth.token}`
    }

    return fetch(url, {
      method,
      headers,
      body: options.body != null ? JSON.stringify(options.body) : undefined,
    })
  }

  let resp = await doFetch()

  if (needAuth && resp.status === 401) {
    const refreshed = await auth.refreshAccessToken()
    if (!refreshed) {
      auth.logout()
      router.replace({ path: '/login', query: { redirect: router.currentRoute.value.fullPath } })
      throw new Error('登录已失效，请重新登录')
    }
    resp = await doFetch()
  }

  if (!resp.ok) {
    let message = '请求失败'
    try {
      const data = await resp.json()
      if (data && typeof data.detail === 'string') {
        message = data.detail
      }
    } catch {
      // ignore parse error
    }
    throw new Error(message)
  }

  if (resp.status === 204) {
    // @ts-expect-error: 允许调用方用 void 接收
    return null
  }

  return (await resp.json()) as T
}

