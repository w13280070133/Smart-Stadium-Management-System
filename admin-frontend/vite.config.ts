// admin-frontend/vite.config.ts
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { fileURLToPath, URL } from "node:url";

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    port: 5173, // 管理端端口，保持和你现在一致就行
    proxy: {
      // 所有 /api 开头的请求转发到 FastAPI 后端
      "/api": {
        target: "http://localhost:9000",
        changeOrigin: true,
      },
    },
  },
});
