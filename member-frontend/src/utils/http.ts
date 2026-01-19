// src/utils/http.ts
import axios, {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
} from "axios";
import { ElMessage } from "element-plus";
import { getMemberToken, clearMemberAuth } from "./auth";

interface HttpInstance {
  get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T>;
  post<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<T>;
  put<T = any>(
    url: string,
    data?: any,
    config?: AxiosRequestConfig
  ): Promise<T>;
  delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T>;
}

const instance: AxiosInstance = axios.create({
  baseURL: "/api",
  timeout: 10000,
});

// 请求拦截：自动注入会员端 Token
instance.interceptors.request.use((config) => {
  const token = getMemberToken?.();
  if (token) {
    config.headers = config.headers ?? {};
    (config.headers as any).Authorization = `Bearer ${token}`;
  }
  return config;
});

instance.interceptors.response.use(
  (response: AxiosResponse) => {
    const data = response.data;

    // 兼容 { code, msg, data } 和直接返回数据两种风格
    if (data && typeof data === "object" && "code" in data) {
      const anyData = data as { code: number; msg?: string; data?: any };
      if (anyData.code === 200) {
        return anyData.data as any;
      }
      ElMessage.error(anyData.msg || "请求失败");
      return Promise.reject(new Error(anyData.msg || "请求失败"));
    }

    return data;
  },
  (error) => {
    if (error?.response?.status === 401) {
      clearMemberAuth?.();
    }
    const msg =
      error.response?.data?.detail ||
      error.response?.data?.msg ||
      error.message ||
      "请求失败";
    ElMessage.error(msg);
    return Promise.reject(error);
  }
);

const http = instance as unknown as HttpInstance;

export default http;
