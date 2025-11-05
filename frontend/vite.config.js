// frontend/vite.config.js (KEMBALI KE DEFAULT LOKAL)
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue' 

export default defineConfig({
  // 2. AKTIFKAN plugin Vue
  plugins: [vue()], 

  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api'), 
      },
    },
  },
})
