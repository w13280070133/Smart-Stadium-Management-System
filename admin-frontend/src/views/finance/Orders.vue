<template>
  <div class="orders-page">
    <div class="page-header">
      <div>
        <h2>订单中心</h2>
        <p class="sub-title">统一查看场地预约 / 商品售卖及退款</p>
      </div>
    </div>

    <el-card shadow="hover" class="card">
      <el-alert type="info" :closable="false" class="order-settings-alert">
        <template #default>
          <div class="order-settings-wrapper">
            <div class="order-settings-title">支付与订单规则（来自系统设置）</div>
            <div class="order-settings-tags">
              <el-tag v-for="m in orderSettings.payMethods" :key="m" effect="plain">
                可用支付：{{ m }}
              </el-tag>
              <el-tag effect="plain">
                未支付自动关闭：{{ orderSettings.autoClose }}
              </el-tag>
            </div>
          </div>
        </template>
      </el-alert>
      <div class="filters">
        <el-select v-model="filters.order_type" placeholder="业务类型" style="width: 140px" clearable>
          <el-option v-for="opt in bizTypeOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
        </el-select>

        <el-select v-model="filters.status" placeholder="支付状态" style="width: 140px" clearable>
          <el-option v-for="opt in statusOptions" :key="opt.value" :label="opt.label" :value="opt.value" />
        </el-select>

        <el-select v-model="filters.source" placeholder="订单来源" style="width: 140px" clearable>
          <el-option label="后台" value="后台" />
          <el-option label="会员端" value="会员端" />
        </el-select>

        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="-"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
        />

        <el-input
          v-model="filters.keyword"
          placeholder="订单号 / 备注"
          clearable
          style="width: 200px"
        />

        <el-input
          v-model="filters.related_id"
          placeholder="关联业务ID"
          clearable
          style="width: 160px"
        />

        <el-button type="primary" @click="onSearch">刷新</el-button>
        <el-button @click="resetFilters">重置</el-button>

        <span class="summary" v-if="total > 0">当前共 {{ total }} 条订单</span>
      </div>

      <el-table
        :data="orders"
        border
        stripe
        style="width: 100%"
        v-loading="loading"
        :cell-class-name="tableCellClassName"
      >
        <el-table-column prop="order_no" label="订单号" min-width="180" />
        <el-table-column label="业务类型" width="120">
          <template #default="{ row }">
            {{ renderOrderType(row.order_type) }}
          </template>
        </el-table-column>
        <el-table-column prop="member_name" label="会员" min-width="120">
          <template #default="{ row }">
            {{ row.member_name || row.member_id || "-" }}
          </template>
        </el-table-column>

        <el-table-column label="应付" width="110">
          <template #default="{ row }">
            {{ formatAmount(row.total_amount) }}
          </template>
        </el-table-column>
        <el-table-column label="优惠" width="90">
          <template #default="{ row }">
            {{ formatAmount(row.discount_amount) }}
          </template>
        </el-table-column>
        <el-table-column label="实付" width="110">
          <template #default="{ row }">
            {{ formatAmount(row.pay_amount) }}
          </template>
        </el-table-column>

        <el-table-column label="支付方式" width="110">
          <template #default="{ row }">
            {{ renderPayMethod(row.pay_method) }}
          </template>
        </el-table-column>

        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" effect="plain">
              {{ renderStatus(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="创建时间" width="170">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="支付时间" width="170">
          <template #default="{ row }">
            {{ row.paid_at ? formatDateTime(row.paid_at) : "-" }}
          </template>
        </el-table-column>

        <el-table-column prop="remark" label="备注" min-width="160" show-overflow-tooltip />

        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openDetail(row)">详情</el-button>

            <el-divider direction="vertical" />

            <el-button
              link
              type="danger"
              size="small"
              :disabled="!canRefund(row)"
              @click="confirmRefund(row)"
            >
              退款
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination" v-if="total > 0">
        <el-pagination
          background
          layout="prev, pager, next"
          :total="total"
          :page-size="pageSize"
          :current-page="page"
          @current-change="handlePageChange"
        />
      </div>

      <div v-if="!loading && orders.length === 0" class="empty-tip">暂无订单记录</div>
    </el-card>

    <el-drawer v-model="detailVisible" title="订单详情" size="40%">
      <el-descriptions :column="1" border size="small" v-if="detailOrder">
        <el-descriptions-item label="订单号">
          {{ detailOrder?.order_no || "-" }}
        </el-descriptions-item>
        <el-descriptions-item label="业务类型">
          {{ renderOrderType(detailOrder?.order_type) }}
        </el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="statusTagType(detailOrder?.status)" effect="plain" size="small">
            {{ renderStatus(detailOrder?.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="会员">
          {{ detailOrder?.member_name || detailOrder?.member_id || "-" }}
        </el-descriptions-item>
        <el-descriptions-item label="金额">
          应付 {{ formatAmount(detailOrder?.total_amount) }} / 实付 {{ formatAmount(detailOrder?.pay_amount) }}
        </el-descriptions-item>
        <el-descriptions-item label="支付方式">
          {{ renderPayMethod(detailOrder?.pay_method) }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ formatDateTime(detailOrder?.created_at) }}
        </el-descriptions-item>
        <el-descriptions-item label="支付时间">
          {{ detailOrder?.paid_at ? formatDateTime(detailOrder?.paid_at) : "-" }}
        </el-descriptions-item>
        <el-descriptions-item label="关联ID">
          {{ detailOrder?.related_id || "-" }}
        </el-descriptions-item>
        <el-descriptions-item label="备注">
          {{ detailOrder?.remark || "-" }}
        </el-descriptions-item>
      </el-descriptions>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch } from "vue";
import { useRoute } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import http from "@/utils/http";
import { hasAction } from "@/utils/permission";
import dayjs from "dayjs";

interface OrderItem {
  id: number;
  order_no: string;
  order_type: string;
  related_id: number | null;
  member_id: number | null;
  member_name: string | null;
  total_amount: string | number | null;
  pay_amount: string | number | null;
  discount_amount: string | number | null;
  currency: string | null;
  pay_method: string | null;
  status: string | null;
  created_at: string | null;
  paid_at: string | null;
  remark: string | null;
}

const route = useRoute();

const orders = ref<OrderItem[]>([]);
const loading = ref(false);
const detailVisible = ref(false);
const detailOrder = ref<OrderItem | null>(null);

const page = ref(1);
const pageSize = ref(20);
const total = ref(0);

const dateRange = ref<[string, string] | []>([]);
const filters = reactive({
  order_type: "" as string | "",
  status: "" as string | "",
  source: "" as string | "",
  related_id: "" as string | "",
  keyword: "" as string | "",
});

const orderSettings = ref({
  payMethods: ["现金", "会员余额"],
  autoClose: "未配置",
});

const bizTypeOptions = [
  { label: "全部类型", value: "" },
  { label: "场地预约", value: "court" },
  { label: "培训报名", value: "training" },
  { label: "商品售卖", value: "goods" },
  { label: "退款", value: "refund" },
];

const statusOptions = [
  { label: "已支付", value: "paid" },
  { label: "未支付", value: "pending" },
  { label: "已退款", value: "refunded" },
  { label: "部分退款", value: "partial_refund" },
  { label: "已关闭", value: "closed" },
];

const loadOrders = async () => {
  loading.value = true;
  try {
    const params: Record<string, any> = {
      page: page.value,
      page_size: pageSize.value,
    };
    if (filters.order_type) params.order_type = filters.order_type;
    if (filters.status) params.status = filters.status;
    if (filters.source) params.source = filters.source;
    if (filters.related_id) {
      const rid = Number(filters.related_id);
      if (!Number.isNaN(rid)) params.related_id = rid;
    }
    if (filters.keyword) params.keyword = filters.keyword.trim();
    if (dateRange.value && dateRange.value.length === 2) {
      params.date_from = dateRange.value[0];
      params.date_to = dateRange.value[1];
    }
    const res = await http.get("/orders", { params });
    orders.value = res.data?.items || [];
    total.value = res.data?.total || 0;
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "获取订单失败");
  } finally {
    loading.value = false;
  }
};

const handlePageChange = (p: number) => {
  page.value = p;
  loadOrders();
};

const onSearch = () => {
  page.value = 1;
  loadOrders();
};

const resetFilters = () => {
  filters.order_type = "";
  filters.status = "";
  filters.source = "";
  filters.related_id = "";
  filters.keyword = "";
  dateRange.value = [];
  onSearch();
};

const openDetail = (row: OrderItem) => {
  detailOrder.value = row;
  detailVisible.value = true;
};

const isRowRefunded = (row: OrderItem) => {
  const s = (row.status || "").toLowerCase();
  return s === "refunded" || s === "partial_refund" || s === "cancelled" || s === "canceled";
};

const canRefund = (row: OrderItem) => {
  if (!hasAction("order.refund")) return false;
  return !isRowRefunded(row);
};

const tableCellClassName = ({
  row,
  column,
}: {
  row: OrderItem;
  column: { label?: string };
}) => {
  return column.label === "操作" && isRowRefunded(row) ? "disabled-row" : "";
};

const confirmRefund = (row: OrderItem) => {
  ElMessageBox.confirm(
    `确认对订单【${row.order_no}】发起退款吗？`,
    "提示",
    { type: "warning", confirmButtonText: "确认退款", cancelButtonText: "取消" }
  )
    .then(() => doRefund(row))
    .catch(() => {});
};

const doRefund = async (row: OrderItem) => {
  try {
    await http.post(`/orders/${row.id}/refund`);
    ElMessage.success("已发起退款");
    loadOrders();
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "退款失败");
  }
};

const formatAmount = (v: any) => {
  if (v === null || v === undefined) return "-";
  const num = Number(v);
  if (Number.isNaN(num)) return v;
  return num.toFixed(2);
};

const formatDateTime = (v: string | null | undefined) => {
  if (!v) return "-";
  return dayjs(v).format("YYYY-MM-DD HH:mm");
};

const renderOrderType = (t: string | null | undefined) => {
  const map: Record<string, string> = {
    court: "场地预约",
    goods: "商品消费",
    product: "商品消费",
    training: "培训报名",
    course: "培训报名",
    refund: "退款",
  };
  const key = (t || "").toLowerCase();
  return map[key] || "其他";
};

const renderPayMethod = (m: string | null | undefined) => {
  const map: Record<string, string> = {
    cash: "现金",
    card: "银行卡",
    member_balance: "会员余额",
    balance: "会员余额",
    wechat: "微信",
    alipay: "支付宝",
    free: "免费",
  };
  return map[(m || "").toLowerCase()] || "-";
};

const renderStatus = (s: string | null | undefined) => {
  const map: Record<string, string> = {
    paid: "已支付",
    pending: "未支付",
    refunded: "已退款",
    partial_refund: "部分退款",
    closed: "已关闭",
  };
  return map[(s || "").toLowerCase()] || "未知";
};

const statusTagType = (s: string | null | undefined) => {
  const key = (s || "").toLowerCase();
  if (key === "paid") return "success";
  if (key === "refunded" || key === "partial_refund") return "warning";
  if (key === "pending") return "info";
  if (key === "closed") return "danger";
  return "info";
};

const applyRoutePrefill = () => {
  const { related_id, order_no } = route.query;
  if (related_id) {
    filters.related_id = String(related_id);
  }
  if (order_no) {
    filters.keyword = String(order_no);
  }
};

watch(
  () => route.query,
  () => {
    applyRoutePrefill();
    onSearch();
  },
  { immediate: true }
);

const loadOrderSettings = async () => {
  try {
    const res = await http.get("/system-settings/grouped");
    const data = res.data || {};
    
    // 处理支付方式：可能是字符串（逗号分隔）或数组
    let payMethodsRaw = data.order?.default_pay_methods || "";
    let payMethodsList: string[] = [];
    
    if (Array.isArray(payMethodsRaw)) {
      payMethodsList = payMethodsRaw;
    } else if (typeof payMethodsRaw === "string" && payMethodsRaw) {
      payMethodsList = payMethodsRaw.split(",").map((m: string) => m.trim()).filter(Boolean);
    }
    
    const payMethods = payMethodsList.length
      ? payMethodsList.map((m: string) => renderPayMethod(m) || m)
      : ["现金", "会员余额"];
    
    const autoCloseMinutes = Number(data.order?.auto_close_minutes ?? 0);
    orderSettings.value = {
      payMethods,
      autoClose: autoCloseMinutes > 0 ? `${autoCloseMinutes} 分钟` : "未启用自动关闭",
    };
  } catch (err) {
    console.error(err);
  }
};

loadOrderSettings();
</script>

<style scoped>
.orders-page {
  padding: 16px 24px 24px;
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
.card {
  border-radius: 16px;
  border: 1px solid rgba(148, 163, 184, 0.35);
}
.filters {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
.summary {
  color: #6b7280;
}
.pagination {
  margin-top: 12px;
  text-align: right;
}
.empty-tip {
  text-align: center;
  color: #94a3b8;
  padding: 28px 0;
}
.disabled-row {
  opacity: 0.6;
}

.order-settings-alert {
  margin-bottom: 12px;
  border-radius: 12px;
}

.order-settings-wrapper {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.order-settings-title {
  font-weight: 600;
  color: #0f172a;
  font-size: 13px;
}

.order-settings-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
