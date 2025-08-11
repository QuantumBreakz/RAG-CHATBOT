import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    exclude: ['lucide-react'],
  },
  server: {
    proxy: {
      '/api/models': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        // Don't rewrite: keep /api prefix for online model endpoints
      },
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
      '/query': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        // No rewrite: forward as-is
      },
      '/upload': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/upload/, '/upload'),
      },
      '/history': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/history/, '/history'),
      },
    },
  },
});