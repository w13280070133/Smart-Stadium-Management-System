<template>
  <div class="login-page">
    <div class="login-card">
      <div class="brand">
        <div class="logo-circle">🏟</div>
        <div class="brand-text">
          <h1>体育馆管理系统</h1>
          <p>简洁 · 高效 · 智能运营</p>
        </div>
      </div>

      <el-form :model="form" @keyup.enter="handleLogin">
        <el-form-item>
          <el-input v-model="form.username" size="large" placeholder="管理员账号" clearable />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="form.password"
            size="large"
            type="password"
            placeholder="登录密码"
            show-password
          />
        </el-form-item>

        <div class="login-actions">
          <el-button
            type="primary"
            size="large"
            class="login-button"
            :loading="loading"
            @click="handleLogin"
          >
            登录
          </el-button>
        </div>

        <p v-if="error" class="error-text">{{ error }}</p>
      </el-form>

      <div class="footer-text">
        <span>适用于体育馆 · 训练营 · 俱乐部的综合管理平台</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import http from "../utils/http";

const router = useRouter();

const form = reactive({
  username: "admin",
  password: "admin123",
});

const loading = ref(false);
const error = ref("");

const fetchAllowedMenusAndActions = async (roleCode: string | null | undefined) => {
  try {
    const res = await http.get("/system-settings/roles-config");
    const roles = res.data?.roles || [];
    const found = roles.find((r: any) => r.code === roleCode);
    const menus = found && Array.isArray(found.menus) && found.menus.length ? found.menus : ["*"];
    const actions = found && Array.isArray(found.actions) && found.actions.length ? found.actions : ["*"];
    const roleName = found?.name || roleCode || "";
    localStorage.setItem("allowed_menus", JSON.stringify(menus));
    localStorage.setItem("allowed_actions", JSON.stringify(actions));
    if (roleName) localStorage.setItem("admin_role_name", roleName);
  } catch (e) {
    localStorage.setItem("allowed_menus", JSON.stringify(["*"]));
    localStorage.setItem("allowed_actions", JSON.stringify(["*"]));
  }
};

async function handleLogin() {
  if (!form.username || !form.password) {
    error.value = "请输入账号和密码";
    return;
  }

  loading.value = true;
  error.value = "";

  try {
    const params = new URLSearchParams();
    params.append("username", form.username);
    params.append("password", form.password);

    const res = await http.post("/auth/token", params, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });

    const data = res.data;
    const token = data.access_token;
    localStorage.setItem("token", token);
    localStorage.setItem("user", JSON.stringify(data.user));
    localStorage.setItem("admin_name", data.user?.username || form.username);

    await fetchAllowedMenusAndActions(data.user?.role);
    router.push("/");
  } catch (e: any) {
    if (e?.response?.data?.detail) {
      error.value = e.response.data.detail;
    } else {
      error.value = "登录失败，请稍后重试";
    }
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
/* ========== Apple iOS 风格登录页 ========== */
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #F2F2F7;
}

.login-card {
  width: 380px;
  padding: 40px 32px 32px;
  border-radius: 20px;
  background: #fff;
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.08);
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 8px;
}

.logo-circle {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: #007AFF;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  color: #fff;
}

.brand-text h1 {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  color: #1D1D1F;
  letter-spacing: -0.02em;
}

.brand-text p {
  margin: 4px 0 0;
  font-size: 13px;
  color: #86868B;
}

.login-actions {
  margin-top: 8px;
}

.login-button {
  width: 100%;
  height: 44px;
  border-radius: 10px;
  font-size: 16px;
  font-weight: 500;
  background: #007AFF;
  border: none;
  transition: background 0.2s;
}

.login-button:hover {
  background: #0066D6;
}

.error-text {
  margin-top: 12px;
  font-size: 14px;
  color: #FF3B30;
  text-align: center;
}

.footer-text {
  margin-top: 4px;
  font-size: 12px;
  color: #86868B;
  text-align: center;
}
</style>
