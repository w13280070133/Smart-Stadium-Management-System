<template>
  <div class="center-page" v-loading="loading">
    <!-- 上半部分：个人信息 + 账号与安全 -->
    <el-row :gutter="18" class="top-row">
      <!-- 左：个人资料 -->
      <el-col :span="16">
        <el-card shadow="hover" class="profile-card">
          <template #header>
            <div class="card-header">
              <div>
                <div class="card-title">个人资料</div>
                <div class="card-sub">查看并维护您的基础信息</div>
              </div>
              <div>
                <el-tag size="small" type="success" v-if="profile.status_text === '已启用'">
                  {{ profile.status_text }}
                </el-tag>
                <el-tag size="small" type="danger" v-else>
                  {{ profile.status_text || '未知状态' }}
                </el-tag>
              </div>
            </div>
          </template>

          <div class="profile-body">
            <div class="avatar-block">
              <div class="avatar-circle">
                {{ avatarText }}
              </div>
              <div class="avatar-info">
                <div class="name">{{ profile.name || "未设置姓名" }}</div>
                <div class="mobile">登录手机号：{{ profile.mobile || "-" }}</div>
                <div class="balance">
                  账户余额：
                  <span class="amount">
                    ¥ {{ profile.balance.toFixed(2) }}
                  </span>
                </div>
              <div class="level-chip">
                当前等级：
                <strong>{{ profile.level_name || "普通会员" }}</strong>
                <span class="discount">{{ renderDiscountText(profile.level_discount) }}</span>
              </div>
              </div>
            </div>

            <el-divider />

            <el-form
              :model="editForm"
              :rules="rules"
              ref="formRef"
              label-width="80px"
              size="small"
              class="profile-form"
            >
              <el-form-item label="姓名" prop="name">
                <el-input v-model="editForm.name" placeholder="请输入姓名" maxlength="20" />
              </el-form-item>
              <el-form-item label="手机号" prop="phone">
                <el-input
                  v-model="editForm.phone"
                  placeholder="请输入手机号"
                  maxlength="20"
                />
              </el-form-item>
              <el-form-item>
                <el-button type="primary" :loading="saving" @click="onSaveProfile">
                  保存修改
                </el-button>
                <el-button @click="resetEdit">重置</el-button>
              </el-form-item>
            </el-form>
          </div>
        </el-card>
      </el-col>

      <!-- 右：账号与安全 + 快捷概览 -->
      <el-col :span="12">
        <el-card shadow="hover" class="security-card">
          <template #header>
            <div class="card-header">
              <div class="card-title">账号与安全</div>
            </div>
          </template>

          <div class="security-body">
            <div class="security-item">
              <div class="label">登录账号</div>
              <div class="value">{{ profile.mobile || "-" }}</div>
            </div>
            <div class="security-item">
              <div class="label">账号状态</div>
              <div class="value">
                <el-tag size="small" type="success" v-if="profile.status_text === '已启用'">
                  已启用
                </el-tag>
                <el-tag size="small" type="danger" v-else>
                  {{ profile.status_text || "未知" }}
                </el-tag>
              </div>
            </div>
            <div class="security-item">
              <div class="label">密码</div>
              <div class="value">
                ********
                <el-button
                  type="primary"
                  text
                  size="small"
                  class="link-btn"
                  @click="goChangePassword"
                >
                  修改密码
                </el-button>
              </div>
            </div>
          </div>
        </el-card>

        <el-card shadow="hover" class="stats-card">
          <template #header>
            <div class="card-header">
              <div class="card-title">近期概览</div>
            </div>
          </template>
          <div class="stats-grid">
            <div class="stat-item">
              <div class="label">历史订单数</div>
              <div class="value">{{ stats.total_orders }}</div>
              <div class="desc">场地预约 + 商品消费</div>
            </div>
            <div class="stat-item">
              <div class="label">本月预约次数</div>
              <div class="value">{{ stats.month_reservations }}</div>
              <div class="desc">{{ currentMonthLabel }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 下半部分：近期记录 -->
    <el-row :gutter="18" class="bottom-row">
      <!-- 近期预约 -->
      <el-col :span="12">
        <el-card shadow="hover" class="list-card">
          <template #header>
            <div class="list-header">
              <span>📌 近期场地预约</span>
              <el-button type="primary" text size="small" @click="goReservations">
                查看全部
              </el-button>
            </div>
          </template>

          <div v-if="!recentReservations.length" class="empty-wrapper">
            <el-empty description="暂无预约记录" />
          </div>
          <ul v-else class="list-body">
            <li v-for="item in recentReservations" :key="item.id" class="list-item">
              <div class="item-main">
                <div class="title">
                  {{ item.court_name || "未知场地" }}
                </div>
                <div class="meta">
                  {{ formatDate(item.date) }} {{ item.start_time }} ~ {{ item.end_time }}
                </div>
              </div>
              <div class="item-extra">
                <el-tag size="small">
                  {{ item.status || "-" }}
                </el-tag>
              </div>
            </li>
          </ul>
        </el-card>
      </el-col>

      <!-- 近期订单 -->
      <el-col :span="8">
        <el-card shadow="hover" class="list-card">
          <template #header>
            <div class="list-header">
              <span>🧾 最近订单</span>
              <el-button type="primary" text size="small" @click="goOrders">
                查看全部
              </el-button>
            </div>
          </template>

          <div v-if="!recentOrders.length" class="empty-wrapper">
            <el-empty description="暂无订单记录" />
          </div>
          <ul v-else class="list-body">
            <li v-for="item in recentOrders" :key="item.id" class="list-item">
              <div class="item-main">
                <div class="title">
                  {{ item.type || item.order_no || "订单" }}
                </div>
                <div class="meta">
                  {{ formatDateTime(item.created_at) }}
                </div>
              </div>
              <div class="item-extra amount">
                ¥ {{ Number(item.amount || 0).toFixed(2) }}
              </div>
            </li>
          </ul>
        </el-card>
      </el-col>

    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { ElMessage, FormInstance, FormRules } from "element-plus";
import { useRouter } from "vue-router";
import api from "@/utils/api";

const router = useRouter();

interface Profile {
  id: number | null;
  name: string;
  phone: string;
  mobile: string;
  status: string;
  status_text: string;
  balance: number;
  level?: string;
  level_name?: string;
  level_discount?: number;
}

interface Stats {
  total_orders: number;
  month_reservations: number;
}

interface ReservationItem {
  id?: number;
  court_name?: string;
  date?: string;
  start_time?: string;
  end_time?: string;
  status?: string;
}

interface OrderItem {
  id: string;
  order_no?: string;
  type?: string;
  amount?: number;
  status?: string;
  created_at?: string;
}

const loading = ref(false);
const saving = ref(false);

const profile = ref<Profile>({
  id: null,
  name: "",
  phone: "",
  mobile: "",
  status: "",
  status_text: "",
  balance: 0,
  level: "",
  level_name: "",
  level_discount: 100,
});

const stats = ref<Stats>({
  total_orders: 0,
  month_reservations: 0,
});

const recentReservations = ref<ReservationItem[]>([]);
const recentOrders = ref<OrderItem[]>([]);

// 编辑表单
const editForm = ref({
  name: "",
  phone: "",
});

const formRef = ref<FormInstance>();

const rules: FormRules = {
  name: [{ required: true, message: "请输入姓名", trigger: "blur" }],
  phone: [{ required: true, message: "请输入手机号", trigger: "blur" }],
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

const currentMonthLabel = computed(() => {
  const d = new Date();
  return `${d.getFullYear()} 年 ${d.getMonth() + 1} 月`;
});

function formatDate(val?: string) {
  if (!val) return "-";
  if (/^\d{4}-\d{2}-\d{2}$/.test(val)) return val;
  const d = new Date(val);
  if (Number.isNaN(d.getTime())) return val;
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function formatDateTime(val?: string) {
  if (!val) return "-";
  const d = new Date(val);
  if (Number.isNaN(d.getTime())) return val;
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  return `${y}-${m}-${day} ${hh}:${mm}`;
}

function renderDiscountText(value?: number) {
  if (!value || value >= 100) return "无折扣";
  const raw = value / 10;
  return `${Number.isInteger(raw) ? raw.toFixed(0) : raw.toFixed(1)} 折`;
}

function resetEdit() {
  editForm.value.name = profile.value.name;
  editForm.value.phone = profile.value.mobile || profile.value.phone;
}

/** 保存个人资料 */
async function onSaveProfile() {
  if (!formRef.value) return;
  await formRef.value.validate(async (valid) => {
    if (!valid) return;
    saving.value = true;
    try {
      await api.put("/member/profile", {
        name: editForm.value.name,
        phone: editForm.value.phone,
      });
      ElMessage.success("资料已保存");
      // 更新本地展示
      profile.value.name = editForm.value.name;
      profile.value.phone = editForm.value.phone;
      profile.value.mobile = editForm.value.phone;
    } catch (err: any) {
      console.error(err);
      const msg = err?.response?.data?.detail || "保存失败";
      ElMessage.error(msg);
    } finally {
      saving.value = false;
    }
  });
}

// 路由跳转
const goChangePassword = () => {
  router.push({ path: "/account" });
};
const goReservations = () => {
  router.push({ path: "/reservations" });
};
const goOrders = () => {
  router.push({ path: "/orders" });
};

// 加载数据
async function loadProfile() {
  const res = await api.get("/member/profile");
  const p = res.data || {};
  profile.value = {
    id: p.id ?? null,
    name: p.name || "",
    phone: p.phone || "",
    mobile: p.mobile || p.phone || "",
    status: p.status || "",
    status_text: p.status_text || "已启用",
    balance: Number(p.balance ?? 0),
    level: p.level || "",
    level_name: p.level_name || p.level || "",
    level_discount: Number(p.level_discount ?? 100),
  };
  resetEdit();
}

async function loadOverview() {
  const res = await api.get("/member/overview");
  const ov = res.data || {};
  stats.value = {
    total_orders: Number(ov.total_orders || 0),
    month_reservations: Number(ov.month_reservations || 0),
  };
}

async function loadLists() {
  const [resvRes, ordersRes] = await Promise.all([
    api.get("/member/reservations", { params: { limit: 5 } }),
    api.get("/member/orders", { params: { limit: 5 } }),
  ]);

  recentReservations.value = (resvRes.data || []) as ReservationItem[];
  recentOrders.value = (ordersRes.data || []) as OrderItem[];
}

async function loadAll() {
  loading.value = true;
  try {
    await Promise.all([loadProfile(), loadOverview(), loadLists()]);
  } catch (err: any) {
    console.error(err);
    const msg = err?.response?.data?.detail || "加载个人中心数据失败";
    ElMessage.error(msg);
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadAll();
});
</script>

<style scoped>
.center-page {
  min-height: 100%;
  padding: 20px 24px 32px;
  box-sizing: border-box;
  background: radial-gradient(circle at top left, #f5f7ff 0, #f5f5f7 40%, #f3f4f6 100%);
}

.top-row {
  margin-bottom: 18px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
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

/* 个人资料卡 */
.profile-card {
  border-radius: 18px;
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.08);
  border: 1px solid rgba(148, 163, 184, 0.18);
}

.profile-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.avatar-block {
  display: flex;
  align-items: center;
  gap: 16px;
}

.avatar-circle {
  width: 64px;
  height: 64px;
  border-radius: 999px;
  background: linear-gradient(135deg, #4f46e5, #0ea5e9);
  color: #f9fafb;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: 600;
  box-shadow: 0 18px 30px rgba(37, 99, 235, 0.4);
}

.avatar-info .name {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
}

.avatar-info .mobile {
  font-size: 12px;
  color: #6b7280;
  margin-top: 2px;
}

.avatar-info .balance {
  margin-top: 4px;
  font-size: 13px;
}

.avatar-info .amount {
  font-weight: 600;
  color: #111827;
}

.level-chip {
  margin-top: 4px;
  font-size: 12px;
  color: #6b7280;
  display: flex;
  gap: 4px;
  align-items: baseline;
}

.level-chip .discount {
  color: #4f46e5;
  font-weight: 600;
}

.profile-form {
  max-width: 420px;
}

/* 账号安全卡 & 概览卡 */
.security-card,
.stats-card {
  border-radius: 18px;
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.08);
  border: 1px solid rgba(148, 163, 184, 0.18);
  margin-bottom: 16px;
}

.security-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
  font-size: 13px;
}

.security-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.security-item .label {
  color: #6b7280;
}

.security-item .value {
  color: #111827;
}

.link-btn {
  margin-left: 8px;
  padding: 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.stat-item {
  padding: 6px 4px;
}

.stat-item .label {
  font-size: 12px;
  color: #6b7280;
}

.stat-item .value {
  font-size: 18px;
  font-weight: 600;
  margin-top: 4px;
}

.stat-item .desc {
  font-size: 11px;
  color: #9ca3af;
}

/* 下面三个列表 */
.bottom-row {
  margin-top: 4px;
}

.list-card {
  border-radius: 18px;
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.08);
  border: 1px solid rgba(148, 163, 184, 0.18);
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
  font-weight: 500;
}

.empty-wrapper {
  padding: 24px 0;
}

.list-body {
  list-style: none;
  padding: 0;
  margin: 0;
}

.list-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px dashed rgba(209, 213, 219, 0.7);
  font-size: 12px;
}

.list-item:last-child {
  border-bottom: none;
}

.item-main {
  flex: 1;
  min-width: 0;
}

.item-main .title {
  font-weight: 500;
  color: #111827;
  margin-bottom: 2px;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
}

.item-main .meta {
  color: #6b7280;
}

.item-extra {
  margin-left: 10px;
  flex-shrink: 0;
}

.item-extra.amount {
  font-weight: 600;
  font-size: 13px;
}
</style>
