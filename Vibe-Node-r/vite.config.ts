import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'  // Node path for absolute file lasers

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    include: [
      // Pre-bundle reactflow's scoped internals—fixes Vite ESM load ENOENT in prod
      '@reactflow/core',
      '@reactflow/background',
      '@reactflow/controls',
      '@reactflow/edges',
      '@reactflow/minimap',
      '@reactflow/node-resizer',
      '@reactflow/node-toolbar',
      '@reactflow/nodes'
    ]
  },
  build: {
    rollupOptions: {
      build: {
        outDir: 'build',
      onwarn(warning, warn) {
        if (warning.code === 'MODULE_LEVEL_DIRECTIVE') return;
        warn(warning);
      }
    }
  }
})