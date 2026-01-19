<template>
  <div class="login-page">
    <el-card class="login-card" shadow="hover">
      <div class="title">会员自助服务</div>
      <div class="sub-title">请输入手机号和密码登录</div>

      <el-form :model="form" class="form" @keyup.enter.native="handleLogin">
        <el-form-item>
          <el-input
            v-model="form.phone"
            placeholder="手机号"
            maxlength="11"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="form.password"
            type="password"
            show-password
            placeholder="登录密码"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            class="btn"
            :loading="loading"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>

      <div class="tip">
        如忘记密码，请联系前台工作人员重置。
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import api from "@/utils/api";
import {
  setMemberToken,
  setMemberInfo,
  clearMemberAuth,
} from "@/utils/auth";

const router = useRouter();

const form = reactive({
  phone: "",
  password: "",
});

const loading = ref(false);

async function handleLogin() {
  if (!form.phone || !form.password) {
    ElMessage.error("请输入手机号和密码");
    return;
  }
  loading.value = true;
  try {
    const params = new URLSearchParams();
    params.append("username", form.phone);
    params.append("password", form.password);

    const res = await api.post("/member-auth/token", params, {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    });

    const data = res.data;
    setMemberToken(data.access_token);
    setMemberInfo(data.member);

    ElMessage.success("登录成功");
    router.push("/home");
  } catch (e: any) {
    clearMemberAuth();
    ElMessage.error(e?.response?.data?.detail || "登录失败，请稍后重试");
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.login-page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(circle at top left, #e0f2fe, #f9fafb);
}

.login-card {
  width: 360px;
  padding: 20px 24px 24px;
  border-radius: 18px;
}

.title {
  font-size: 22px;
  font-weight: 600;
  text-align: center;
}

.sub-title {
  margin-top: 4px;
  text-align: center;
  font-size: 13px;
  color: #6b7280;
}

.form {
  margin-top: 18px;
}

.btn {
  width: 100%;
}

.tip {
  margin-top: 8px;
  font-size: 12px;
  color: #9ca3af;
  text-align: center;
}
</style>
