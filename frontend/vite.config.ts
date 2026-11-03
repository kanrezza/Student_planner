import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    // Khi chạy `npm run dev`, chuyển /api sang ứng dụng đang chạy bằng Docker (localhost).
    // Trong docker-compose.dev.yml, VITE_API_PROXY trỏ tới service `web` bên trong mạng Compose.
    proxy: {
      '/api': process.env.VITE_API_PROXY ?? 'http://127.0.0.1:8080',
    },
  },
  test: {
    environment: 'jsdom',
    include: ['tests/**/*.test.ts', 'tests/**/*.test.tsx'],
  },
});
