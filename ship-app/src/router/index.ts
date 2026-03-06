import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import EmptyLayout from '@/layouts/EmptyLayout.vue'
import MainLayout from '@/layouts/MainLayout.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
        path: '/',
        component: EmptyLayout,
        children: [
            {
                path: '/',
                component: () => import('@/views/Home.vue'),
                meta: { title: '首页' }
            },
            {
                path: '/login',
                component: () => import('@/views/Login.vue'),
                meta: { title: '登录' }
            },
            {
                path: '/share/:token',
                component: () => import('@/views/Share.vue'),
                meta: { title: '分享' }
            },
            {
                path: '/order-lookup',
                component: () => import('@/views/OrderLookup.vue'),
                meta: { title: '快递单号查询' }
            }
        ]
    },
    {
        path: '/auth',
        component: MainLayout,
        children: [
            {
                path: '/main',
                component: () => import('@/views/auth/MainView.vue'),
                meta: { title: '主页' }
            },
            {
                path: '/orders',
                component: () => import('@/views/auth/OrdersView.vue'),
                meta: { title: '订单' }
            },
            {
                path: '/profile',
                component: () => import('@/views/auth/ProfileView.vue'),
                meta: { title: '个人' }
            },
            {
                path: '/messages',
                component: () => import('@/views/auth/MessagesView.vue'),
                meta: { title: '消息中心' }
            },
            {
                path: '/customers',
                component: () => import('@/views/auth/CustomersView.vue'),
                meta: { title: '客户管理' }
            },
            {
                path: '/share-links',
                component: () => import('@/views/auth/ShareLinksView.vue'),
                meta: { title: '分享链接管理' }
            },
            {
                path: '/order-styles',
                component: () => import('@/views/auth/OrderStyle/OrderStylesView.vue'),
                meta: { title: '订单样式管理' }
            },
            {
                path: '/order-styles/new',
                component: () => import('@/views/auth/OrderStyle/OrderStyleEditView.vue'),
                meta: { title: '新建订单样式' }
            },
            {
                path: '/order-styles/:id',
                component: () => import('@/views/auth/OrderStyle/OrderStyleEditView.vue'),
                meta: { title: '编辑订单样式' }
            },
            {
                path: '/submit-order',
                component: () => import('@/views/auth/Order/OrderCompleteView.vue'),
                meta: { title: '提交订单' }
            },
            {
                path: '/create-order',
                component: () => import('@/views/auth/Order/OrderCreateView.vue'),
                meta: { title: '新建订单' }
            },
            {
                path: '/order/:id',
                component: () => import('@/views/auth/Order/OrderEditView.vue'),
                meta: { title: '订单详情' }
            }
        ],
        meta: { requiresAuth: true }
    },
    // 未定义路由一律重定向到首页
    { path: '/:pathMatch(.*)*', redirect: '/' }
  ],
})

router.beforeEach((to, _from, next) => {
  const requiresAuth = to.matched.some((r) => r.meta.requiresAuth)
  const auth = useAuthStore()
  const isLoggedIn = auth.isLoggedIn

  // 需要登录的页面且未登录 → 去登录页，并记下目标地址
  if (requiresAuth && !isLoggedIn) {
    next({ path: '/login', query: { redirect: to.fullPath } })
    return
  }
  // 已登录用户访问无须登录的页面 → 跳到 MainTab；排除 /main 和 /share/:token（分享链接任何人可打开）
  if (!requiresAuth && isLoggedIn && to.path !== '/main' && !to.path.startsWith('/share/') && to.path !== '/order-lookup') {
    next({ path: '/main' })
    return
  }
  next()
})

export default router
