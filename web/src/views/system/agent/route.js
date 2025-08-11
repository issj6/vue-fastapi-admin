const Layout = () => import('@/layout/index.vue')

export default {
  name: '代理管理',
  path: '/system/agent',
  component: Layout,
  redirect: '/system/agent',
  meta: {
    title: '代理管理',
    icon: 'carbon:user-multiple',
    order: 7,
  },
  children: [
    {
      name: '代理管理',
      path: '',
      component: () => import('./index.vue'),
      meta: {
        title: '代理管理',
        icon: 'carbon:user-multiple',
        affix: false,
      },
    },
  ],
}
