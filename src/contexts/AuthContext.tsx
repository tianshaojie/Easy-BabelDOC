import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { authUtils, initGuestUser, login as authLogin, logout as authLogout } from '@/utils/auth'

interface UserInfo {
  user_id: string
  username: string
  is_guest: boolean
  token: string
}

interface AuthContextType {
  user: UserInfo | null
  loading: boolean
  login: (username: string, password: string) => Promise<boolean>
  logout: () => Promise<void>
  isGuest: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserInfo | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const initAuth = async () => {
      try {
        const existingUser = authUtils.getUserInfo()
        
        if (existingUser) {
          console.log('Using existing user:', existingUser.user_id)
          setUser(existingUser)
        } else {
          console.log('Creating new guest user...')
          const guestUser = await initGuestUser()
          if (guestUser) {
            console.log('Guest user initialized:', guestUser.user_id)
            setUser(guestUser)
          } else {
            console.error('Failed to initialize guest user')
          }
        }
      } catch (error) {
        console.error('Auth initialization error:', error)
      } finally {
        setLoading(false)
      }
    }

    initAuth()
  }, [])

  const login = async (username: string, password: string): Promise<boolean> => {
    const userInfo = await authLogin(username, password)
    if (userInfo) {
      setUser(userInfo)
      return true
    }
    return false
  }

  const logout = async () => {
    // 如果当前是游客，不做任何操作，保留游客信息
    if (user?.is_guest) {
      return
    }
    
    // 如果是正式用户登出，调用登出API
    await authLogout()
    
    // 登出后，恢复之前保存的游客用户信息
    const savedGuestUser = authUtils.getGuestUser()
    if (savedGuestUser) {
      // 恢复游客用户，保持游客ID不变
      authUtils.setUserInfo(savedGuestUser)
      setUser(savedGuestUser)
      console.log('Restored guest user:', savedGuestUser.user_id)
    } else {
      // 如果没有保存的游客信息，创建新的游客
      setUser(null)
      const guestUser = await initGuestUser()
      if (guestUser) {
        setUser(guestUser)
      }
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        logout,
        isGuest: user?.is_guest ?? true
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
