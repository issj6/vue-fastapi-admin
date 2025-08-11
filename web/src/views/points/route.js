const Layout = () => import('@/layout/index.vue')

export default {
  name: '积分管理',
  path: '/points',
  component: Layout,
  redirect: '/points/info',
  meta: {
    title: '积分管理',
    icon: 'CreditCardOutlined',
    order: 4,
  },
  children: [
    {
      name: '积分信息',
      path: 'info',
      component: () => import('./info/index.vue'),
      meta: {
        title: '积分信息',
        icon: 'WalletOutlined',
        keepAlive: true,
      },
    },
    {
      name: '使用记录',
      path: 'usage',
      component: () => import('./usage/index.vue'),
      meta: {
        title: '使用记录',
        icon: 'HistoryOutlined',
        keepAlive: true,
      },
    },
  ],
}
