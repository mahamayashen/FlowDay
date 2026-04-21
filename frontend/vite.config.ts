import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5060',
        changeOrigin: true,
      },
      '/auth': {
        target: 'http://localhost:5060',
        changeOrigin: true,
        bypass(req) {
          // Let the frontend handle OAuth callback GET redirects from providers
          // but proxy POST requests (code exchange) to the backend
          if (req.method === 'GET' && req.url?.match(/^\/auth\/(google|github)\/callback/)) {
            return req.url
          }
        },
      },
      '/projects': {
        target: 'http://localhost:5060',
        changeOrigin: true,
      },
      '/analytics': {
        target: 'http://localhost:5060',
        changeOrigin: true,
      },
      '/schedule-blocks': {
        target: 'http://localhost:5060',
        changeOrigin: true,
      },
      '/time-entries': {
        target: 'http://localhost:5060',
        changeOrigin: true,
      },
      '/sync': {
        target: 'http://localhost:5060',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://localhost:5060',
        changeOrigin: true,
      },
      '/metrics': {
        target: 'http://localhost:5060',
        changeOrigin: true,
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/setupTests.ts'],
    exclude: ['e2e/**', 'node_modules/**'],
  },
})
