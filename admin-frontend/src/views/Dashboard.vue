<template>
  <div class="dashboard">
    <div class="page-header">
      <div>
        <h2>📊 数据总览</h2>
        <p class="sub-title">快速查看今日/本月预约、收入与会员数据，掌握最新预约和收支</p>
      </div>
    </div>

    <el-row :gutter="20" class="stats-row">
      <el-col :span="6">
        <el-card class="stat-card stat-blue" shadow="hover" :loading="loadingOverview">
          <div class="label">今日预约数</div>
          <div class="value">{{ overview?.today_reservations ?? 0 }}</div>
          <div class="sub">今日新建的场地预约</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card stat-green" shadow="hover" :loading="loadingOverview">
          <div class="label">本月预约数</div>
          <div class="value">{{ overview?.month_reservations ?? 0 }}</div>
          <div class="sub">自然月累计预约数</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card stat-orange" shadow="hover" :loading="loadingOverview">
          <div class="label">今日收入（元）</div>
          <div class="value">¥ {{ formatMoney(overview?.today_income ?? 0) }}</div>
          <div class="sub">包含场地预约与商品售卖</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="stat-card stat-purple" shadow="hover" :loading="loadingOverview">
          <div class="label">本月收入（元）</div>
          <div class="value">¥ {{ formatMoney(overview?.month_income ?? 0) }}</div>
          <div class="sub">自然月累计收入</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="stats-row">
      <el-col :span="12">
        <el-card class="mini-card" shadow="hover" :loading="loadingOverview">
          <div class="mini-title">会员总数</div>
          <div class="mini-value">{{ overview?.member_count ?? 0 }}</div>
          <div class="mini-sub">当前系统内有效会员人数</div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="mini-card" shadow="hover" :loading="loadingOverview">
          <div class="mini-title">会员余额总额（元）</div>
          <div class="mini-value">¥ {{ formatMoney(overview?.member_balance ?? 0) }}</div>
          <div class="mini-sub">所有会员账户余额之和</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="lists-row">
      <el-col :span="12">
        <el-card class="list-card" shadow="hover" :loading="loadingReservations">
          <div class="list-header">
            <div class="title">最近预约</div>
            <div class="tip">从场地预约记录中取最近 5 条</div>
          </div>

          <el-table :data="latestReservations" size="small" v-if="latestReservations.length" border>
            <el-table-column prop="court_name" label="场地" width="120" />
            <el-table-column prop="member_name" label="会员" width="120">
              <template #default="{ row }">
                <span v-if="row.member_name">{{ row.member_name }}</span>
                <span v-else class="text-muted">散客</span>
              </template>
            </el-table-column>
            <el-table-column prop="start_time" label="开始时间" width="160" />
            <el-table-column prop="status" label="状态" width="80">
              <template #default="{ row }">
                <el-tag v-if="row.status === '已预约'" type="warning" size="small">已预约</el-tag>
                <el-tag v-else-if="row.status === '进行中' || row.status === '使用中'" type="success" size="small">
                  进行中
                </el-tag>
                <el-tag v-else-if="row.status === '已完成'" type="info" size="small">已完成</el-tag>
                <el-tag v-else type="danger" size="small">已取消</el-tag>
              </template>
            </el-table-column>
          </el-table>

          <div v-else class="empty-text">暂无预约记录，可前往「场地预约」创建</div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="list-card" shadow="hover" :loading="loadingTransactions">
          <div class="list-header">
            <div class="title">最近收支记录</div>
            <div class="tip">从会员收支记录中取最近 5 条</div>
          </div>

          <el-table :data="latestTransactions" size="small" v-if="latestTransactions.length" border>
            <el-table-column prop="member_name" label="会员" width="120" />
            <el-table-column prop="type" label="类型" width="90" />
            <el-table-column prop="amount" label="金额（元）" width="110">
              <template #default="{ row }">
                <span :class="row.amount >= 0 ? 'text-income' : 'text-expense'">
                  {{ row.amount >= 0 ? '+' : '' }}{{ formatMoney(row.amount) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="balance_after" label="变动后余额" width="120">
              <template #default="{ row }">¥ {{ formatMoney(row.balance_after) }}</template>
            </el-table-column>
            <el-table-column prop="created_at" label="时间" width="160" />
          </el-table>

          <div v-else class="empty-text">暂无收支记录</div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { ElMessage } from "element-plus";
import http from "../utils/http";

interface OverviewResp {
  today_reservations: number;
  month_reservations: number;
  today_income: number;
  month_income: number;
  member_count: number;
  member_balance: number;
}

interface Reservation {
  court_name: string;
  member_name: string | null;
  start_time: string;
  status: string;
}

interface Transaction {
  member_name: string;
  type: string;
  amount: number;
  balance_after: number;
  created_at: string;
}

const overview = ref<OverviewResp | null>(null);
const latestReservations = ref<Reservation[]>([]);
const latestTransactions = ref<Transaction[]>([]);
const loadingOverview = ref(false);
const loadingReservations = ref(false);
const loadingTransactions = ref(false);

const formatMoney = (v: unknown) => {
  const num = Number(v);
  if (Number.isNaN(num)) return "0.00";
  return num.toFixed(2);
};

const loadOverview = async () => {
  loadingOverview.value = true;
  try {
    const res = await http.get<OverviewResp>("/reports/overview");
    overview.value = res.data;
  } catch (err) {
    console.error(err);
    ElMessage.error("获取数据总览失败");
  } finally {
    loadingOverview.value = false;
  }
};

const loadLatestReservations = async () => {
  loadingReservations.value = true;
  try {
    const res = await http.get<any[]>("/court-reservations");
    const list = res.data || [];
    latestReservations.value = list.slice(0, 5);
  } catch (err) {
    console.error(err);
    ElMessage.error("获取预约列表失败");
  } finally {
    loadingReservations.value = false;
  }
};

const loadLatestTransactions = async () => {
  loadingTransactions.value = true;
  try {
    const res = await http.get<any[]>("/member-transactions");
    const list = res.data || [];
    latestTransactions.value = list.slice(0, 5);
  } catch (err) {
    console.error(err);
    ElMessage.error("获取收支记录失败");
  } finally {
    loadingTransactions.value = false;
  }
};

onMounted(() => {
  loadOverview();
  loadLatestReservations();
  loadLatestTransactions();
});
</script>

<style scoped>
.dashboard {
  padding: 16px 24px 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.sub-title {
  margin: 4px 0 0;
  font-size: 13px;
  color: #6b7280;
}
.stats-row {
  margin-top: 8px;
}
.stat-card {
  border-radius: 16px;
  color: #0f172a;
}
.stat-card .label {
  font-size: 13px;
  color: #6b7280;
}
.stat-card .value {
  margin-top: 6px;
  font-size: 24px;
  font-weight: 600;
}
.stat-card .sub {
  margin-top: 4px;
  font-size: 12px;
  color: #94a3b8;
}
.stat-blue {
  background: linear-gradient(135deg, #e0f2fe, #eff6ff);
}
.stat-green {
  background: linear-gradient(135deg, #dcfce7, #f0fdf4);
}
.stat-orange {
  background: linear-gradient(135deg, #ffedd5, #fff7ed);
}
.stat-purple {
  background: linear-gradient(135deg, #ede9fe, #faf5ff);
}
.mini-card {
  border-radius: 16px;
}
.mini-title {
  font-size: 13px;
  color: #6b7280;
}
.mini-value {
  margin-top: 6px;
  font-size: 22px;
  font-weight: 600;
  color: #111827;
}
.mini-sub {
  margin-top: 4px;
  font-size: 12px;
  color: #9ca3af;
}
.lists-row {
  margin-top: 12px;
}
.list-card {
  border-radius: 16px;
}
.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.list-header .title {
  font-weight: 600;
}
.list-header .tip {
  font-size: 12px;
  color: #9ca3af;
}
.empty-text {
  padding: 12px;
  text-align: center;
  color: #9ca3af;
}
.text-income {
  color: #16a34a;
}
.text-expense {
  color: #dc2626;
}
.text-muted {
  color: #9ca3af;
}
</style>
