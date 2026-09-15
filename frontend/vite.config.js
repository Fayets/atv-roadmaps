import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// El backend corre en 8014 (ver docs/plantilla-inicio-proyecto.md y el deploy).
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5182,
    proxy: {
      '/api': { target: 'http://127.0.0.1:8014', changeOrigin: true },
    },
  },
})
