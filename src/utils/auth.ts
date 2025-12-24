interface UserInfo {
  user_id: string
  username: string
  is_guest: boolean
  token: string
}

const USER_INFO_KEY = 'babeldoc_user'
const GUEST_USER_KEY = 'babeldoc_guest_user'

export const authUtils = {
  getUserId(): string | null {
    const user = this.getUserInfo()
    return user ? user.user_id : null
  },

  getUserInfo(): UserInfo | null {
    const userStr = localStorage.getItem(USER_INFO_KEY)
    if (!userStr) return null
    try {
      return JSON.parse(userStr)
    } catch {
      return null
    }
  },

  setUserInfo(user: UserInfo): void {
    // 如果当前有游客用户，且新用户不是游客，则保存游客信息
    const currentUser = this.getUserInfo()
    if (currentUser?.is_guest && !user.is_guest) {
      this.saveGuestUser(currentUser)
    }
    localStorage.setItem(USER_INFO_KEY, JSON.stringify(user))
  },

  removeUserInfo(): void {
    localStorage.removeItem(USER_INFO_KEY)
  },

  saveGuestUser(guestUser: UserInfo): void {
    localStorage.setItem(GUEST_USER_KEY, JSON.stringify(guestUser))
  },

  getGuestUser(): UserInfo | null {
    const guestStr = localStorage.getItem(GUEST_USER_KEY)
    if (!guestStr) return null
    try {
      return JSON.parse(guestStr)
    } catch {
      return null
    }
  },

  isAuthenticated(): boolean {
    return !!this.getUserId()
  },

  logout(): void {
    this.removeUserInfo()
  },

  getAuthHeaders(): HeadersInit {
    const userId = this.getUserId()
    if (!userId) return {}
    return {
      'Authorization': `Bearer ${userId}`
    }
  }
}

export async function initGuestUser(): Promise<UserInfo | null> {
  // 如果已经有认证信息，直接返回
  if (authUtils.isAuthenticated()) {
    const existingUser = authUtils.getUserInfo()
    if (existingUser) {
      return existingUser
    }
  }
  
  try {
    // 动态导入API_ENDPOINTS以避免循环依赖
    const { API_ENDPOINTS } = await import('@/config/api')
    
    const response = await fetch(API_ENDPOINTS.guestCreate, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })

    if (response.ok) {
      const userInfo: UserInfo = await response.json()
      authUtils.setUserInfo(userInfo)
      console.log('Guest user created:', userInfo.user_id)
      return userInfo
    } else {
      const errorText = await response.text()
      console.error('Failed to create guest user:', response.status, errorText)
    }
  } catch (error) {
    console.error('Failed to create guest user:', error)
  }

  return null
}

export async function login(username: string, password: string): Promise<UserInfo | null> {
  try {
    const { API_ENDPOINTS } = await import('@/config/api')
    
    const response = await fetch(API_ENDPOINTS.login, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ username, password })
    })

    if (response.ok) {
      const userInfo: UserInfo = await response.json()
      authUtils.setUserInfo(userInfo)
      return userInfo
    }
  } catch (error) {
    console.error('Login failed:', error)
  }

  return null
}

export async function logout(): Promise<void> {
  try {
    const { API_ENDPOINTS } = await import('@/config/api')
    
    await fetch(API_ENDPOINTS.logout, {
      method: 'POST',
      headers: {
        ...authUtils.getAuthHeaders()
      }
    })
  } catch (error) {
    console.error('Logout failed:', error)
  } finally {
    authUtils.logout()
  }
}
