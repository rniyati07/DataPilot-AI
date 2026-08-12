import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    // The backend's CORS_ALLOWED_ORIGINS only permits http://localhost:5173.
    // Without strictPort, Vite silently falls back to 5174 when 5173 is busy,
    // and every API call is then blocked by CORS — which surfaces in the UI as
    // "Backend unreachable". Failing loudly on a busy port is far easier to
    // diagnose than a running app that cannot talk to its own backend.
    strictPort: true,
  },
})
