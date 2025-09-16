import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      // Proxy API requests to microservices during development
      '/api/games': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      },
      '/api/admin': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/admin/, '')
      }
    }
  },
  resolve: {
    alias: {
      '@': '/src',
    },
  },
  define: {
    // Ensure environment variables are available at build time
    __GAME_API_URL__: JSON.stringify(process.env.VITE_GAME_API_URL || 'http://localhost:8000'),
    __ADMIN_API_URL__: JSON.stringify(process.env.VITE_ADMIN_API_URL || 'http://localhost:8001'),
  }
});