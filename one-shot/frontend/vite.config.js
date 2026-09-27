import {defineConfig} from 'vite';

export default defineConfig({
  server: {
    port: Number(process.env.FRONTEND_PORT || 5173),
    strictPort: true,
    proxy: {
      '/api': {target: process.env.BACKEND_URL || 'http://127.0.0.1:4101', changeOrigin: true, ws: true},
    },
  },
});
