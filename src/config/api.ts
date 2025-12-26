// API 配置文件
// 默认端口与 backend/main.py 中的 determine_port 函数返回值保持一致

const API_PORT = import.meta.env.VITE_API_PORT || '58273'
const API_HOST = import.meta.env.VITE_API_HOST || window.location.hostname
const API_PROTOCOL = import.meta.env.VITE_API_PROTOCOL || window.location.protocol.replace(':', '')
const WS_PROTOCOL = API_PROTOCOL === 'https' ? 'wss' : 'ws'

export const API_BASE_URL = `${API_PROTOCOL}://${API_HOST}:${API_PORT}`
export const WS_BASE_URL = `${WS_PROTOCOL}://${API_HOST}:${API_PORT}`

// API 端点
export const API_ENDPOINTS = {
  // 健康检查
  health: `${API_BASE_URL}/api/health`,
  
  // 文件上传
  upload: `${API_BASE_URL}/api/upload`,
  
  // 翻译
  translate: `${API_BASE_URL}/api/translate`,
  translationStatus: (taskId: string) => `${API_BASE_URL}/api/translation/${taskId}/status`,
  translationWs: (taskId: string) => `${WS_BASE_URL}/api/translation/${taskId}/ws`,
  translationDownload: (taskId: string, type: string) => `${API_BASE_URL}/api/translation/${taskId}/download/${type}`,
  translationCancel: (taskId: string) => `${API_BASE_URL}/api/translation/${taskId}/cancel`,
  translationMarkFailed: (taskId: string) => `${API_BASE_URL}/api/translation/${taskId}/mark-failed`,
  
  // 翻译历史
  translations: `${API_BASE_URL}/api/translations`,
  deleteTranslation: (taskId: string) => `${API_BASE_URL}/api/translation/${taskId}`,
  
  // 术语表
  glossaries: `${API_BASE_URL}/api/glossaries`,
  glossaryUpload: `${API_BASE_URL}/api/glossary/upload`,
  deleteGlossary: (glossaryId: string) => `${API_BASE_URL}/api/glossary/${glossaryId}`,
  
  // 文件管理
  fileStats: `${API_BASE_URL}/api/files/stats`,
  fileCleanup: `${API_BASE_URL}/api/files/cleanup`,
  
  // 用户认证
  login: `${API_BASE_URL}/api/auth/login`,
  logout: `${API_BASE_URL}/api/auth/logout`,
  guestCreate: `${API_BASE_URL}/api/auth/guest`,
  currentUser: `${API_BASE_URL}/api/auth/me`,
  
  // 模型管理
  models: `${API_BASE_URL}/api/models`,
  modelUpdate: (modelId: number) => `${API_BASE_URL}/api/models/${modelId}`,
  modelDelete: (modelId: number) => `${API_BASE_URL}/api/models/${modelId}`,
  modelSetDefault: (modelId: number) => `${API_BASE_URL}/api/models/${modelId}/set-default`,
}
