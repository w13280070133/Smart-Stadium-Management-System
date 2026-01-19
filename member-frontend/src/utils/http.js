// src/utils/http.ts
import axios from "axios";
import { ElMessage } from "element-plus";
import { getMemberToken, clearMemberAuth } from "./auth";
const instance = axios.create({
    baseURL: "/api",
    timeout: 10000,
});
// 请求拦截：自动注入会员端 Token
instance.interceptors.request.use((config) => {
    const token = getMemberToken?.();
    if (token) {
        config.headers = config.headers ?? {};
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});
instance.interceptors.response.use((response) => {
    const data = response.data;
    // 兼容 { code, msg, data } 和直接返回数据两种风格
    if (data && typeof data === "object" && "code" in data) {
        const anyData = data;
        if (anyData.code === 200) {
            return anyData.data;
        }
        ElMessage.error(anyData.msg || "请求失败");
        return Promise.reject(new Error(anyData.msg || "请求失败"));
    }
    return data;
}, (error) => {
    if (error?.response?.status === 401) {
        clearMemberAuth?.();
    }
    const msg = error.response?.data?.detail ||
        error.response?.data?.msg ||
        error.message ||
        "请求失败";
    ElMessage.error(msg);
    return Promise.reject(error);
});
const http = instance;
export default http;
