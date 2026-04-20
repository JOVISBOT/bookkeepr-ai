import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss()
  ],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true,
      }
    }
  },
  define: {
    // Production API URL for Render backend
    '__API_URL__': JSON.stringify(process.env.NODE_ENV === 'production' 
      ? 'https://bookkeepr-ai.onrender.com/api/v1'
      : '/api/v1'
    ),
  },
})
