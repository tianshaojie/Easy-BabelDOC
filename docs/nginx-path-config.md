# Nginx 路径配置说明

## 问题说明

之前的 `vite.config.ts` 中设置了 `base: '/t/'`,导致:
- ❌ 访问 `http://ai.skyui.cn/t` 无法正常工作
- ✅ 必须访问 `http://ai.skyui.cn/t/` (带结尾斜杠) 才能工作

## 解决方案

### 1. 移除 Vite base 配置

已将 `vite.config.ts` 中的 `base: '/t/'` 配置移除,改为在 Nginx 层面处理路径映射。

### 2. Nginx Proxy Manager 配置

#### 方法一: 使用 Forward Path (推荐)

在 NPM 添加 Proxy Host 时:

```
Domain Names: ai.skyui.cn/t
Scheme: http
Forward Hostname/IP: localhost
Forward Port: 4173
Forward Path: /
```

**工作原理:**
- 用户访问: `http://ai.skyui.cn/t` 或 `http://ai.skyui.cn/t/xxx`
- Nginx 转发: `http://localhost:4173/` 或 `http://localhost:4173/xxx`
- 路径 `/t` 被自动去除

#### 方法二: 使用 Advanced 配置

如果 Forward Path 不生效,在 "Advanced" 标签页添加:

```nginx
# 自动重定向 /t 到 /t/
rewrite ^/t$ /t/ permanent;

# 去除 /t 前缀,转发给后端
rewrite ^/t/(.*)$ /$1 break;
```

**工作原理:**
- 访问 `http://ai.skyui.cn/t` → 301 重定向到 `http://ai.skyui.cn/t/`
- 访问 `http://ai.skyui.cn/t/home` → 转发到 `http://localhost:4173/home`

### 3. API 路径配置

API 路径保持不变,在 Custom Locations 添加:

```
Define Location: /api
Scheme: http
Forward Hostname/IP: localhost
Forward Port: 58273
```

**注意:** API 路径不需要重写,因为前端请求的就是 `/api/*`,直接转发即可。

## 完整配置示例

### NPM Proxy Host 配置

**Details 标签页:**
```
Domain Names: ai.skyui.cn/t
Scheme: http
Forward Hostname/IP: localhost
Forward Port: 4173
Forward Path: /
Cache Assets: ✅
Block Common Exploits: ✅
Websockets Support: ✅
```

**Custom Locations 标签页:**
```
Location: /api
Scheme: http
Forward Hostname/IP: localhost
Forward Port: 58273
Websockets Support: ✅
```

**Advanced 标签页 (可选):**
```nginx
client_max_body_size 100M;
proxy_read_timeout 300s;
proxy_connect_timeout 300s;
proxy_send_timeout 300s;

# 如果 Forward Path 不生效,取消下面两行注释
# rewrite ^/t$ /t/ permanent;
# rewrite ^/t/(.*)$ /$1 break;
```

## 验证配置

### 1. 测试前端访问

```bash
# 不带斜杠
curl -I http://ai.skyui.cn/t

# 带斜杠
curl -I http://ai.skyui.cn/t/

# 子路径
curl -I http://ai.skyui.cn/t/home
```

都应该返回 `200 OK` 或 `301/302` 重定向。

### 2. 测试 API 访问

```bash
curl http://ai.skyui.cn/api/health
```

应该返回后端健康检查响应。

## 路径映射总结

| 用户访问 | Nginx 转发 | 说明 |
|---------|-----------|------|
| `http://ai.skyui.cn/t` | `http://localhost:4173/` | 前端首页 |
| `http://ai.skyui.cn/t/` | `http://localhost:4173/` | 前端首页 |
| `http://ai.skyui.cn/t/home` | `http://localhost:4173/home` | 前端路由 |
| `http://ai.skyui.cn/api/health` | `http://localhost:58273/api/health` | 后端 API |

## 注意事项

1. ✅ **已移除** `vite.config.ts` 中的 `base: '/t/'` 配置
2. ✅ 路径映射由 Nginx 处理,前端无需关心
3. ✅ 开发环境和生产环境使用相同的前端代码
4. ✅ 支持 `/t` 和 `/t/` 两种访问方式
