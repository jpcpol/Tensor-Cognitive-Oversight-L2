import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const BACKEND = 'http://localhost:8000'

// All paths that map directly to the TCO Engine backend.
// The SPA lives at /cal/* in production; backend API routes are at /cal/api/*,
// /vector/*, /tensor/*, /inference/*, /policy/*, /health.
const BACKEND_PATHS = ['/cal/api', '/vector', '/tensor', '/inference', '/policy', '/health']

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: Object.fromEntries(
      BACKEND_PATHS.map((path) => [
        path,
        { target: BACKEND, changeOrigin: true, secure: false },
      ])
    ),
  },
  build: {
    target: 'es2022',
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        // Split heavy vendor libs into cacheable chunks (charts rarely change)
        manualChunks: {
          react: ['react', 'react-dom'],
          charts: ['recharts'],
        },
      },
    },
  },
  // Ensure all non-matched paths serve index.html (SPA fallback)
  preview: { port: 3000 },
})
