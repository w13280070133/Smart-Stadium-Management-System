<template>
  <div class="page">
    <div class="page-header">
      <div>
        <div class="page-header-title">我的订单</div>
        <div class="page-header-subtitle">
          查看在场地预约、商品消费等业务产生的订单记录
        </div>
      </div>
    </div>

    <el-card shadow="hover" class="page-card">
      <el-table
        :data="orders"
        border
        v-loading="loading"
        style="width: 100%"
      >
        <el-table-column prop="order_no" label="订单号" width="180" />
        <el-table-column prop="type" label="业务类型" width="120" />
        <el-table-column label="金额(元)" width="120">
          <template #default="{ row }">
            ¥ {{ Number(row.amount || 0).toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="订单状态" width="110">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">
              {{ renderStatus(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
      </el-table>

      <div v-if="!loading && orders.length === 0" class="empty">
        暂无订单记录
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import api from "@/utils/api";

interface OrderItem {
  id: number;
  order_no: string;
  type: string; // 已是中文标签：场地预约 / 商品消费
  amount: number;
  status: string;
  created_at: string;
}

const orders = ref<OrderItem[]>([]);
const loading = ref(false);

function renderStatus(status?: string) {
  const s = (status || "").toLowerCase();
  switch (s) {
    case "paid":
    case "已支付":
      return "已支付";
    case "unpaid":
    case "pending":
    case "未支付":
      return "未支付";
    case "cancelled":
    case "canceled":
    case "已取消":
      return "已取消";
    case "refunded":
    case "已退款":
      return "已退款";
    case "partial_refund":
      return "部分退款";
    default:
      return status || "-";
  }
}

function statusTagType(status?: string) {
  const s = (status || "").toLowerCase();
  if (s === "paid") return "success";
  if (s === "unpaid" || s === "pending") return "info";
  if (s === "refunded" || s === "partial_refund") return "warning";
  if (s === "cancelled" || s === "canceled") return "danger";
  return "";
}

async function loadOrders() {
  loading.value = true;
  try {
    const res = await api.get<OrderItem[]>("/member/orders");
    orders.value = res.data || [];
  } catch (e: any) {
    console.error(e);
    ElMessage.error(e?.response?.data?.detail || "获取订单失败");
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadOrders();
});
</script>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.page-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
}

.page-header-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.page-header-subtitle {
  margin-top: 4px;
  font-size: 13px;
  color: #6b7280;
}

.page-card {
  border-radius: 16px;
}

.empty {
  margin-top: 12px;
  text-align: center;
  font-size: 13px;
  color: #9ca3af;
}
</style>
