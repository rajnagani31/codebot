import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig(({ mode }) => {
  // Load .env from project root (codebot/) and apps/ directory
  const rootEnv = loadEnv(mode, path.resolve(__dirname, "../.."), "");
  const appsEnv = loadEnv(mode, path.resolve(__dirname, ".."), "");
  const env = { ...appsEnv, ...rootEnv };

  const backendPort = env.BACKEND_PORT || process.env.BACKEND_PORT || "8000";
  const backendTarget =
    env.VITE_BACKEND_URL || env.BACKEND_URL || `http://127.0.0.1:${backendPort}`;

  return {
    plugins: [react()],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    server: {
      host: "0.0.0.0",
      port: 5173,
      proxy: {
        "/api": {
          target: backendTarget,
          changeOrigin: true,
        },
      },
    },
  };
});
