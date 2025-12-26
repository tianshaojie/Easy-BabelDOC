import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tsconfigPaths from "vite-tsconfig-paths";
import { traeBadgePlugin } from 'vite-plugin-trae-solo-badge';

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
    traeBadgePlugin({
      variant: 'dark',
      position: 'bottom-right',
      prodOnly: true,
      clickable: true,
      clickUrl: 'https://www.trae.ai/solo?showJoin=1',
      autoTheme: true,
      autoThemeTarget: '#root'
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
