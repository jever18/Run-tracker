import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig(({ mode }) => ({
  plugins: [vue()],

  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5000', // Alamat backend Flask
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '/api'), 
      },
    },
  },

  build: {
    outDir: '../backend/dist', 
    
    emptyOutDir: true, 
    
  },
  
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  }
}));
