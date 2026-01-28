// admin-frontend/src/utils/request.ts
import axios from "axios";
import type { AxiosRequestConfig, AxiosResponse } from "axios";

const service = axios.create({
  baseURL: "/api", // 你后端 FastAPI 通过 /api 代理的话就保持这样
  timeout: 10000,
});

// 请求拦截器：自动携带 Token
service.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers = config.headers || {};
      (config.headers as any).Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器：统一只返回 data
service.interceptors.response.use(
  (response: AxiosResponse) => {
    // 如果你的后端统一返回 { code, msg, data }，可以在这里做一些校验
    return response;
  },
  (error) => {
    return Promise.reject(error);
  }
);

export default service;

// 如果你想在别的地方用类型，也可以这样导出：
export type RequestConfig = AxiosRequestConfig;
