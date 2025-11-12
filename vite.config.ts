import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'  // ADD THIS LINE
import { fileURLToPath } from 'url'  // ADD THIS TOO (for __dirname in ESM)

const __dirname = path.dirname(fileURLToPath(import.meta.url))  // ADD THIS

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'build',
    rollupOptions: {
      external: [],
    },
  },
  resolve: {
    alias: {
      // Fixed: Now resolve is defined via path.resolve
      '/index.tsx': path.resolve(__dirname, 'index.tsx'),
    },
  },
})