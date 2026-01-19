<template>
  <div class="orders-page" v-loading="loading">
    <div class="page-header">
      <div>
        <h2>我的订单</h2>
        <p class="sub-title">统一查看场地预约与商品消费订单，含退款状态</p>
      </div>
    </div>

    <el-row :gutter="12" class="stat-row">
      <el-col :span="6">
        <div class="stat-card">
          <div class="label">全部订单数</div>
          <div class="value">{{ totalCount }}</div>
          <div class="desc">包含所有来源的订单</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card stat-court">
          <div class="label">场地预约</div>
          <div class="value">{{ courtCount }}</div>
          <div class="desc">场地预约产生的订单</div>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="stat-card stat-goods">
          <div class="label">商品消费</div>
          <div class="value">{{ goodsCount }}</div>
          <div class="desc">商品售卖</div>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="stat-card stat-training">
          <div class="label">培训报名</div>
          <div class="value">{{ trainingCount }}</div>
          <div class="desc">课程报名</div>
        </div>
      </el-col>
      <el-col :span="4">
        <div class="stat-card stat-refund">
          <div class="label">退款订单</div>
          <div class="value">{{ refundCount }}</div>
          <div class="desc">退款记录</div>
        </div>
      </el-col>
    </el-row>

    <div class="filter-bar">
      <el-select v-model="filters.type" placeholder="全部类型" clearable style="width: 150px" size="small">
        <el-option label="场地预约" value="court" />
        <el-option label="商品消费" value="goods" />
        <el-option label="培训报名" value="training" />
        <el-option label="退款" value="refund" />
      </el-select>

      <el-select v-model="filters.status" placeholder="全部状态" clearable style="width: 150px; margin-left: 8px" size="small">
        <el-option label="已支付" value="paid" />
        <el-option label="未支付" value="pending" />
        <el-option label="已退款" value="refunded" />
        <el-option label="部分退款" value="partial_refund" />
        <el-option label="已关闭" value="closed" />
      </el-select>

      <el-input
        v-model="filters.keyword"
        placeholder="按订单号 / 类型搜索"
        size="small"
        clearable
        style="width: 240px; margin-left: 8px"
      >
        <template #prefix>
          <i class="el-icon-search" />
        </template>
      </el-input>

      <el-button size="small" type="primary" text style="margin-left: 8px" @click="resetFilter">
        重置筛选
      </el-button>
    </div>

    <el-card shadow="hover" class="table-card">
      <el-table :data="filteredOrders" style="width: 100%" border size="small">
        <el-table-column prop="order_no" label="订单号" min-width="160" show-overflow-tooltip />
        <el-table-column prop="order_type" label="类型" width="110">
          <template #default="{ row }">
            {{ renderType(row.order_type ?? row.business_type) }}
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="金额（元）" width="120">
          <template #default="{ row }">
            ¥ {{ Number(row.amount ?? row.pay_amount ?? row.total_amount ?? 0).toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="statusTagType(row.status)">
              {{ renderStatus(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="下单时间" min-width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!filteredOrders.length && !loading" class="empty-wrapper">
        <el-empty description="暂无订单记录" />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import api from "@/utils/api";

interface OrderItem {
  id: string | number;
  order_no?: string;
  order_type?: string;
  business_type?: string;
  total_amount?: number;
  pay_amount?: number;
  amount?: number;
  status?: string;
  created_at?: string;
}

const loading = ref(false);
const orders = ref<OrderItem[]>([]);

const filters = ref({
  type: "" as string | "",
  status: "" as string | "",
  keyword: "",
});

const totalCount = computed(() => orders.value.length);
const courtCount = computed(() => orders.value.filter((o) => normalizeType(o.order_type ?? o.business_type) === "court").length);
const goodsCount = computed(() => orders.value.filter((o) => normalizeType(o.order_type ?? o.business_type) === "goods").length);
const trainingCount = computed(() => orders.value.filter((o) => normalizeType(o.order_type ?? o.business_type) === "training").length);
const refundCount = computed(() => orders.value.filter((o) => normalizeType(o.order_type ?? o.business_type) === "refund").length);

const filteredOrders = computed(() => {
  return orders.value.filter((o) => {
    const t = normalizeType(o.order_type ?? o.business_type);
    const s = (o.status || "").toString().toLowerCase();

    if (filters.value.type && t !== filters.value.type) return false;

    if (filters.value.status) {
      const fs = filters.value.status.toLowerCase();
      if (s !== fs) return false;
    }

    if (filters.value.keyword) {
      const kw = filters.value.keyword.trim();
      const orderType = o.order_type ?? o.business_type;
      if (!(o.order_no || "").includes(kw) && !(renderType(orderType)).includes(kw)) {
        return false;
      }
    }
    return true;
  });
});

function normalizeType(type?: string) {
  const t = (type || "").toLowerCase();
  if (t === "product") return "goods";
  if (t === "course") return "training";
  return t;
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

function renderType(t?: string) {
  const nt = normalizeType(t);
  if (nt === "court") return "场地预约";
  if (nt === "goods") return "商品消费";
  if (nt === "training") return "培训报名";
  if (nt === "refund") return "退款";
  return "其他";
}

function renderStatus(status?: string) {
  const s = (status || "").toLowerCase();
  if (s === "paid") return "已支付";
  if (s === "pending") return "未支付";
  if (s === "refunded") return "已退款";
  if (s === "partial_refund") return "部分退款";
  if (s === "closed") return "已关闭";
  return status || "-";
}

function statusTagType(status?: string) {
  const s = (status || "").toLowerCase();
  if (s === "paid") return "success";
  if (s === "refunded" || s === "partial_refund") return "warning";
  if (s === "pending") return "info";
  if (s === "closed") return "danger";
  return "";
}

function resetFilter() {
  filters.value.type = "";
  filters.value.status = "";
  filters.value.keyword = "";
}

const loadOrders = async () => {
  loading.value = true;
  try {
    const res = await api.get<OrderItem[]>("/member/orders", { params: { limit: 100 } });
    orders.value = res.data || [];
  } catch (err: any) {
    ElMessage.error(err?.response?.data?.detail || "获取订单失败");
  } finally {
    loading.value = false;
  }
};

onMounted(loadOrders);
</script>

<style scoped>
.orders-page {
  padding: 16px 20px 24px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.sub-title {
  margin-top: 4px;
  font-size: 13px;
  color: #6b7280;
}
.stat-row {
  margin-bottom: 8px;
}
.stat-card {
  padding: 12px;
  border-radius: 12px;
  background: #f8fafc;
}
.stat-card .label {
  color: #64748b;
}
.stat-card .value {
  font-size: 22px;
  font-weight: 600;
  margin-top: 4px;
}
.stat-card .desc {
  color: #94a3b8;
  font-size: 12px;
}
.stat-court {
  background: linear-gradient(135deg, #e0f2fe, #eff6ff);
}
.stat-goods {
  background: linear-gradient(135deg, #fef3c7, #fff7ed);
}
.stat-training {
  background: linear-gradient(135deg, #ddd6fe, #ede9fe);
}
.stat-refund {
  background: linear-gradient(135deg, #fee2e2, #fef2f2);
}
.filter-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 8px 0 12px;
}
.table-card {
  border-radius: 12px;
}
.empty-wrapper {
  margin-top: 8px;
}
</style>
