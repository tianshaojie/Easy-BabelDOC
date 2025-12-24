interface UserInfo {
  user_id: string
  username: string
  is_guest: boolean
  token: string
}

const TOKEN_KEY = 'babeldoc_token'
const USER_INFO_KEY = 'babeldoc_user'
const GUEST_ID_KEY = 'babeldoc_guest_id'

export const authUtils = {
  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY)
  },

  setToken(token: string): void {
    localStorage.setItem(TOKEN_KEY, token)
  },

  removeToken(): void {
    localStorage.removeItem(TOKEN_KEY)
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
    localStorage.setItem(USER_INFO_KEY, JSON.stringify(user))
  },

  removeUserInfo(): void {
    localStorage.removeItem(USER_INFO_KEY)
  },

  isAuthenticated(): boolean {
    return !!this.getToken()
  },

  logout(): void {
    this.removeToken()
    this.removeUserInfo()
  },

  getAuthHeaders(): HeadersInit {
    const token = this.getToken()
    if (!token) return {}
    return {
      'Authorization': `Bearer ${token}`
    }
  },

  getGuestId(): string | null {
    return localStorage.getItem(GUEST_ID_KEY)
  },

  setGuestId(guestId: string): void {
    localStorage.setItem(GUEST_ID_KEY, guestId)
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
      authUtils.setToken(userInfo.token)
      authUtils.setUserInfo(userInfo)
      authUtils.setGuestId(userInfo.user_id)
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
      authUtils.setToken(userInfo.token)
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
