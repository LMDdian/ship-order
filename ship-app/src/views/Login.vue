<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { showToast } from 'vant'
import { useAuthStore } from '@/stores/auth'
import type { UserPreference } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const username = ref('')
const password = ref('')
const loading = ref(false)

async function onSubmit() {
  if (!username.value.trim() || !password.value) {
    showToast('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    const resp = await fetch('/api/login/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: username.value.trim(),
        password: password.value,
      }),
    })

    if (!resp.ok) {
      const data = await resp.json().catch(() => ({}))
      throw new Error((data as any).detail || '登录失败')
    }

    const data = await resp.json()
    const token = data.access as string | null
    const refresh = data.refresh as string | null
    const user = data.user as any

    if (!token || !refresh) {
      throw new Error('登录接口未返回完整的 token 信息')
    }

    auth.login(
      token,
      {
        id: user.id,
        username: user.username,
        first_name: user.first_name,
        last_name: user.last_name,
      },
      refresh,
    )

    // 登录成功后，调用后端用户偏好接口，更新前端 auth 中的用户喜好对象
    try {
      const prefResp = await fetch('/api/user-preference/', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
      })
      if (prefResp.ok) {
        const prefData = (await prefResp.json()) as UserPreference
        auth.setPreference(prefData)
      }
    } catch {
      // 获取偏好失败不影响登录流程，静默忽略
    }
    showToast('登录成功')
    router.push((route.query.redirect as string) || '/')
  } catch (err: any) {
    showToast(err?.message || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <van-form @submit="onSubmit">
      <van-cell-group inset>
        <van-field
          v-model="username"
          name="username"
          label="用户名"
          placeholder="请输入"
          :rules="[{ required: true }]"
        />
        <van-field
          v-model="password"
          type="password"
          name="password"
          label="密码"
          placeholder="请输入"
          :rules="[{ required: true }]"
        />
      </van-cell-group>
      <div class="form-actions">
        <button
          type="submit"
          class="btn-login"
          :disabled="loading"
        >
          {{ loading ? '登录中…' : '登录' }}
        </button>
        <router-link to="/" class="link-home">返回首页</router-link>
      </div>
    </van-form>
  </div>
</template>

<style scoped>
.login-page { padding-top: 24px; }

.form-actions {
  margin: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.btn-login {
  width: 100%;
  padding: 12px 16px;
  font-size: 16px;
  font-weight: 500;
  color: #fff;
  background: #000;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}

.btn-login:hover:not(:disabled) {
  background: #333;
}

.btn-login:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.link-home {
  display: block;
  text-align: center;
  font-size: 14px;
  color: #64748b;
  text-decoration: none;
}

.link-home:hover {
  color: #475569;
}
</style>
