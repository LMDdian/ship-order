import { defineStore } from 'pinia'

// 定义 token / 用户信息 / 用户偏好的 key （存储于 localStorage）
const TOKEN_KEY = 'ship_token'
const REFRESH_KEY = 'ship_refresh'
const USER_KEY = 'ship_user'
const PREFERENCE_KEY = 'ship_preference'

export type AuthUser = {
  id: number
  username?: string
  first_name?: string
  last_name?: string
}

export type UserPreference = {
  id: number
  button_reverse: boolean
  default_order_style?: {
    id: number
    name: string
  } | null
  /** 快递单号查询密钥：分享给他人后，他人可用 密钥+完整快递单号 查看只读订单 */
  tracking_lookup_key?: string
  /** 允许存储容量（字节），默认 10GB */
  storage_limit_bytes?: number
  /** 已使用存储（字节），由服务端计算 */
  storage_used_bytes?: number
}

function loadUserFromStorage(): AuthUser | null {
  try {
    const raw = localStorage.getItem(USER_KEY)
    if (!raw) return null
    return JSON.parse(raw)
  } catch {
    return null
  }
}

function loadPreferenceFromStorage(): UserPreference | null {
  try {
    const raw = localStorage.getItem(PREFERENCE_KEY)
    if (!raw) return null
    return JSON.parse(raw)
  } catch {
    return null
  }
}

// 创建auth store
// defineStore 接受两个参数，第一个是store的名称，第二个是store的配置对象
export const useAuthStore = defineStore('auth', {
  // state定义store的状态，返回一个对象，对象的属性就是store的状态
  state: () => ({
    token: (localStorage.getItem(TOKEN_KEY) as string) || null,
    refresh: (localStorage.getItem(REFRESH_KEY) as string) || null,
    user: loadUserFromStorage(),
    preference: loadPreferenceFromStorage() as UserPreference | null,
  }),

  // getters定义store的计算属性，返回一个对象，对象的属性就是store的计算属性
  getters: {
    // 判断用户是否登录
    isLoggedIn(state): boolean {
      return !!state.token
    },
  },

  // actions定义store的actions，所有对state的修改都应该通过actions来完成
  actions: {
    setToken(token: string) {
      this.token = token
      localStorage.setItem(TOKEN_KEY, token)
    },

    setRefresh(refresh: string | null) {
      this.refresh = refresh
      if (refresh) {
        localStorage.setItem(REFRESH_KEY, refresh)
      } else {
        localStorage.removeItem(REFRESH_KEY)
      }
    },

    setUser(user: AuthUser | null) {
      this.user = user
      if (user) {
        localStorage.setItem(USER_KEY, JSON.stringify(user))
      } else {
        localStorage.removeItem(USER_KEY)
      }
    },

    setPreference(preference: UserPreference | null) {
      this.preference = preference
      if (preference) {
        localStorage.setItem(PREFERENCE_KEY, JSON.stringify(preference))
      } else {
        localStorage.removeItem(PREFERENCE_KEY)
      }
    },

    login(token: string, user?: AuthUser, refresh?: string | null) {
      this.setToken(token)
      this.setRefresh(refresh || null)
      if (user) this.setUser(user)
    },

    logout() {
      this.token = null
      this.refresh = null
      this.user = null
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(REFRESH_KEY)
      localStorage.removeItem(USER_KEY)
      this.setPreference(null)
    },

    async refreshAccessToken(): Promise<boolean> {
      if (!this.refresh) return false
      try {
        const resp = await fetch('/api/token/refresh/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh: this.refresh }),
        })
        if (!resp.ok) {
          this.logout()
          return false
        }
        const data = await resp.json()
        const access = (data as any).access as string | undefined
        if (!access) {
          this.logout()
          return false
        }
        this.setToken(access)
        return true
      } catch {
        this.logout()
        return false
      }
    },
  },
})
