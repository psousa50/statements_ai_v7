import { defineConfig } from 'vitest/config'
import path from 'path'

// Only VITE_ variables are exposed to frontend code. WEB_PORT is used only for dev server config.
const WEB_PORT = process.env.WEB_PORT ? parseInt(process.env.WEB_PORT) : 5173
const API_URL = process.env.VITE_API_URL || process.env.API_BASE_URL || 'http://localhost:8000'

export default defineConfig({
  test: {
    globals: true,
    setupFiles: './tests/setupTests.ts',
    environment: 'jsdom',
    include: ['tests/**/*.test.ts?(x)'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      include: ['src/**/*'],
      exclude: ['src/**/*.test.ts', 'src/**/*.test.tsx', 'src/main.tsx'],
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'), // <- This is the fix
    },
  },
  server: {
    host: process.env.VITE_DEV_SERVER_HOST || '0.0.0.0',
    port: WEB_PORT,
    proxy: {
      '/api': {
        target: API_URL,
        changeOrigin: true,
      },
    },
  },
})
