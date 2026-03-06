<script setup lang="ts">
</script>

<template>
  <div class="home-page">
    <van-nav-bar title="打单发货" />
    <div class="content">
      <section class="intro">
        <h1 class="intro-title">打单发货</h1>
        <p class="intro-desc">管理订单、上传图片、生成面单，支持分享链接与授权查询。登录后可使用完整功能。</p>
      </section>

      <section class="entries">
        <router-link to="/order-lookup" class="entry-link">
          <span class="entry-label">快递单号查询</span>
          <span class="entry-desc">已有用户授权链接：通过密钥与快递单号查看订单（只读）</span>
          <span class="entry-arrow">→</span>
        </router-link>
        <router-link to="/login" class="entry-link">
          <span class="entry-label">登录</span>
          <span class="entry-desc">登录后进入工作台，管理订单与客户</span>
          <span class="entry-arrow">→</span>
        </router-link>
      </section>
    </div>
  </div>
</template>

<style scoped>
.home-page { min-height: 100vh; background: #f7f8fa; }

.content {
  padding: 24px 16px;
  max-width: 480px;
  margin: 0 auto;
}

.intro {
  margin-bottom: 28px;
}

.intro-title {
  margin: 0 0 12px;
  font-size: 22px;
  font-weight: 600;
  color: #111827;
}

.intro-desc {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  color: #64748b;
}

.entries {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.entry-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  text-decoration: none;
  color: inherit;
  transition: border-color 0.2s;
}

.entry-link:hover {
  border-color: #cbd5e1;
}

.entry-label {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  flex-shrink: 0;
}

.entry-desc {
  flex: 1;
  min-width: 0;
  font-size: 13px;
  color: #64748b;
  line-height: 1.4;
}

.entry-arrow {
  flex-shrink: 0;
  font-size: 16px;
  color: #94a3b8;
}
</style>
