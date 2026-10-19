import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  // Sub-path for hosting under e.g. https://<user>.github.io/<repo>/ (ADR-0004).
  base: process.env.VITE_BASE_PATH || '/',
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      // Proxy API requests to the consolidated single-app backend during development.
      // The admin routes live on the SAME app (app.main, port 8000) — there is no
      // separate :8001 admin service anymore.
      '/api/games': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
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
  }
});
