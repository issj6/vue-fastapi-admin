const Layout = () => import('@/layout/index.vue')

export default {
  name: '前台设置',
  path: '/settings/frontend',
  component: Layout,
  isHidden: true,
  children: [
    {
      name: '前台设置',
      path: '',
      component: () => import('./index.vue'),
      meta: {
        title: '前台设置',
        icon: 'material-symbols:settings-outline',
        role: ['admin'],
        requireAuth: true,
      },
    },
  ],
}
