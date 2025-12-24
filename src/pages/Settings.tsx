import { useState, useEffect, useCallback } from 'react'
import { Settings as SettingsIcon, Key, Globe, Upload, Trash2, Save, Eye, EyeOff, FileText, Plus, Star } from 'lucide-react'
import { toast } from 'sonner'
import { API_ENDPOINTS } from '@/config/api'
import { useAuth } from '@/contexts/AuthContext'

interface GlossaryItem {
  id: string
  name: string
  upload_time: string
  size: number
}

interface ModelItem {
  id: number
  user_id: string
  base_url: string
  api_key: string
  model: string
  is_default: boolean
  created_at: string
}

type TabType = 'model' | 'language' | 'glossary' | 'license'

const Settings = () => {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState<TabType>('model')
  const [defaultSourceLang, setDefaultSourceLang] = useState('auto')
  const [defaultTargetLang, setDefaultTargetLang] = useState('zh')
  const [defaultQps, setDefaultQps] = useState(1)
  const [glossaries, setGlossaries] = useState<GlossaryItem[]>([])
  const [uploading, setUploading] = useState(false)
  const [savingLanguage, setSavingLanguage] = useState(false)
  
  const [models, setModels] = useState<ModelItem[]>([])
  const [newBaseUrl, setNewBaseUrl] = useState('')
  const [newApiKey, setNewApiKey] = useState('')
  const [newModel, setNewModel] = useState('')
  const [showNewApiKey, setShowNewApiKey] = useState(false)
  const [addingModel, setAddingModel] = useState(false)
  const [savingQps, setSavingQps] = useState(false)

  const languages = [
    { code: 'auto', name: '自动检测' },
    { code: 'zh', name: '中文' },
    { code: 'en', name: '英文' },
    { code: 'ja', name: '日文' },
    { code: 'ko', name: '韩文' },
    { code: 'fr', name: '法文' },
    { code: 'de', name: '德文' },
    { code: 'es', name: '西班牙文' },
    { code: 'ru', name: '俄文' },
    { code: 'it', name: '意大利文' },
    { code: 'pt', name: '葡萄牙文' },
    { code: 'ar', name: '阿拉伯文' },
    { code: 'hi', name: '印地文' },
    { code: 'th', name: '泰文' },
    { code: 'vi', name: '越南文' }
  ]

  const loadSettings = () => {
    const savedSourceLang = localStorage.getItem('babeldoc_default_source_lang') || 'auto'
    const savedTargetLang = localStorage.getItem('babeldoc_default_target_lang') || 'zh'
    const savedQps = parseInt(localStorage.getItem('babeldoc_default_qps') || '1')

    setDefaultSourceLang(savedSourceLang)
    setDefaultTargetLang(savedTargetLang)
    setDefaultQps(savedQps)
  }

  const loadGlossaries = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.glossaries)
      if (response.ok) {
        const data = await response.json()
        setGlossaries(data)
      }
    } catch (error) {
      console.error('Failed to load glossaries:', error)
    }
  }

  const loadModels = useCallback(async () => {
    try {
      const token = user?.token
      if (!token) return
      
      const response = await fetch(API_ENDPOINTS.models, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        setModels(data)
      }
    } catch (error) {
      console.error('Failed to load models:', error)
    }
  }, [user?.token])

  useEffect(() => {
    loadSettings()
    loadGlossaries()
    loadModels()
  }, [loadModels])
  
  const addModel = async () => {
    if (!newBaseUrl.trim() || !newApiKey.trim() || !newModel.trim()) {
      toast.error('请填写完整的模型信息')
      return
    }
    
    setAddingModel(true)
    
    try {
      const token = user?.token
      if (!token) {
        toast.error('未登录')
        return
      }
      
      const response = await fetch(API_ENDPOINTS.models, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          base_url: newBaseUrl.trim(),
          api_key: newApiKey.trim(),
          model: newModel.trim(),
          is_default: models.length === 0
        })
      })
      
      if (response.ok) {
        toast.success('模型已添加')
        setNewBaseUrl('')
        setNewApiKey('')
        setNewModel('')
        loadModels()
      } else {
        const error = await response.json()
        toast.error(error.detail || '添加失败')
      }
    } catch (error) {
      console.error('Add model failed:', error)
      toast.error('添加过程中发生错误')
    } finally {
      setAddingModel(false)
    }
  }
  
  const deleteModel = async (modelId: number) => {
    if (!window.confirm('确定要删除这个模型配置吗？')) return
    
    try {
      const token = user?.token
      if (!token) return
      
      const response = await fetch(API_ENDPOINTS.modelDelete(modelId), {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (response.ok) {
        toast.success('模型已删除')
        loadModels()
      } else {
        toast.error('删除失败')
      }
    } catch (error) {
      console.error('Delete model failed:', error)
      toast.error('删除过程中发生错误')
    }
  }
  
  const setDefaultModel = async (modelId: number) => {
    try {
      const token = user?.token
      if (!token) return
      
      const response = await fetch(API_ENDPOINTS.modelSetDefault(modelId), {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (response.ok) {
        toast.success('默认模型已设置')
        loadModels()
      } else {
        toast.error('设置失败')
      }
    } catch (error) {
      console.error('Set default model failed:', error)
      toast.error('设置过程中发生错误')
    }
  }
  
  const saveQpsSettings = async () => {
    setSavingQps(true)
    
    try {
      localStorage.setItem('babeldoc_default_qps', defaultQps.toString())
      toast.success('QPS设置已保存')
    } catch {
      toast.error('保存QPS设置失败')
    } finally {
      setSavingQps(false)
    }
  }

  const saveLanguageSettings = async () => {
    setSavingLanguage(true)
    
    try {
      localStorage.setItem('babeldoc_default_source_lang', defaultSourceLang)
      localStorage.setItem('babeldoc_default_target_lang', defaultTargetLang)
      
      toast.success('语言设置已保存')
    } catch {
      toast.error('保存语言设置失败')
    } finally {
      setSavingLanguage(false)
    }
  }

  const handleGlossaryUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    if (!file.name.toLowerCase().endsWith('.csv')) {
      toast.error('请选择.csv格式的词汇表文件')
      return
    }

    setUploading(true)
    
    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch(API_ENDPOINTS.glossaryUpload, {
        method: 'POST',
        body: formData
      })

      if (response.ok) {
        toast.success('词汇表上传成功')
        loadGlossaries()
      } else {
        const error = await response.json()
        toast.error(error.detail || '上传失败')
      }
    } catch (error) {
      console.error('Upload failed:', error)
      toast.error('上传过程中发生错误')
    } finally {
      setUploading(false)
      event.target.value = ''
    }
  }

  const deleteGlossary = async (glossaryId: string) => {
    if (!window.confirm('确定要删除这个词汇表吗？')) return

    try {
      const response = await fetch(API_ENDPOINTS.deleteGlossary(glossaryId), {
        method: 'DELETE'
      })

      if (response.ok) {
        toast.success('词汇表已删除')
        loadGlossaries()
      } else {
        toast.error('删除失败')
      }
    } catch (error) {
      console.error('Delete failed:', error)
      toast.error('删除过程中发生错误')
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const groupModelsByBaseUrl = () => {
    const grouped: { [key: string]: ModelItem[] } = {}
    models.forEach(model => {
      if (!grouped[model.base_url]) {
        grouped[model.base_url] = []
      }
      grouped[model.base_url].push(model)
    })
    return grouped
  }

  const tabs = [
    { id: 'model' as TabType, name: '模型设置', icon: Key },
    { id: 'language' as TabType, name: '语言设置', icon: Globe },
    { id: 'glossary' as TabType, name: '词汇表管理', icon: Upload },
    { id: 'license' as TabType, name: '许可证信息', icon: FileText }
  ]

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center justify-center">
          <SettingsIcon className="h-8 w-8 mr-2 text-pink-600" />
          设置
        </h1>
        <p className="text-gray-600">配置API密钥、默认参数和词汇表</p>
      </div>

      <div className="bg-white rounded-lg border border-gray-200 mb-6">
        <div className="flex border-b border-gray-200">
          {tabs.map((tab) => {
            const Icon = tab.icon
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 px-6 py-4 text-sm font-medium transition-colors flex items-center justify-center space-x-2 ${
                  activeTab === tab.id
                    ? 'text-pink-600 border-b-2 border-pink-600 bg-pink-50'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                <Icon className="h-5 w-5" />
                <span>{tab.name}</span>
              </button>
            )
          })}
        </div>
      </div>

      {activeTab === 'model' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">模型列表</h2>
            
            {models.length > 0 ? (
              <div className="space-y-4">
                {Object.entries(groupModelsByBaseUrl()).map(([baseUrl, modelList]) => (
                  <div key={baseUrl} className="border border-gray-200 rounded-lg p-4">
                    <h3 className="font-medium text-gray-700 mb-3 flex items-center">
                      <Globe className="h-4 w-4 mr-2" />
                      {baseUrl}
                    </h3>
                    <div className="space-y-2">
                      {modelList.map(model => (
                        <div key={model.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                          <div className="flex-1">
                            <div className="flex items-center space-x-2">
                              <span className="font-medium text-gray-900">{model.model}</span>
                              {model.is_default && (
                                <span className="px-2 py-1 text-xs bg-pink-100 text-pink-600 rounded-full flex items-center">
                                  <Star className="h-3 w-3 mr-1 fill-current" />
                                  默认
                                </span>
                              )}
                            </div>
                            <p className="text-xs text-gray-500 mt-1">
                              API Key: {model.api_key.substring(0, 10)}...
                            </p>
                          </div>
                          
                          <div className="flex items-center space-x-2">
                            {!model.is_default && (
                              <button
                                onClick={() => setDefaultModel(model.id)}
                                className="text-gray-600 hover:text-pink-600 p-2 rounded-lg hover:bg-pink-50 transition-colors"
                                title="设为默认"
                              >
                                <Star className="h-4 w-4" />
                              </button>
                            )}
                            <button
                              onClick={() => deleteModel(model.id)}
                              className="text-red-600 hover:text-red-800 p-2 rounded-lg hover:bg-red-50 transition-colors"
                              title="删除"
                            >
                              <Trash2 className="h-4 w-4" />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <Key className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                <p>暂无模型配置</p>
                <p className="text-sm">请在下方添加模型</p>
              </div>
            )}
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">添加模型（仅支持兼容OpenAI的大语言模型）</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Base URL
                </label>
                <input
                  type="text"
                  value={newBaseUrl}
                  onChange={(e) => setNewBaseUrl(e.target.value)}
                  placeholder="https://api.openai.com/v1"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  API密钥
                </label>
                <div className="relative">
                  <input
                    type={showNewApiKey ? 'text' : 'password'}
                    value={newApiKey}
                    onChange={(e) => setNewApiKey(e.target.value)}
                    placeholder="请输入API密钥"
                    className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent"
                  />
                  <button
                    type="button"
                    onClick={() => setShowNewApiKey(!showNewApiKey)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
                  >
                    {showNewApiKey ? (
                      <EyeOff className="h-5 w-5" />
                    ) : (
                      <Eye className="h-5 w-5" />
                    )}
                  </button>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  模型名称
                </label>
                <input
                  type="text"
                  value={newModel}
                  onChange={(e) => setNewModel(e.target.value)}
                  placeholder="gpt-4o"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent"
                />
              </div>
            </div>

            <div className="flex justify-center mt-6">
              <button
                onClick={addModel}
                disabled={addingModel}
                className="bg-pink-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-pink-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                {addingModel ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    <span>添加中...</span>
                  </>
                ) : (
                  <>
                    <Plus className="h-5 w-5" />
                    <span>添加模型</span>
                  </>
                )}
              </button>
            </div>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">默认QPS</h2>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                默认QPS（每秒请求数）
              </label>
              <input
                type="number"
                min="1"
                max="10"
                value={defaultQps}
                onChange={(e) => setDefaultQps(parseInt(e.target.value) || 1)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent"
              />
            </div>

            <div className="flex justify-center mt-6">
              <button
                onClick={saveQpsSettings}
                disabled={savingQps}
                className="bg-pink-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-pink-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                {savingQps ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    <span>保存中...</span>
                  </>
                ) : (
                  <>
                    <Save className="h-5 w-5" />
                    <span>保存设置</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'language' && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">翻译语言设置</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                默认源语言
              </label>
              <select
                value={defaultSourceLang}
                onChange={(e) => setDefaultSourceLang(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent"
              >
                {languages.map(lang => (
                  <option key={lang.code} value={lang.code}>{lang.name}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                默认目标语言
              </label>
              <select
                value={defaultTargetLang}
                onChange={(e) => setDefaultTargetLang(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent"
              >
                {languages.filter(lang => lang.code !== 'auto').map(lang => (
                  <option key={lang.code} value={lang.code}>{lang.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex justify-center mt-6">
            <button
              onClick={saveLanguageSettings}
              disabled={savingLanguage}
              className="bg-pink-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-pink-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
            >
              {savingLanguage ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  <span>保存中...</span>
                </>
              ) : (
                <>
                  <Save className="h-5 w-5" />
                  <span>保存设置</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {activeTab === 'glossary' && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-gray-900">词汇表管理</h2>
            
            <div className="relative">
              <input
                type="file"
                accept=".csv"
                onChange={handleGlossaryUpload}
                disabled={uploading}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed"
              />
              <button
                disabled={uploading}
                className="bg-pink-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-pink-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
              >
                {uploading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>上传中...</span>
                  </>
                ) : (
                  <>
                    <Upload className="h-4 w-4" />
                    <span>上传词汇表</span>
                  </>
                )}
              </button>
            </div>
          </div>
          
          <div className="mb-4">
            <p className="text-sm text-gray-600">
              支持.csv格式的词汇表文件（UTF-8），可包含表头，示例：源文本,目标文本
            </p>
          </div>
          
          {glossaries.length > 0 ? (
            <div className="space-y-3">
              {glossaries.map(glossary => (
                <div key={glossary.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-pink-300 transition-colors">
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900">{glossary.name}</h3>
                    <div className="flex items-center space-x-4 text-sm text-gray-500 mt-1">
                      <span>大小: {formatFileSize(glossary.size)}</span>
                      <span>上传时间: {new Date(glossary.upload_time).toLocaleString()}</span>
                    </div>
                  </div>
                  
                  <button
                    onClick={() => deleteGlossary(glossary.id)}
                    className="text-red-600 hover:text-red-800 p-2 rounded-lg hover:bg-red-50 transition-colors"
                    title="删除词汇表"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Upload className="h-12 w-12 mx-auto mb-2 text-gray-300" />
              <p>暂无词汇表</p>
              <p className="text-sm">点击上方按钮上传词汇表文件</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'license' && (
        <div className="bg-white rounded-lg border border-gray-200 p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">许可证信息</h2>
          <div className="space-y-4 text-sm text-gray-600">
            <div>
              <h3 className="font-medium text-gray-900 mb-2">Easy-BabelDOC</h3>
              <p>版本: 1.0.0</p>
              <p>作者: lijiapeng365</p>
              <p>许可证: GNU Affero General Public License (AGPL) v3</p>
            </div>
            
            <div className="border-t pt-4">
              <h4 className="font-medium text-gray-900 mb-2">重要声明</h4>
              <p className="mb-2">
                本软件基于 <a href="https://github.com/funstory-ai/BabelDOC" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">BabelDOC</a> 开发，使用 AGPL-3.0 许可证。
              </p>
              <p className="mb-2">
                根据 AGPL-3.0 要求，如果您修改本软件并通过网络提供服务，必须向用户提供修改后的源代码。
              </p>
              <p>
                完整源代码可在 <a href="https://github.com/lijiapeng365/Easy-BabelDOC" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">GitHub</a> 获取。
              </p>
            </div>
            
            <div className="border-t pt-4">
              <h4 className="font-medium text-gray-900 mb-2">第三方组件</h4>
              <p>本软件使用了多个开源组件，详细信息请查看项目的 package.json 和 requirements.txt 文件。</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Settings
