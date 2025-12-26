# 本地开发指南

## 问题说明

使用 `./start.sh` 启动服务时遇到的常见问题:

### 问题 1: API 请求失败 (ERR_CONNECTION_REFUSED)

**错误信息:**
```
GET http://localhost/api/files/stats net::ERR_CONNECTION_REFUSED
```

**原因:**
- `./start.sh` 默认使用**生产模式** (`npm run build` + `npm run preview`)
- 之前的配置在生产模式下会访问 `http://localhost/api/...` (无端口号)
- 但本地后端运行在 `http://localhost:58273`

**已修复:**
- 修改了 `src/config/api.ts`,本地开发(localhost)总是使用端口号 `58273`
- 生产环境(域名)才通过 Nginx 反向代理,不使用端口号

### 问题 2: 后端启动失败 (ModuleNotFoundError)

**错误信息:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**原因:**
- Python 环境缺少依赖包

**解决方法:**
```bash
cd backend
pip install -r requirements.txt
```

## 正确的启动方式

### 方式一: 开发模式 (推荐本地开发)

```bash
./start.sh dev
```

**特点:**
- ✅ 前端支持热重载 (修改代码自动刷新)
- ✅ 前端运行在 `http://localhost:5173` (Vite 开发服务器)
- ✅ 后端运行在 `http://localhost:58273`
- ✅ 前端自动访问 `http://localhost:58273/api/...`
- ✅ 适合本地开发调试

**启动流程:**
1. 后台启动后端服务
2. 前台运行前端开发服务器 (按 Ctrl+C 停止)

### 方式二: 生产模式 (用于服务器部署)

```bash
./start.sh
```

**特点:**
- ✅ 前端构建生产版本 (优化、压缩)
- ✅ 前端运行在 `http://localhost:4173` (Vite 预览服务器)
- ✅ 后端运行在 `http://localhost:58273`
- ✅ **修复后**: 本地也能正常访问 `http://localhost:58273/api/...`
- ✅ 适合服务器部署、生产环境测试

**启动流程:**
1. 后台启动后端服务
2. 构建前端 (`npm run build`)
3. 后台启动前端预览服务

### 方式三: 仅启动后端

```bash
./start.sh backend
```

### 方式四: 仅启动前端

```bash
./start.sh frontend
```

## 完整部署流程

### 1. 安装依赖

**后端依赖:**
```bash
cd backend
pip install -r requirements.txt
```

**前端依赖:**
```bash
npm install
```

### 2. 本地开发

```bash
./start.sh dev
```

访问: `http://localhost:5173`

### 3. 停止服务

```bash
./stop.sh
```

### 4. 查看日志

```bash
# 后端日志
tail -f /tmp/easy_babeldoc_backend.log

# 前端日志
tail -f /tmp/easy_babeldoc_frontend.log
```

## API 配置说明

### 配置逻辑 (src/config/api.ts)

```typescript
// 判断是否需要使用端口号
// 本地开发(localhost/127.0.0.1)总是使用端口号
// 生产环境(域名)通过 Nginx 反向代理,不使用端口号
const isLocalhost = API_HOST === 'localhost' || API_HOST === '127.0.0.1'
const usePort = isLocalhost || import.meta.env.VITE_USE_PORT === 'true'
```

### 不同场景的 API 地址

| 场景 | 前端地址 | API 地址 | 说明 |
|------|---------|---------|------|
| 开发模式 (`./start.sh dev`) | `http://localhost:5173` | `http://localhost:58273/api/...` | 热重载 |
| 生产模式 (`./start.sh`) | `http://localhost:4173` | `http://localhost:58273/api/...` | 本地预览 |
| 服务器部署 (Nginx) | `http://ai.skyui.cn/t` | `http://ai.skyui.cn/api/...` | 反向代理 |

## 环境变量配置 (可选)

创建 `.env.local` 文件 (本地开发):

```bash
# 强制使用端口号 (通常不需要,自动检测)
VITE_USE_PORT=true

# 自定义后端端口
VITE_API_PORT=58273

# 自定义后端地址
VITE_API_HOST=localhost
VITE_API_PROTOCOL=http
```

创建 `.env.production` 文件 (生产环境):

```bash
# 生产环境通常不需要配置,使用默认值即可
# 如果需要强制使用端口号
VITE_USE_PORT=true
```

## 常见问题

### Q1: 为什么 `./start.sh` 不带 `dev` 会报错?

**A:** 之前的配置有问题,现在已修复。不带 `dev` 也能正常工作,但推荐本地开发使用 `./start.sh dev` 以获得热重载功能。

### Q2: 开发模式和生产模式有什么区别?

**A:**
- **开发模式**: 前端支持热重载,修改代码自动刷新,适合开发调试
- **生产模式**: 前端构建优化版本,适合服务器部署和生产环境测试

### Q3: 如何在服务器上部署?

**A:** 参考 `docs/nginx-proxy-manager-setup.md` 和 `docs/nginx-path-config.md`

### Q4: 后端启动失败怎么办?

**A:** 检查 Python 依赖是否安装:
```bash
cd backend
pip install -r requirements.txt
```

### Q5: 前端访问 API 失败怎么办?

**A:** 
1. 确认后端已启动: `curl http://localhost:58273/api/health`
2. 检查后端日志: `tail -f /tmp/easy_babeldoc_backend.log`
3. 确认配置正确: 本地开发会自动使用 `localhost:58273`

## 总结

- ✅ **本地开发**: 使用 `./start.sh dev` (推荐)
- ✅ **生产测试**: 使用 `./start.sh`
- ✅ **服务器部署**: 使用 `./start.sh` + Nginx 反向代理
- ✅ **配置已修复**: 本地开发(localhost)总是使用端口号 `58273`
- ✅ **无需手动配置**: 自动识别本地/生产环境
