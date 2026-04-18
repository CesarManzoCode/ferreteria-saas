import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    // usePolling es necesario para hot reload en volúmenes Docker montados.
    // Sin esto, Vite no detecta cambios de archivos en Linux con volúmenes.
    watch: { usePolling: true },
    // Proxy: en desarrollo, /api/... se redirige al backend dentro de Docker.
    // El browser llama a localhost:5173/api/... → Vite lo manda a backend:8000
    // Esto evita problemas de CORS y hace que todo funcione igual que producción.
    proxy: {
      '/api': {
        target: 'http://backend:8000',
        changeOrigin: true,
      },
    },
  },
})
