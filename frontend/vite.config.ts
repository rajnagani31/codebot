import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig(({ mode }) => {
  // Load .env from project root (one level up from frontend/)
  const env = loadEnv(mode, path.resolve(__dirname, ".."), "");
  const backendPort = env.BACKEND_PORT || "8001";

  return {
    plugins: [react()],
    server: {
      host: "0.0.0.0",
      port: 5173,
      proxy: {
        "/api": {
          target: `http://127.0.0.1:${backendPort}`,
          changeOrigin: true,
        },
      },
    },
  };
});
