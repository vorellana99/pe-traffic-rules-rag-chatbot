import path from "node:path";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: true,
    port: 5173,
    // El bind-mount en Windows/WSL2 no propaga eventos inotify; se usa polling
    // para que el HMR detecte los cambios de archivos de forma fiable.
    watch: { usePolling: true, interval: 300 },
    // Proxy al backend: /api -> api:8000 (nombre del servicio en docker compose).
    proxy: {
      "/api": {
        target: "http://api:8000",
        changeOrigin: true,
      },
    },
  },
});
