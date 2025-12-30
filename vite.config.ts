import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tsconfigPaths from "vite-tsconfig-paths";

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react({
      babel: {
        plugins: [
          'react-dev-locator',
        ],
      },
    }),
    tsconfigPaths()
  ],
  // 开发环境 (npm run dev)
  server: {
    // 设置为 true 即可允许所有域名
    allowedHosts: true, 
    // 同时也建议开启 host: true (即 0.0.0.0)，确保通过 IP 或域名能访问到服务
    host: true
  },

  // 预览环境 (npm run preview)
  preview: {
    // 设置为 true 即可允许所有域名
    allowedHosts: true,
    host: true
  }
})
