const Layout = () => import('@/layout/index.vue')

export default {
  name: '公告设置',
  path: '/settings/announcement',
  component: Layout,
  isHidden: true,
  children: [
    {
      name: '公告设置',
      path: '',
      component: () => import('./index.vue'),
      meta: {
        title: '公告设置',
        icon: 'material-symbols:campaign-outline',
        role: ['admin'],
        requireAuth: true,
      },
    },
  ],
}

