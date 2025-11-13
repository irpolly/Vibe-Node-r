import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      // Fix Rollup resolution for reactflow v11 ESM subpath imports
      '@reactflow/core': 'reactflow/dist/core/index.esm.js',
      '@reactflow/background': 'reactflow/dist/background/index.esm.js',
      '@reactflow/controls': 'reactflow/dist/controls/index.esm.js',
      '@reactflow/edges': 'reactflow/dist/edges/index.esm.js',
      '@reactflow/minimap': 'reactflow/dist/minimap/index.esm.js',
      '@reactflow/node-toolbar': 'reactflow/dist/nodeToolbar/index.esm.js',
      '@reactflow/nodes': 'reactflow/dist/nodes/index.esm.js',
      // Add more if your app uses extras (e.g., connection line)
    }
  },
  build: {
    rollupOptions: {
      // Optional: If ya wanna externalize somethin' else, but skip for now
    }
  }
})