import react from '@vitejs/plugin-react'
import { defineConfig } from 'vitest/config'

// In development the browser talks to this dev server (port 5173), which forwards API
// calls to the Java backend, so the page and the API look like one site and CORS is not needed.
const backend = 'http://localhost:8081'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/prices': backend,
      '/decisions': backend,
    },
  },
  test: {
    environment: 'node',
  },
})
