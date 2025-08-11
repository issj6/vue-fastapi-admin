import { request } from '@/utils'

export default {
  login: (data) => request.post('/base/admin_access_token', data, { noNeedToken: true }), // 管理平台登录
  clientLogin: (data) => request.post('/base/access_token', data, { noNeedToken: true }), // 前台客户端登录
  getUserInfo: () => request.get('/base/userinfo'),
  getUserMenu: () => request.get('/base/usermenu'),
  getUserApi: () => request.get('/base/userapi'),
  getPermissionMenuMapping: () => request.get('/base/permission-menu-mapping'),
  // profile
  updatePassword: (data = {}) => request.post('/base/update_password', data),
  // users
  getUserList: (params = {}) => request.get('/user/list', { params }),
  getUserById: (params = {}) => request.get('/user/get', { params }),
  createUser: (data = {}) => request.post('/user/create', data),
  updateUser: (data = {}) => request.post('/user/update', data),
  deleteUser: (params = {}) => request.delete(`/user/delete`, { params }),
  resetPassword: (data = {}) => request.post(`/user/reset_password`, data),
  // 新增用户相关API
  getInvitationInfo: () => request.get('/user/invitation_info'),
  getSubordinateUsers: (params = {}) => request.get('/user/subordinates', { params }),
  addUserPoints: (data = {}) => request.post('/user/add_points', data),
  deductUserPoints: (data = {}) => request.post('/user/deduct_points', data),
  // 代理管理API
  getAgentList: (params = {}) => request.get('/user/agents', { params }),
  // 积分管理API
  getPointsInfo: () => request.get('/points/info'),
  exchangePoints: (data = {}) => request.post('/points/exchange', data),
  rechargePoints: (data = {}) => request.post('/points/recharge', data),
  getPointsRechargeRecords: (params = {}) => request.get('/points/recharge/records', { params }),
  getPointsUsageRecords: (params = {}) => request.get('/points/usage/records', { params }),
  getAdminPointsUsageRecords: (params = {}) => request.get('/points/usage/admin/records', { params }),
  createPointsUsage: (data = {}) => request.post('/points/usage/create', data),
  // role
  getRoleList: (params = {}) => request.get('/role/list', { params }),
  createRole: (data = {}) => request.post('/role/create', data),
  updateRole: (data = {}) => request.post('/role/update', data),
  deleteRole: (params = {}) => request.delete('/role/delete', { params }),
  checkRoleUsers: (params = {}) => request.get('/role/check_users', { params }),
  updateRoleAuthorized: (data = {}) => request.post('/role/authorized', data),
  getRoleAuthorized: (params = {}) => request.get('/role/authorized', { params }),
  // 代理权限相关API
  updateRoleAgentPermissions: (data = {}) => request.post('/role/agent_permissions', data),
  getAgentPermissionsConfig: () => request.get('/role/agent_permissions'),
  getAgentRoles: () => request.get('/role/agent_roles'),
  getCreatableRoles: () => request.get('/role/creatable'),
  // menus
  getMenus: (params = {}) => request.get('/menu/list', { params }),
  createMenu: (data = {}) => request.post('/menu/create', data),
  updateMenu: (data = {}) => request.post('/menu/update', data),
  deleteMenu: (params = {}) => request.delete('/menu/delete', { params }),
  // apis
  getApis: (params = {}) => request.get('/api/list', { params }),
  createApi: (data = {}) => request.post('/api/create', data),
  updateApi: (data = {}) => request.post('/api/update', data),
  deleteApi: (params = {}) => request.delete('/api/delete', { params }),
  refreshApi: (data = {}) => request.post('/api/refresh', data),
  // auditlog
  getAuditLogList: (params = {}) => request.get('/auditlog/list', { params }),
  // announcement 公告管理
  getActiveAnnouncements: () => request.get('/announcement/active'), // 获取当前有效公告（智能识别用户类型）
  getAnnouncementList: (params = {}) => request.get('/announcement/list', { params }), // 获取公告列表（管理员）
  getAnnouncementById: (params = {}) => request.get('/announcement/get', { params }), // 获取单个公告详情
  createAnnouncement: (data = {}) => request.post('/announcement/create', data), // 创建公告
  updateAnnouncement: (data = {}) => request.put('/announcement/update', data), // 更新公告
  toggleAnnouncementStatus: (data = {}) => request.post('/announcement/toggle_status', data), // 切换公告状态
  deleteAnnouncement: (params = {}) => request.delete('/announcement/delete', { params }), // 删除公告
  // sys_config 系统配置管理
  getSysConfigList: (params = {}) => request.get('/sys_config/list', { params }), // 获取系统配置列表（超级管理员）
  getSysConfigById: (params = {}) => request.get('/sys_config/get', { params }), // 获取单个系统配置
  createSysConfig: (data = {}) => request.post('/sys_config/create', data), // 创建系统配置
  updateSysConfig: (data = {}) => request.post('/sys_config/update', data), // 更新系统配置
  deleteSysConfig: (params = {}) => request.delete('/sys_config/delete', { params }), // 删除系统配置
  getFrontendConfig: () => request.get('/sys_config/frontend'), // 获取前台配置（公共接口）
  updateFrontendConfig: (data = {}) => request.post('/sys_config/frontend/update', data), // 更新前台配置
}
