# Nginx Proxy Manager 域名配置指南

## 概述

本文档说明如何使用 Nginx Proxy Manager (NPM) 配置域名 `http://ai.skyui.cn/t`，实现前后端服务的统一访问。

## 架构说明

```
用户访问: http://ai.skyui.cn/t
    ↓
Nginx Proxy Manager (反向代理)
    ↓
    ├─→ /t/*     → 前端服务 (端口 4173)
    └─→ /api/*   → 后端服务 (端口 58273)
```

## Nginx Proxy Manager 配置步骤

### 1. 添加 Proxy Host

登录 Nginx Proxy Manager 管理界面,点击 "Proxy Hosts" → "Add Proxy Host"

#### Details 标签页配置:

| 配置项 | 值 | 说明 |
|--------|-----|------|
| Domain Names | `ai.skyui.cn/t` | 你的域名+路径 |
| Scheme | `http` | 协议类型 |
| Forward Hostname/IP | `localhost` 或服务器IP | 转发目标 |
| Forward Port | `4173` | 前端服务端口 |
| Forward Path | `/` | 转发路径(重要) |
| Cache Assets | ✅ 开启 | 缓存静态资源 |
| Block Common Exploits | ✅ 开启 | 安全防护 |
| Websockets Support | ✅ 开启 | 支持 WebSocket |

**重要说明:**
- Domain Names 填写 `ai.skyui.cn/t` (包含路径)
- Forward Path 填写 `/` (将 `/t` 路径重写为 `/`)
- 这样访问 `http://ai.skyui.cn/t` 会转发到 `http://localhost:4173/`

### 2. 配置 Custom Locations (关键)

在 "Custom Locations" 标签页添加后端 API 路由:

点击 "Add location" 按钮:

| 配置项 | 值 | 说明 |
|--------|-----|------|
| Define Location | `/api` | API 路径前缀 |
| Scheme | `http` | 协议类型 |
| Forward Hostname/IP | `localhost` 或服务器IP | 后端服务地址 |
| Forward Port | `58273` | 后端服务端口 |
| Websockets Support | ✅ 开启 | 支持 WebSocket (翻译进度推送) |

### 3. SSL 配置 (推荐)

在 "SSL" 标签页:

1. 选择 "Request a new SSL Certificate"
2. 勾选 "Force SSL" (强制 HTTPS)
3. 填写邮箱地址
4. 勾选 "I Agree to the Let's Encrypt Terms of Service"
5. 点击 "Save"

配置 SSL 后,访问地址变为: `https://ai.skyui.cn/t`

### 4. Advanced 配置 (可选)

如果需要自定义 Nginx 配置,可以在 "Advanced" 标签页添加:

```nginx
# 增加上传文件大小限制 (如果需要上传大文件)
client_max_body_size 100M;

# 超时设置 (翻译任务可能需要较长时间)
proxy_read_timeout 300s;
proxy_connect_timeout 300s;
proxy_send_timeout 300s;

# 路径重写 (如果 Forward Path 不生效,使用此配置)
rewrite ^/t$ /t/ permanent;
rewrite ^/t/(.*)$ /$1 break;
```

**路径重写说明:**
- `rewrite ^/t$ /t/ permanent;` - 将 `/t` 重定向到 `/t/` (301 永久重定向)
- `rewrite ^/t/(.*)$ /$1 break;` - 将 `/t/xxx` 重写为 `/xxx` 转发给后端

## 工程配置说明

### 前端配置

前端已配置自动识别环境:

- **开发环境** (`npm run dev`): 直接访问 `http://localhost:58273`
- **生产环境** (`npm run build` + `npm run preview`): 通过域名访问 `/api/*`，由 Nginx 反向代理到后端

配置文件: `src/config/api.ts`

```typescript
// 生产环境使用域名(通过 Nginx 反向代理),开发环境使用端口
const isProduction = import.meta.env.PROD
const API_URL = isProduction 
  ? `${API_PROTOCOL}://${API_HOST}` 
  : `${API_PROTOCOL}://${API_HOST}:${API_PORT}`
```

### 环境变量 (可选)

如果需要自定义配置,可以创建 `.env.production` 文件:

```bash
# 强制指定 API 配置 (通常不需要,使用默认即可)
VITE_API_PROTOCOL=https
VITE_API_HOST=ai.skyui.cn
# 生产环境不需要指定端口,由 Nginx 反向代理
```

## 部署流程

### 1. 构建前端

```bash
npm run build
```

### 2. 预览前端 (端口 4173)

```bash
npm run preview
```

或使用 `start.sh` 脚本启动前后端:

```bash
./start.sh
```

### 3. 启动后端 (端口 58273)

```bash
cd backend
python main.py
```

### 4. 配置 Nginx Proxy Manager

按照上述步骤配置域名和反向代理。

### 5. 访问测试

访问: `http://ai.skyui.cn/t` (或 `https://ai.skyui.cn/t` 如果配置了 SSL)

## 验证配置

### 检查前端访问

```bash
curl http://ai.skyui.cn/t
```

应该返回前端页面 HTML。

### 检查 API 访问

```bash
curl http://ai.skyui.cn/api/health
```

应该返回后端健康检查响应:

```json
{
  "status": "healthy",
  "timestamp": "2024-12-26T06:36:00.000Z"
}
```

## 常见问题

### 1. 502 Bad Gateway

**原因**: 后端服务未启动或端口配置错误

**解决**:
- 检查后端服务是否运行: `ps aux | grep python`
- 检查端口是否正确: `netstat -an | grep 58273`
- 检查 NPM Custom Location 配置是否正确

### 2. API 请求 404

**原因**: Custom Location 未配置或路径不匹配

**解决**:
- 确认 NPM 中已添加 `/api` 的 Custom Location
- 检查前端请求路径是否以 `/api/` 开头

### 3. WebSocket 连接失败

**原因**: Websockets Support 未开启

**解决**:
- 在 NPM 的 Details 和 Custom Locations 中都开启 "Websockets Support"

### 4. CORS 错误

**原因**: 跨域配置问题

**解决**:
- 生产环境通过 Nginx 反向代理,前后端同域,不应出现 CORS 问题
- 如果仍有问题,检查后端 CORS 配置

## 总结

通过 Nginx Proxy Manager 的反向代理配置:

✅ 前端和后端统一使用同一个域名  
✅ 无需暴露后端端口号  
✅ 支持 SSL/HTTPS 加密  
✅ 开发环境和生产环境配置自动切换  
✅ 支持 WebSocket 实时通信  

现在你可以通过 `http://ai.skyui.cn/t` 访问完整的应用了！
