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
}
