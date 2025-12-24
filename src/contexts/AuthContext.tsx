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
        const existingToken = authUtils.getToken()
        
        if (existingUser && existingToken) {
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
    await authLogout()
    setUser(null)
    const guestUser = await initGuestUser()
    if (guestUser) {
      setUser(guestUser)
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
