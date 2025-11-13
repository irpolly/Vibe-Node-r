import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'  // Node path for absolute file lasers

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      // Laser aliases for reactflow v11 scoped internals—bypass exports drama
      '@reactflow/core': path.resolve(__dirname, './node_modules/@reactflow/core/dist/esm/index.mjs'),
      '@reactflow/background': path.resolve(__dirname, './node_modules/@reactflow/background/dist/esm/index.mjs'),
      '@reactflow/controls': path.resolve(__dirname, './node_modules/@reactflow/controls/dist/esm/index.mjs'),
      '@reactflow/edges': path.resolve(__dirname, './node_modules/@reactflow/edges/dist/esm/index.mjs'),
      '@reactflow/minimap': path.resolve(__dirname, './node_modules/@reactflow/minimap/dist/esm/index.mjs'),
      '@reactflow/node-toolbar': path.resolve(__dirname, './node_modules/@reactflow/node-toolbar/dist/esm/index.mjs'),
      '@reactflow/nodes': path.resolve(__dirname, './node_modules/@reactflow/nodes/dist/esm/index.mjs'),
      // Pro Tip: Add '@reactflow/node-resizer' if your canvas resizes nodes
    }
  },
  build: {
    rollupOptions: {
      // Optional: Dedupe reactflow deps to squash any shadow versions
      external: [],  // Keep all bundled
      onwarn(warning, warn) {
        if (warning.code === 'MODULE_LEVEL_DIRECTIVE') return  // Silence ESM nags if any
      }
    }
  }
})