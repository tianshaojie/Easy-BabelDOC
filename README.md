# Easy-BabelDOC

基于BabelDOC API的Web翻译应用，提供PDF文档翻译功能。

## 功能特性

- 📄 PDF文档上传和翻译
- 🌐 多语言支持（中文、英文、日文、韩文等）
- 🤖 多种AI模型选择（GPT-4o、GPT-4o Mini等）
- 📊 实时翻译进度监控
- 📥 双语PDF和单语PDF下载
- 📚 词汇表管理
- 📋 翻译历史记录
- ⚙️ 个性化设置

## 技术栈

### 前端
- React 18 + TypeScript
- Vite 构建工具
- Tailwind CSS 样式框架
- React Router 路由管理
- Zustand 状态管理
- Lucide React 图标库
- Sonner 通知组件

### 后端
- Python FastAPI
- BabelDOC 翻译引擎
- WebSocket 实时通信
- 文件上传和管理

## 快速开始

### 环境要求
- Node.js 18+
- Python 3.12+
- OpenAI API Key

### 安装步骤

#### 1. 创建 Conda 虚拟环境
```bash
# 创建虚拟环境
conda create -n babeldoc python=3.12

# 激活虚拟环境
conda activate babeldoc

# 安装后端依赖
pip install -r backend/requirements.txt
```

#### 2. 安装前端依赖
```bash
# 安装前端依赖
npm install

# 构建前端（生产环境）
npm run build
```

### 启动和停止

**启动所有服务**

```bash
# 确保已激活 conda 环境
conda activate babeldoc

# 启动前端和后端服务（会自动重新构建前端）
./start.sh

# 仅启动后端
./start.sh backend

# 仅启动前端（会自动重新构建）
./start.sh frontend

# 开发模式（后端后台运行，前端前台运行，支持热重载）
./start.sh dev
```

> **注意**: `./start.sh` 默认会重新构建前端代码,确保使用最新版本。开发时建议使用 `./start.sh dev` 模式,支持热重载。

**停止所有服务**

```bash
# 停止前端和后端服务
./stop.sh

# 仅停止后端
./stop.sh backend

# 仅停止前端
./stop.sh frontend
```

**查看日志**

```bash
# 查看后端日志
tail -f /tmp/easy_babeldoc_backend.log

# 查看前端日志
tail -f /tmp/easy_babeldoc_frontend.log
```


### 访问应用
- 前端（生产模式）：http://localhost:4173
- 前端（开发模式）：http://localhost:5173
- 后端API：http://localhost:58273
- API文档：http://localhost:58273/docs

## 使用说明

### 1. 配置API密钥
- 访问设置页面
- 输入您的OpenAI API密钥
- 配置默认翻译参数

### 2. 上传和翻译文档
- 在首页上传PDF文件
- 选择源语言和目标语言
- 选择AI模型和其他参数
- 点击开始翻译

### 3. 监控翻译进度
- 实时查看翻译进度
- 查看详细的翻译日志
- 支持取消正在进行的翻译

### 4. 下载翻译结果
- 下载单语PDF（仅翻译内容）
- 下载双语PDF（原文+翻译对照）

### 5. 管理词汇表
- 上传自定义词汇表文件
- 管理和删除词汇表
- 提高翻译准确性

## 项目结构

```
Easy-BabelDOC/
├── backend/                 # Python后端
│   ├── api/                # API路由
│   ├── db/                 # 数据库模块
│   ├── main.py             # FastAPI应用入口
│   ├── requirements.txt    # Python依赖
│   └── stop.sh            # 后端停止脚本
├── src/                    # React前端源码
│   ├── components/         # 组件
│   ├── pages/             # 页面
│   ├── hooks/             # 自定义Hooks
│   └── lib/               # 工具函数
├── public/                # 静态资源
├── dist/                  # 前端构建产物
├── start.sh              # 项目启动脚本
├── stop.sh               # 项目停止脚本
├── package.json          # 前端依赖配置
└── README.md             # 项目说明
```

## 开发说明

### 前端开发
```bash
npm run dev      # 开发模式（热重载）
npm run build    # 构建生产版本
npm run preview  # 预览生产版本
npm run lint     # 代码检查
```

### 后端开发
```bash
# 激活虚拟环境
conda activate babeldoc

# 安装新依赖
pip install package_name
pip freeze > backend/requirements.txt

# 运行后端（开发模式）
cd backend
python main.py
```

### 开发模式启动
```bash
# 推荐：使用开发模式启动
# 后端后台运行，前端前台运行（支持热重载）
./start.sh dev
```

## API文档

后端提供完整的RESTful API和WebSocket接口：
- 文件上传：`POST /api/upload`
- 开始翻译：`POST /api/translation/start`
- 翻译状态：`GET /api/translation/{task_id}/status`
- 实时进度：`WebSocket /api/translation/{task_id}/ws`
- 下载结果：`GET /api/translation/{task_id}/download`
- 词汇表管理：`/api/glossary/*`

详细API文档请访问：http://localhost:8000/docs

## 注意事项

1. **API密钥安全**：API密钥存储在浏览器本地，请妥善保管
2. **文件大小限制**：建议上传文件不超过50MB
3. **网络连接**：翻译过程需要稳定的网络连接
4. **虚拟环境**：后端使用 Conda 管理虚拟环境，避免依赖冲突
5. **C++ 库兼容**：服务器部署时，启动脚本会自动配置 LD_LIBRARY_PATH 解决 C++ 标准库兼容问题

## 故障排除

### 常见问题

1. **后端启动失败**
   - 检查Python版本是否为3.12+
   - 确认conda虚拟环境已激活：`conda activate babeldoc`
   - 检查依赖是否正确安装：`pip install -r backend/requirements.txt`
   - 查看后端日志：`tail -f /tmp/easy_babeldoc_backend.log`

2. **前端编译错误**
   - 检查Node.js版本是否为18+
   - 删除node_modules重新安装
   - 检查依赖版本兼容性

3. **翻译失败**
   - 检查API密钥是否正确
   - 确认网络连接正常
   - 查看后端日志获取详细错误信息

## 许可证

本项目基于 GNU Affero General Public License (AGPL) v3 许可证开源。

### 重要说明

- 本项目基于 [BabelDOC](https://github.com/funstory-ai/BabelDOC) 开发，BabelDOC 使用 AGPL-3.0 许可证
- 根据 AGPL-3.0 要求，如果您修改本软件并通过网络提供服务，必须向用户提供修改后的源代码
- 完整的许可证文本请参见 [LICENSE](./LICENSE) 文件
- 版权声明和第三方依赖信息请参见 [NOTICE](./NOTICE) 文件

### 源代码获取

- 本项目完整源代码地址：GitHub: https://github.com/tianshaojie/Easy-BabelDOC
- 特别备注本项目fork至：GitHub: https://github.com/lijiapeng365/Easy-BabelDOC

### AGPL-3.0 关键要求

1. **网络使用条款**：如果您修改软件并通过网络提供服务，必须向用户提供源代码
2. **版权保留**：保留所有版权声明和许可证通知
3. **源码分发**：分发时必须包含源代码或提供获取源代码的方式
4. **修改标记**：如有修改，需要明确标记修改内容

如果您计划商业使用或提供在线服务，请确保遵守AGPL-3.0的所有条款。

## 贡献

欢迎提交Issue和Pull Request来改进项目！

在贡献代码前，请确保：
1. 您的代码符合项目的编码规范
2. 添加适当的测试用例
3. 更新相关文档
4. 您同意将贡献的代码以AGPL-3.0许可证发布
