import { defineConfig } from 'vitest/config'
import path from 'path'
import { execSync } from 'child_process'
import { readFileSync } from 'fs'

// Only VITE_ variables are exposed to frontend code. WEB_PORT is used only for dev server config.
const WEB_PORT = process.env.WEB_PORT ? parseInt(process.env.WEB_PORT) : 5173
const API_URL = process.env.VITE_API_URL || process.env.API_BASE_URL || 'http://localhost:8000'

const appVersion = (() => {
  for (const candidate of [path.resolve(__dirname, '../VERSION'), path.resolve(__dirname, 'VERSION'), '/VERSION']) {
    try {
      return readFileSync(candidate, 'utf-8').trim()
    } catch {
      // try next
    }
  }
  return 'unknown'
})()
const gitCommit = (() => {
  try {
    return execSync('git rev-parse --short HEAD', { cwd: __dirname }).toString().trim()
  } catch {
    return 'unknown'
  }
})()
process.env.VITE_APP_VERSION = appVersion
process.env.VITE_APP_COMMIT = gitCommit

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
