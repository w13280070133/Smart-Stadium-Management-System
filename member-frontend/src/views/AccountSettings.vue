<template>
  <div class="account-page" v-loading="loading">
    <div class="page-header">
      <div>
        <h2>账号与安全</h2>
        <p>修改登录密码，保障您的账户安全</p>
      </div>
      <el-tag v-if="profile.status_text === '已启用'" type="success" size="small">
        {{ profile.status_text }}
      </el-tag>
      <el-tag v-else type="danger" size="small">
        {{ profile.status_text || "未知状态" }}
      </el-tag>
    </div>

    <el-row :gutter="20">
      <!-- 左：修改密码表单 -->
      <el-col :span="14">
        <el-card shadow="hover" class="form-card">
          <template #header>
            <div class="card-header">
              <div class="card-title">修改登录密码</div>
              <div class="card-sub">
                当前登录手机号：{{ profile.mobile || "-" }}
              </div>
            </div>
          </template>

          <el-form
            ref="formRef"
            :model="form"
            :rules="rules"
            label-width="100px"
            size="large"
            class="password-form"
          >
            <el-form-item label="当前密码" prop="old_password">
              <el-input
                v-model="form.old_password"
                type="password"
                show-password
                autocomplete="current-password"
                placeholder="请输入当前登录密码"
              />
            </el-form-item>

            <el-form-item label="新密码" prop="new_password">
              <el-input
                v-model="form.new_password"
                type="password"
                show-password
                autocomplete="new-password"
                placeholder="请输入新密码，至少 6 位"
              />
            </el-form-item>

            <el-form-item label="确认新密码" prop="confirm_password">
              <el-input
                v-model="form.confirm_password"
                type="password"
                show-password
                autocomplete="new-password"
                placeholder="请再次输入新密码"
              />
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                :loading="submitting"
                @click="onSubmit"
              >
                确认修改
              </el-button>
              <el-button @click="onReset">重置</el-button>
            </el-form-item>
          </el-form>

          <div class="tips">
            <div class="tips-title">安全小提示</div>
            <ul>
              <li>建议定期更换密码，避免与其他网站使用相同密码。</li>
              <li>密码中尽量包含数字、字母和符号，提升复杂度。</li>
              <li>如发现账号异常，请尽快联系场馆工作人员处理。</li>
            </ul>
          </div>
        </el-card>
      </el-col>

      <!-- 右：账号信息概览 -->
      <el-col :span="10">
        <el-card shadow="hover" class="info-card">
          <template #header>
            <div class="card-header">
              <div class="card-title">账号信息</div>
            </div>
          </template>

          <div class="info-body">
            <div class="avatar-circle">
              {{ avatarText }}
            </div>
            <div class="info-main">
              <div class="name">{{ profile.name || "会员用户" }}</div>
              <div class="mobile">登录手机号：{{ profile.mobile || "-" }}</div>
              <div class="status">
                账号状态：
                <span v-if="profile.status_text === '已启用'">已启用</span>
                <span v-else>{{ profile.status_text || "未知" }}</span>
              </div>
              <div class="balance">
                当前余额：
                <span class="amount">
                  ¥ {{ profile.balance.toFixed(2) }}
                </span>
              </div>
            </div>
          </div>

          <el-divider />

          <div class="logout-block">
            <div class="tip">
              修改密码后，建议重新登录以确保安全。
            </div>
            <el-button type="danger" plain @click="logout">
              退出当前登录
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, FormInstance, FormRules } from "element-plus";
import api from "@/utils/api";

const router = useRouter();

interface Profile {
  id: number | null;
  name: string;
  mobile: string;
  status_text: string;
  balance: number;
}

const loading = ref(false);
const submitting = ref(false);

const profile = ref<Profile>({
  id: null,
  name: "",
  mobile: "",
  status_text: "",
  balance: 0,
});

const form = ref({
  old_password: "",
  new_password: "",
  confirm_password: "",
});

const formRef = ref<FormInstance>();

const rules: FormRules = {
  old_password: [{ required: true, message: "请输入当前密码", trigger: "blur" }],
  new_password: [
    { required: true, message: "请输入新密码", trigger: "blur" },
    {
      min: 6,
      message: "新密码长度不能少于 6 位",
      trigger: "blur",
    },
  ],
  confirm_password: [
    { required: true, message: "请确认新密码", trigger: "blur" },
    {
      validator: (_rule, value, callback) => {
        if (!value) {
          callback(new Error("请确认新密码"));
        } else if (value !== form.value.new_password) {
          callback(new Error("两次输入的新密码不一致"));
        } else {
          callback();
        }
      },
      trigger: "blur",
    },
  ],
};

const avatarText = computed(() => {
  if (profile.value.name) {
    return profile.value.name.slice(-2);
  }
  if (profile.value.mobile) {
    return profile.value.mobile.slice(-2);
  }
  return "会员";
});

async function loadProfile() {
  loading.value = true;
  try {
    const res = await api.get("/member/profile");
    const p = res.data || {};
    profile.value = {
      id: p.id ?? null,
      name: p.name || "",
      mobile: p.mobile || p.phone || "",
      status_text: p.status_text || "已启用",
      balance: Number(p.balance ?? 0),
    };
  } catch (err: any) {
    console.error(err);
    const msg = err?.response?.data?.detail || "加载账号信息失败";
    ElMessage.error(msg);
  } finally {
    loading.value = false;
  }
}

function onReset() {
  form.value.old_password = "";
  form.value.new_password = "";
  form.value.confirm_password = "";
}

async function onSubmit() {
  if (!formRef.value) return;
  await formRef.value.validate(async (valid) => {
    if (!valid) return;
    submitting.value = true;
    try {
      await api.post("/member/change-password", {
        old_password: form.value.old_password,
        new_password: form.value.new_password,
      });
      ElMessage.success("密码修改成功，请使用新密码重新登录");
      // 简单处理：清掉本地 token，跳回登录页
      localStorage.removeItem("member_token");
      router.push({ path: "/login" });
    } catch (err: any) {
      console.error(err);
      const msg = err?.response?.data?.detail || "修改密码失败";
      ElMessage.error(msg);
    } finally {
      submitting.value = false;
    }
  });
}

function logout() {
  localStorage.removeItem("member_token");
  router.push({ path: "/login" });
}

onMounted(() => {
  loadProfile();
});
</script>

<style scoped>
.account-page {
  min-height: 100%;
  padding: 20px 24px 32px;
  box-sizing: border-box;
  background: radial-gradient(circle at top left, #f5f7ff 0, #f5f5f7 40%, #f3f4f6 100%);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #111827;
}

.page-header p {
  margin: 2px 0 0;
  font-size: 13px;
  color: #6b7280;
}

.form-card,
.info-card {
  border-radius: 18px;
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.08);
  border: 1px solid rgba(148, 163, 184, 0.18);
}

.card-header {
  display: flex;
  flex-direction: column;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #111827;
}

.card-sub {
  font-size: 12px;
  color: #6b7280;
  margin-top: 2px;
}

.password-form {
  max-width: 460px;
}

.tips {
  margin-top: 18px;
  padding-top: 10px;
  border-top: 1px dashed rgba(209, 213, 219, 0.8);
  font-size: 12px;
  color: #6b7280;
}

.tips-title {
  font-weight: 500;
  margin-bottom: 6px;
}

.tips ul {
  padding-left: 16px;
  margin: 0;
}

/* 右侧账号卡片 */
.info-body {
  display: flex;
  align-items: center;
  gap: 16px;
}

.avatar-circle {
  width: 68px;
  height: 68px;
  border-radius: 999px;
  background: linear-gradient(135deg, #4f46e5, #0ea5e9);
  color: #f9fafb;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  font-weight: 600;
  box-shadow: 0 18px 30px rgba(37, 99, 235, 0.4);
}

.info-main .name {
  font-size: 17px;
  font-weight: 600;
  color: #111827;
}

.info-main .mobile,
.info-main .status {
  font-size: 13px;
  color: #6b7280;
  margin-top: 2px;
}

.info-main .balance {
  margin-top: 6px;
  font-size: 13px;
}

.info-main .amount {
  font-weight: 600;
  color: #111827;
}

.logout-block {
  margin-top: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #6b7280;
}

.logout-block .tip {
  max-width: 200px;
}
</style>
