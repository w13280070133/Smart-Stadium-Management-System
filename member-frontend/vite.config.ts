/// <reference types="vite/client" />

import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// 这是 member-frontend 的配置，不是后台管理的 admin-frontend
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url))
    }
  },
  server: {
    port: 5175,
    proxy: {
      "/api": {
        target: "http://localhost:9000",
        changeOrigin: true
      }
    }
  }
});
