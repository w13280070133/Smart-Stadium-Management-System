// admin-frontend/src/utils/http.ts
import axios from "axios";

// 注意：这里用相对路径 /api，真正的后端地址由 Vite 代理去转发
const http = axios.create({
  baseURL: "/api",
  timeout: 15000, // 15 秒超时，配合你现在的提示文案
});

// 请求拦截器：自动带上 token
http.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers = config.headers || {};
    (config.headers as any).Authorization = `Bearer ${token}`;
  }
  return config;
});

// 可选：响应拦截器，方便排查错误
http.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error("HTTP error ->", error);
    return Promise.reject(error);
  }
);

export default http;
