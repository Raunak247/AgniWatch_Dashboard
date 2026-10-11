import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    host: '0.0.0.0', // Bind to both IPv4 (127.0.0.1) and IPv6 to prevent Windows loopback mismatch
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000', // Explicit IPv4 to prevent Node.js ECONNREFUSED ::1
        changeOrigin: true,
      },
    },
  },
});
