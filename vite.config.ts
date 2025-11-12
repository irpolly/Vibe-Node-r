
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'


export default defineConfig({
  // ... your existing config
  build: {
    outDir: 'build',
    rollupOptions: {
      external: [],  // Explicitly NO externals for /index.tsx
    },
  },
  resolve: {
    alias: {
      '/index.tsx': resolve(__dirname, 'index.tsx'),  // Root alias
    },
  },
});