import { defineConfig } from 'vitest/config'
import path from 'path'

export default defineConfig({
  test: {
    globals: true,
    setupFiles: './tests/setupTests.ts',
    environment: 'jsdom',
    include: ['tests/**/*.test.ts?(x)'],
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'), // <- This is the fix
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
