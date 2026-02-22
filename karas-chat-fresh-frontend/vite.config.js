import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    proxy: {
      '/api': { target: 'http://localhost:5002', changeOrigin: true },
      '/socket.io': {
        target: 'http://localhost:5002',
        ws: true,
        configure: (proxy) => {
          proxy.on('error', () => {}); // تجاهل أخطاء الاتصال عند توقف الباك اند
        }
      }
    }
  }
})
