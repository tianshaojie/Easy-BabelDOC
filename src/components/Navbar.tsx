import { Link, useLocation, useNavigate } from 'react-router-dom'
import { FileText, Settings, History, Home, FolderOpen, LogIn, LogOut, User } from 'lucide-react'
import { useAuth } from '@/contexts/AuthContext'

const Navbar = () => {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout, isGuest } = useAuth()

  const navItems = [
    { path: '/', label: '首页', icon: Home },
    { path: '/settings', label: '配置', icon: Settings },
    { path: '/history', label: '历史', icon: History },
    { path: '/file-manager', label: '文件管理', icon: FolderOpen },
  ]

  const handleLogout = async () => {
    await logout()
    navigate('/')
  }

  return (
    <nav className="bg-white border-b border-gray-200 shadow-sm">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <FileText className="h-8 w-8 text-pink-600" />
            <span className="text-xl font-bold text-gray-900">BabelDOC</span>
          </Link>

          {/* Navigation Links */}
          <div className="flex items-center space-x-8">
            {navItems.map(({ path, label, icon: Icon }) => {
              const isActive = location.pathname === path
              return (
                <Link
                  key={path}
                  to={path}
                  className={`flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'text-pink-600 bg-pink-50'
                      : 'text-gray-600 hover:text-pink-600 hover:bg-pink-50'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{label}</span>
                </Link>
              )
            })}

            {/* User Section */}
            <div className="flex items-center space-x-2 border-l border-gray-200 pl-4">
              {user && (
                <>
                  <div className="flex items-center space-x-2 px-3 py-2 bg-gray-50 rounded-md">
                    <User className="h-4 w-4 text-gray-600" />
                    <span className="text-sm text-gray-700">
                      {isGuest ? '游客' : user.username}
                    </span>
                  </div>
                  
                  {isGuest ? (
                    <Link
                      to="/login"
                      className="flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium text-pink-600 hover:bg-pink-50 transition-colors"
                    >
                      <LogIn className="h-4 w-4" />
                      <span>登录</span>
                    </Link>
                  ) : (
                    <button
                      onClick={handleLogout}
                      className="flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium text-gray-600 hover:text-pink-600 hover:bg-pink-50 transition-colors"
                    >
                      <LogOut className="h-4 w-4" />
                      <span>登出</span>
                    </button>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navbar