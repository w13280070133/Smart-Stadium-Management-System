// member-frontend/src/utils/api.ts
import axios, { type AxiosInstance } from "axios";
import { getMemberToken, clearMemberAuth } from "./auth";

const api: AxiosInstance = axios.create({
  baseURL: "http://localhost:9000/api",
  timeout: 10000,
});

// 请求拦截：自动带上会员 Token
api.interceptors.request.use((config) => {
  const token = getMemberToken();
  if (token) {
    config.headers = config.headers ?? {};
    (config.headers as any).Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截：401 时清理本地登录信息，交给路由守卫跳登录
api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error?.response?.status === 401) {
      clearMemberAuth();
    }
    return Promise.reject(error);
  }
);

export default api;
