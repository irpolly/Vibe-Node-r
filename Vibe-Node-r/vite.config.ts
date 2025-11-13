// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'build'  // ← This makes Vite output to /app/build
  },
  optimizeDeps: {
    include: [
      '@reactflow/core',
      '@reactflow/background',
      '@reactflow/controls',
      '@reactflow/edges',
      '@reactflow/minimap',
      '@reactflow/node-resizer',
      '@reactflow/node-toolbar',
      '@reactflow/nodes'
    ]
  }
})