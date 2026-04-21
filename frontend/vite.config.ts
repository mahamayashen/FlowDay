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
      // Backend exposes routes at the root (no /api prefix). Proxy every
      // resource the SPA calls. Without these entries Vite falls back to
      // serving index.html, which breaks JSON parsing in React Query.
      '^/(api|projects|tasks|time-entries|schedule-blocks|analytics|weekly-reviews|sync|health|metrics)(/.*|\\?.*)?$': {
        target: 'http://localhost:5060',
        changeOrigin: true,
      },
      '/auth': {
        target: 'http://localhost:5060',
        changeOrigin: true,
        bypass(req) {
          // OAuth providers redirect here via GET — let React Router handle it
          if (req.method === 'GET' && req.url?.match(/^\/auth\/[^/]+\/callback/)) {
            return req.url
          }
        },
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/setupTests.ts'],
  },
})
