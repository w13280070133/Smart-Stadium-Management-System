<template>
  <div class="member-home" v-loading="loading">
    <!-- 顶部欢迎条 -->
    <div class="welcome-banner">
      <div class="welcome-left">
        <div class="hello">
          你好，{{ profile.name || "会员用户" }} 👋
        </div>
        <div class="tip">
          欢迎使用会员自助服务，可以在线预约场地、查看订单。
        </div>
        <div class="base-info">
          <span>手机号：{{ profile.mobile || "-" }}</span>
          <span class="divider">|</span>
          <span>账号状态：{{ profile.status_text || "已启用" }}</span>
        </div>
        <div class="level-badge">
          当前等级：
          <strong>{{ profile.level_name || "普通会员" }}</strong>
          <span class="discount">（{{ renderDiscountText(profile.level_discount) }}）</span>
        </div>
        <div class="action-row">
          <el-button type="primary" size="small" @click="goReservations">
            预约场地
          </el-button>
        </div>
      </div>

      <div class="welcome-right">
        <div class="balance-label">账户余额（元）</div>
        <div class="balance-value">
          ¥ {{ profile.balance.toFixed(2) }}
        </div>
        <div class="balance-sub">余额以前台实际为准</div>
        <div class="quick-links">
  <router-link to="/center" class="link-btn">
    编辑个人信息
  </router-link>
  <router-link to="/account-settings" class="link-btn">
    修改密码
  </router-link>
</div>
      </div>
    </div>

    <!-- 中间：三张统计卡片 -->
    <el-row :gutter="16" class="stat-row">
      <el-col :span="12">
        <div class="stat-card stat-card-blue">
          <div class="stat-card-top">
            <div class="stat-title">历史订单数</div>
            <div class="stat-badge">订单</div>
          </div>
          <div class="stat-value">{{ stats.totalOrders }}</div>
          <div class="stat-sub">包含场地预约、商品消费等</div>
        </div>
      </el-col>

      <el-col :span="12">
        <div class="stat-card stat-card-purple">
          <div class="stat-card-top">
            <div class="stat-title">本月预约次数</div>
            <div class="stat-badge">场地</div>
          </div>
          <div class="stat-value">{{ stats.monthReservations }}</div>
          <div class="stat-sub">{{ currentMonthLabel }}</div>
        </div>
      </el-col>
    </el-row>

    <!-- 底部：左侧近期预约，右侧近期订单 -->
    <el-row :gutter="16" class="bottom-row">
      <!-- 左：近期场地预约 -->
      <el-col :span="12">
        <el-card shadow="hover" class="list-card">
          <template #header>
            <div class="list-header">
              <div class="title">📌 近期场地预约</div>
              <el-button type="primary" text size="small" @click="goReservations">
                查看全部
              </el-button>
            </div>
          </template>

          <div v-if="!recentReservations.length" class="empty-wrapper">
            <el-empty description="暂无预约记录" />
          </div>
          <div v-else class="list-body">
            <div
              v-for="item in recentReservations"
              :key="item.id"
              class="list-item"
            >
              <div class="item-main">
                <div class="item-title">
                  {{ item.court_name || "未知场地" }}
                </div>
                <div class="item-time">
                  {{ formatDate(item.date) }}
                  {{ item.start_time }} ~ {{ item.end_time }}
                </div>
              </div>
              <div class="item-extra">
                <el-tag size="small">
                  {{ item.status || "-" }}
                </el-tag>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 右：最近订单 -->
      <el-col :span="12">
        <el-card shadow="hover" class="list-card">
          <template #header>
            <div class="list-header">
              <div class="title">🧾 最近订单</div>
              <el-button type="primary" text size="small" @click="goOrders">
                查看全部
              </el-button>
            </div>
          </template>

          <div v-if="!recentOrders.length" class="empty-wrapper">
            <el-empty description="暂无订单记录" />
          </div>
          <div v-else class="list-body">
            <div
              v-for="order in recentOrders"
              :key="order.id"
              class="list-item"
            >
              <div class="item-main">
                <div class="item-title">
                  {{ order.type || order.order_no || "订单" }}
                </div>
                <div class="item-time">
                  {{ formatDateTime(order.created_at) }}
                </div>
              </div>
              <div class="item-extra item-extra-right">
                <div class="amount">
                  ¥ {{ Number(order.amount || 0).toFixed(2) }}
                </div>
                <el-tag size="small">
                  {{ order.status || "-" }}
                </el-tag>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import api from "@/utils/api";

const router = useRouter();

interface Profile {
  name: string;
  mobile: string;
  status_text: string;
  balance: number;
  level_name?: string;
  level_discount?: number;
}

interface Stats {
  totalOrders: number;
  monthReservations: number;
}

interface OrderItem {
  id: string;
  order_no?: string;
  type?: string;
  amount?: number;
  status?: string;
  created_at?: string;
}

interface ReservationItem {
  id?: number;
  court_name?: string;
  date?: string;
  start_time?: string;
  end_time?: string;
  status?: string;
  created_at?: string;
}

const loading = ref(false);

const profile = ref<Profile>({
  name: "",
  mobile: "",
  status_text: "",
  balance: 0,
  level_name: "",
  level_discount: 100,
});

const stats = ref<Stats>({
  totalOrders: 0,
  monthReservations: 0,
});

const recentOrders = ref<OrderItem[]>([]);
const recentReservations = ref<ReservationItem[]>([]);

const currentMonthLabel = computed(() => {
  const d = new Date();
  return `${d.getFullYear()} 年 ${d.getMonth() + 1} 月`;
});

const renderDiscountText = (value?: number) => {
  if (!value || value >= 100) return "原价";
  const raw = value / 10;
  return `${Number.isInteger(raw) ? raw.toFixed(0) : raw.toFixed(1)} 折`;
};

/** created_at 倒序排序 */
function sortByCreatedAtDesc<T extends { created_at?: string }>(list: T[]): T[] {
  return [...list].sort((a, b) => {
    const ta = a.created_at ? new Date(a.created_at).getTime() : 0;
    const tb = b.created_at ? new Date(b.created_at).getTime() : 0;
    return tb - ta;
  });
}

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

/** 路由跳转 */
const goReservations = () => {
  router.push({ path: "/reservations" });
};

const goOrders = () => {
  router.push({ path: "/orders" });
};

const goProfile = () => {
  router.push({ path: "/center" });
};

const goChangePassword = () => {
  router.push({ path: "/account-settings" });
};

/** 加载个人资料 */
async function loadProfile() {
  let p: any = null;
  try {
    const profileRes = await api.get("/member/profile");
    p = profileRes.data;
  } catch {
    // 兜底：从本地读取部分信息
    p = {
      name:
        localStorage.getItem("member_name") ||
        localStorage.getItem("memberName") ||
        "",
      mobile:
        localStorage.getItem("member_phone") ||
        localStorage.getItem("memberPhone") ||
        "",
      balance: Number(localStorage.getItem("member_balance") || "0") || 0,
      status_text: "已启用",
    };
  }

  profile.value = {
    name: p.name || "",
    mobile: p.mobile || p.phone || "",
    status_text: p.status_text || p.status || "已启用",
    balance: Number(p.balance ?? 0),
    level_name: p.level_name || p.level || "普通会员",
    level_discount: Number(p.level_discount ?? 100),
  };
}

/** 概览 + 最近订单 + 最近预约 */
async function loadOverviewAndLists() {
  const [overviewRes, ordersRes, reservationsRes] = await Promise.all([
    api.get("/member/overview"),
    api.get<OrderItem[]>("/member/orders", { params: { limit: 5 } }),
    api.get<ReservationItem[]>("/member/reservations", {
      params: { limit: 5 },
    }),
  ]);

  const overview = overviewRes.data || {};

  stats.value = {
    totalOrders: Number(overview.total_orders || 0),
    monthReservations: Number(overview.month_reservations || 0),
  };

  const orders = (ordersRes.data || []) as OrderItem[];
  const reservations = (reservationsRes.data || []) as ReservationItem[];

  recentOrders.value = sortByCreatedAtDesc(orders).slice(0, 5);
  recentReservations.value = sortByCreatedAtDesc(reservations).slice(0, 5);
}

async function loadDashboard() {
  loading.value = true;
  try {
    await Promise.all([loadProfile(), loadOverviewAndLists()]);
  } catch (e) {
    console.error(e);
    ElMessage.error("加载首页数据失败，请稍后重试");
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadDashboard();
});
</script>

<style scoped>
.member-home {
  min-height: 100%;
  padding: 20px 24px 32px;
  box-sizing: border-box;
  background: radial-gradient(circle at top left, #f5f7ff 0, #f5f5f7 40%, #f3f4f6 100%);
}

/* 顶部欢迎条 */
.welcome-banner {
  display: flex;
  justify-content: space-between;
  align-items: stretch;
  padding: 24px 28px;
  border-radius: 20px;
  background: linear-gradient(120deg, #020617, #0b1220);
  color: #f9fafb;
  box-shadow: 0 22px 40px rgba(15, 23, 42, 0.45);
  margin-bottom: 20px;
}

.welcome-left {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.hello {
  font-size: 22px;
  font-weight: 600;
  letter-spacing: 0.03em;
}

.tip {
  font-size: 13px;
  opacity: 0.85;
}

.base-info {
  margin-top: 8px;
  font-size: 12px;
  opacity: 0.9;
}

.base-info .divider {
  margin: 0 8px;
  opacity: 0.5;
}

.level-badge {
  margin-top: 6px;
  font-size: 13px;
  color: #cbd5f5;
  display: flex;
  gap: 6px;
  align-items: baseline;
}

.level-badge .discount {
  font-size: 12px;
  color: #a5b4fc;
}

.action-row {
  margin-top: 14px;
  display: flex;
  gap: 8px;
}

.welcome-right {
  width: 260px;
  margin-left: 32px;
  padding: 16px 18px;
  border-radius: 16px;
  background: radial-gradient(circle at top right, rgba(248, 250, 252, 0.16) 0, rgba(15, 23, 42, 0.85) 60%);
  border: 1px solid rgba(148, 163, 184, 0.4);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.balance-label {
  font-size: 12px;
  opacity: 0.8;
}

.balance-value {
  margin-top: 4px;
  font-size: 30px;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.balance-sub {
  margin-top: 4px;
  font-size: 11px;
  opacity: 0.8;
}

.quick-links {
  margin-top: 10px;
  display: flex;
  justify-content: flex-end;
  gap: 6px;
}

/* 统计卡片 */
.stat-row {
  margin-bottom: 18px;
}

.stat-card {
  border-radius: 16px;
  padding: 16px 18px;
  background: #ffffff;
  box-shadow: 0 14px 30px rgba(15, 23, 42, 0.08);
  border: 1px solid rgba(148, 163, 184, 0.22);
  height: 120px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-sizing: border-box;
}

.stat-card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-title {
  font-size: 13px;
  color: #111827;
}

.stat-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.05);
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  margin-top: 4px;
}

.stat-sub {
  font-size: 11px;
  color: #6b7280;
}

.stat-card-blue .stat-badge {
  background: rgba(59, 130, 246, 0.1);
  color: #2563eb;
}

.stat-card-green .stat-badge {
  background: rgba(52, 211, 153, 0.1);
  color: #059669;
}

.stat-card-purple .stat-badge {
  background: rgba(196, 181, 253, 0.15);
  color: #7c3aed;
}

/* 底部列表卡片 */
.bottom-row {
  margin-top: 4px;
}

.list-card {
  border-radius: 18px;
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.08);
  border: 1px solid rgba(148, 163, 184, 0.18);
  height: 320px;
  display: flex;
  flex-direction: column;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.list-header .title {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
}

.empty-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.list-body {
  flex: 1;
  overflow: hidden;
  padding-top: 4px;
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

.item-title {
  font-weight: 500;
  color: #111827;
  margin-bottom: 2px;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
}

.item-time {
  color: #6b7280;
}

.item-extra {
  margin-left: 12px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
}

.item-extra-right {
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.item-extra-right .amount {
  font-weight: 600;
  font-size: 13px;
  color: #111827;
}


</style>
