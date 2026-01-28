<template>
  <div class="reservations-page">
    <div class="page-header">
      <div>
        <h2>场地预约</h2>
        <p class="sub-title">后台管理场地预约记录，含支付、状态、退款等操作</p>
      </div>
      <el-button type="primary" round @click="openAddDialog" :disabled="!canCreate">新增预约</el-button>
    </div>

    <el-alert type="info" class="rules-alert" :closable="false">
      <template #default>
        <div class="rules-wrapper">
          <div class="rules-title">预约规则（来自系统设置）</div>
          <div class="rules-tags">
            <el-tag effect="plain">营业时间：{{ reservationRules.businessHours }}</el-tag>
            <el-tag effect="plain">可提前：{{ reservationRules.openDays }} 天</el-tag>
            <el-tag effect="plain">取消期限：{{ reservationRules.cancelLimit }}</el-tag>
            <el-tag effect="plain">超时自动取消：{{ reservationRules.autoCancel }}</el-tag>
          </div>
        </div>
      </template>
    </el-alert>

    <el-row :gutter="16" class="stat-row">
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card">
          <div class="stat-label">今日预约数</div>
          <div class="stat-value">{{ statTodayCount }}</div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card">
          <div class="stat-label">今日预约金额</div>
          <div class="stat-value">¥ {{ formatAmount(statTodayAmount) }}</div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card">
          <div class="stat-label">本月预约数</div>
          <div class="stat-value">{{ statMonthCount }}</div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <div class="stat-card">
          <div class="stat-label">本月预约金额</div>
          <div class="stat-value">¥ {{ formatAmount(statMonthAmount) }}</div>
        </div>
      </el-col>
    </el-row>

    <el-card class="filter-card" shadow="never">
      <el-form inline>
        <el-form-item label="场地">
          <el-select v-model="filterCourtId" placeholder="全部场地" clearable style="width: 180px">
            <el-option v-for="c in courtOptions" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="状态">
          <el-select v-model="filterStatus" placeholder="全部状态" clearable style="width: 160px">
            <el-option label="已预约" value="已预约" />
            <el-option label="进行中" value="进行中" />
            <el-option label="已完成" value="已完成" />
            <el-option label="已取消" value="已取消" />
          </el-select>
        </el-form-item>

        <el-form-item label="时间段">
          <el-date-picker
            v-model="filterDateRange"
            type="datetimerange"
            range-separator="-"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            :default-time="defaultRangeTime"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>

        <el-form-item label="备注/会员/场地">
          <el-input
            v-model="filterKeyword"
            placeholder="可模糊搜索备注、会员、场地"
            style="width: 240px"
            clearable
          />
        </el-form-item>

        <el-form-item>
          <el-button @click="resetFilters">重置筛选</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="card" shadow="hover">
      <el-table :data="filteredReservations" border style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="court_name" label="场地" width="160" />
        <el-table-column prop="member_name" label="会员" width="140">
          <template #default="{ row }">
            <span v-if="row.member_name">{{ row.member_name }}</span>
            <span v-else class="text-muted">散客</span>
          </template>
        </el-table-column>

        <el-table-column prop="start_time" label="开始时间" width="180" />
        <el-table-column prop="end_time" label="结束时间" width="180" />

        <el-table-column prop="status" label="状态" width="110">
          <template #default="{ row }">
            <el-tag v-if="row.status === '已预约'" type="warning" effect="light">已预约</el-tag>
            <el-tag v-else-if="row.status === '进行中'" type="success" effect="light">进行中</el-tag>
            <el-tag v-else-if="row.status === '已完成'" type="info" effect="light">已完成</el-tag>
            <el-tag v-else type="danger" effect="light">已取消</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="total_amount" label="金额（元）" width="120">
          <template #default="{ row }">
            ¥ {{ formatAmount(row.total_amount) }}
          </template>
        </el-table-column>

        <el-table-column label="关联订单" min-width="220">
          <template #default="{ row }">
            <div v-if="row.order_no" class="order-wrapper">
              <div class="order-no">{{ row.order_no }}</div>
              <el-tag size="small" :type="orderTagType(row.order_status)" effect="plain">
                {{ renderOrderStatus(row.order_status) }}
              </el-tag>
            </div>
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>

        <el-table-column prop="source" label="来源" width="90" />
        <el-table-column prop="remark" label="备注" min-width="160" />
        <el-table-column prop="created_at" label="创建时间" width="180" />

        <el-table-column label="操作" width="320" fixed="right">
          <template #default="{ row }">
            <el-dropdown @command="onStatusCommand($event, row)" :disabled="!canUpdate">
              <span class="el-dropdown-link">
                状态变更
                <el-icon class="el-icon--right">
                  <ArrowDown />
                </el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="已预约">标为已预约</el-dropdown-item>
                  <el-dropdown-item command="进行中">标为进行中</el-dropdown-item>
                  <el-dropdown-item command="已完成">标为已完成</el-dropdown-item>
                  <el-dropdown-item command="已取消">标为已取消</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>

            <el-divider direction="vertical" />

            <el-button
              link
              type="danger"
              size="small"
              :disabled="row.status === '已取消' || !canRefund"
              @click="handleRefund(row)">
              退款
            </el-button>

            <el-divider direction="vertical" />

            <el-button
              link
              type="primary"
              size="small"
              :disabled="!row.order_no"
              @click="goOrderDetail(row)">
              查看订单
            </el-button>

            <el-divider direction="vertical" />

            <el-button link type="danger" size="small" :disabled="!canDelete" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && !filteredReservations.length" class="empty-text">
        暂无预约记录，可点击右上角“新增预约”
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" title="新增预约" width="520px">
      <el-form :model="form" label-width="90px">
        <el-form-item label="场地">
          <el-select v-model="form.court_id" placeholder="选择场地" style="width: 260px">
            <el-option v-for="c in courtOptions" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="会员">
          <el-select
            v-model="form.member_id"
            placeholder="可选，不选则默认为散客"
            style="width: 260px"
            clearable
          >
            <el-option v-for="m in memberOptions" :key="m.id" :label="`${m.name}（${m.phone}）`" :value="m.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="支付方式">
          <el-select v-model="form.pay_method" placeholder="选择支付方式" style="width: 260px">
            <el-option label="会员余额" value="会员余额" />
            <el-option label="现金" value="现金" />
          </el-select>
        </el-form-item>

        <el-form-item label="时间段">
          <el-date-picker
            v-model="form.timeRange"
            type="datetimerange"
            start-placeholder="开始时间"
            end-placeholder="结束时间"
            :default-time="defaultRangeTime"
            range-separator="-"
            format="YYYY-MM-DD HH:mm"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>

        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="选填" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitForm">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { ArrowDown } from "@element-plus/icons-vue";
import dayjs from "dayjs";
import http from "../utils/http";
import { hasAction } from "@/utils/permission";

interface Reservation {
  id: number;
  court_id: number;
  court_name: string;
  member_id: number | null;
  member_name: string | null;
  start_time: string;
  end_time: string;
  status: string;
  total_amount: number | string | null;
  source: string;
  remark: string;
  created_at: string;
  order_id?: number;
  order_no?: string;
  order_status?: string;
  order_pay_method?: string | null;
}

interface CourtOption {
  id: number;
  name: string;
}

interface MemberOption {
  id: number;
  name: string;
  phone: string;
}

interface ReservationForm {
  court_id: number | null;
  member_id: number | null;
  timeRange: string[];
  remark: string;
}

const router = useRouter();

const loading = ref(false);
const reservations = ref<Reservation[]>([]);

const dialogVisible = ref(false);
const saving = ref(false);

const courtOptions = ref<CourtOption[]>([]);
const memberOptions = ref<MemberOption[]>([]);

const form = ref<ReservationForm>({
  court_id: null,
  member_id: null,
  timeRange: [],
  remark: "",
});

const canCreate = hasAction("reservation.create");
const canUpdate = hasAction("reservation.edit");
const canRefund = hasAction("reservation.refund");
const canDelete = hasAction("reservation.delete");

const reservationRules = ref({
  businessHours: "—",
  openDays: "—",
  cancelLimit: "—",
  autoCancel: "—",
});

const formatAmount = (value: unknown) => {
  const n = Number(value);
  if (Number.isNaN(n)) return "0.00";
  return n.toFixed(2);
};

const sumAmount = (filterFn: (r: Reservation) => boolean) => {
  return reservations.value.reduce((sum, r) => {
    if (!filterFn(r)) return sum;
    const v = Number(r.total_amount ?? 0);
    return sum + (Number.isNaN(v) ? 0 : v);
  }, 0);
};

const statTodayCount = computed(() =>
  reservations.value.filter((r) => dayjs(r.start_time).isSame(dayjs(), "day")).length
);

const statTodayAmount = computed(() => sumAmount((r) => dayjs(r.start_time).isSame(dayjs(), "day")));

const statMonthCount = computed(() =>
  reservations.value.filter((r) => dayjs(r.start_time).isSame(dayjs(), "month")).length
);

const statMonthAmount = computed(() => sumAmount((r) => dayjs(r.start_time).isSame(dayjs(), "month")));

const filterCourtId = ref<number | null>(null);
const filterStatus = ref<string>("");
const filterDateRange = ref<string[]>([]);
const filterKeyword = ref<string>("");

const defaultRangeTime = [new Date(0, 0, 0, 9, 0, 0), new Date(0, 0, 0, 10, 0, 0)];

const filteredReservations = computed(() => {
  return reservations.value.filter((r) => {
    if (filterCourtId.value && r.court_id !== filterCourtId.value) return false;
    if (filterStatus.value && r.status !== filterStatus.value) return false;
    if (filterDateRange.value && filterDateRange.value.length === 2) {
      const [start, end] = filterDateRange.value;
      const s = dayjs(start);
      const e = dayjs(end);
      const t = dayjs(r.start_time);
      if (t.isBefore(s) || t.isAfter(e)) return false;
    }
    if (filterKeyword.value.trim()) {
      const kw = filterKeyword.value.trim();
      const text = (r.remark || "") + (r.court_name || "") + (r.member_name || "");
      if (!text.includes(kw)) return false;
    }
    return true;
  });
});

const resetFilters = () => {
  filterCourtId.value = null;
  filterStatus.value = "";
  filterDateRange.value = [];
  filterKeyword.value = "";
};

const loadReservations = async () => {
  loading.value = true;
  try {
    const res = await http.get<Reservation[]>("/court-reservations");
    reservations.value = res.data || [];
  } catch (err) {
    console.error(err);
    ElMessage.error("获取预约列表失败");
  } finally {
    loading.value = false;
  }
};

const loadCourts = async () => {
  try {
    const res = await http.get<any[]>("/courts");
    courtOptions.value = (res.data || []).map((c: any) => ({ id: c.id, name: c.name }));
  } catch (err) {
    console.error(err);
    ElMessage.error("获取场地列表失败");
  }
};

const loadMembers = async () => {
  try {
    const res = await http.get<any>("/members", { params: { page_size: 1000 } });
    const members = res.data?.items || res.data || [];
    memberOptions.value = members.map((m: any) => ({ id: m.id, name: m.name, phone: m.phone }));
  } catch (err) {
    console.error(err);
    ElMessage.error("获取会员列表失败");
  }
};

onMounted(() => {
  loadReservations();
  loadCourts();
  loadMembers();
  loadReservationRules();
});

const openAddDialog = () => {
  form.value = { 
    court_id: null, 
    member_id: null, 
    pay_method: "会员余额", 
    timeRange: [], 
    remark: "" 
  };
  dialogVisible.value = true;
};

const submitForm = async () => {
  if (!canCreate) {
    ElMessage.warning("无新增权限");
    return;
  }
  if (!form.value.court_id) {
    ElMessage.warning("请选择场地");
    return;
  }
  if (!form.value.timeRange || form.value.timeRange.length !== 2) {
    ElMessage.warning("请选择开始和结束时间");
    return;
  }

  const payload = {
    court_id: form.value.court_id,
    member_id: form.value.member_id || null,
    start_time: form.value.timeRange[0],
    end_time: form.value.timeRange[1],
    pay_method: form.value.pay_method || "会员余额",
    remark: form.value.remark,
  };

  try {
    saving.value = true;
    const res = await http.post<any>("/court-reservations", payload);
    const body = res?.data ?? res;
    const order = body?.order || body?.data?.order;
    const orderNo = order?.order_no || order?.orderNo || order?.id;
    if (orderNo) {
      ElMessage.success(`预约创建成功，订单号：${orderNo}`);
    } else {
      ElMessage.success("预约创建成功");
    }
    dialogVisible.value = false;
    await loadReservations();
  } catch (err: any) {
    console.error(err);
    const msg = err?.response?.data?.detail || "创建预约失败，请稍后重试";
    ElMessage.error(msg);
  } finally {
    saving.value = false;
  }
};

const handleStatusCommand = async (cmd: string, row: Reservation) => {
  if (!canUpdate) {
    ElMessage.warning("无权限变更状态");
    return;
  }
  try {
    await http.put(`/court-reservations/${row.id}/status`, { status: cmd });
    ElMessage.success("状态已更新");
    await loadReservations();
  } catch (err: any) {
    console.error(err);
    const msg = err?.response?.data?.detail || "更新状态失败，请稍后重试";
    ElMessage.error(msg);
  }
};

const onStatusCommand = (cmd: string, row: Reservation) => {
  handleStatusCommand(cmd, row);
};

const handleDelete = (row: Reservation) => {
  if (!canDelete) {
    ElMessage.warning("无删除权限");
    return;
  }
  ElMessageBox.confirm(`确认要删除预约【${row.court_name} ${row.start_time}】吗？`, "删除确认", {
    type: "warning",
    confirmButtonText: "删除",
    cancelButtonText: "取消",
  })
    .then(async () => {
      try {
        await http.delete(`/court-reservations/${row.id}`);
        ElMessage.success("删除成功");
        await loadReservations();
      } catch (err) {
        console.error(err);
        ElMessage.error("删除失败，请稍后重试");
      }
    })
    .catch(() => {});
};

const handleRefund = async (row: Reservation) => {
  if (!canRefund) {
    ElMessage.warning("无退款权限");
    return;
  }
  if (!row.id || row.status === "已取消") return;
  try {
    await ElMessageBox.confirm(`确认对预约 #${row.id} 发起退款并取消吗？`, "退款确认", {
      confirmButtonText: "确认退款",
      cancelButtonText: "取消",
      type: "warning",
    });
  } catch {
    return;
  }

  try {
    const res = await http.post<any>(`/court-reservations/${row.id}/refund`, {});
    const payload = (res as any)?.data ?? res;
    const refundOrderNo =
      payload?.refund_order?.order_no ||
      payload?.order_no;
    ElMessage.success(refundOrderNo ? `退款成功，退款单号：${refundOrderNo}` : "退款成功");
    await loadReservations();
  } catch (err: any) {
    console.error(err);
    const msg = err?.response?.data?.detail || "退款失败，请稍后重试";
    ElMessage.error(msg);
  }
};

const goOrderDetail = (row: Reservation) => {
  if (!row.order_id && !row.order_no) return;
  router.push({
    path: "/orders",
    query: { related_id: row.id },
  });
};

const renderOrderStatus = (status?: string | null) => {
  const s = (status || "").toLowerCase();
  if (s === "paid") return "已支付";
  if (s === "pending") return "未支付";
  if (s === "refunded") return "已退款";
  if (s === "partial_refund") return "部分退款";
  if (s === "closed") return "已关闭";
  return status || "-";
};

const orderTagType = (status?: string | null) => {
  const s = (status || "").toLowerCase();
  if (s === "paid") return "success";
  if (s === "refunded" || s === "partial_refund") return "warning";
  if (s === "pending") return "info";
  if (s === "closed") return "danger";
  return "info";
};

const loadReservationRules = async () => {
  try {
    const res = await http.get("/system-settings/grouped");
    const data = res.data || {};
    const open = data.time?.business_open_time || "06:00";
    const close = data.time?.business_close_time || "22:00";
    const openDays = Number(data.business?.reservation_open_days ?? 7);
    const cancelLimit = Number(data.business?.reservation_cancel_limit_hours ?? 4);
    const autoCancel = Number(data.business?.auto_cancel_minutes ?? 30);
    reservationRules.value = {
      businessHours: `${open} ~ ${close}`,
      openDays: openDays > 0 ? `${openDays}` : "未限制",
      cancelLimit: cancelLimit > 0 ? `提前 ${cancelLimit} 小时` : "随时可取消",
      autoCancel: autoCancel > 0 ? `${autoCancel} 分钟未支付自动取消` : "不自动取消",
    };
  } catch (err) {
    console.error(err);
  }
};
</script>

<style scoped>
.reservations-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: #F2F2F7;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-header h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  color: #1D1D1F;
}

.sub-title {
  margin: 4px 0 0;
  font-size: 13px;
  color: #86868B;
}

.stat-row {
  margin-bottom: 18px;
}

.stat-card {
  position: relative;
  border-radius: 12px;
  padding: 16px 20px;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.stat-card::before {
  content: "";
  position: absolute;
  left: 0;
  top: 12px;
  bottom: 12px;
  width: 4px;
  border-radius: 999px;
  background: #007AFF;
}

.stat-row .el-col:nth-child(2) .stat-card::before {
  background: #34C759;
}

.stat-row .el-col:nth-child(3) .stat-card::before {
  background: #FF9500;
}

.stat-row .el-col:nth-child(4) .stat-card::before {
  background: #AF52DE;
}

.stat-label {
  position: relative;
  font-size: 13px;
  color: #86868B;
  margin-bottom: 4px;
}

.stat-value {
  position: relative;
  font-size: 26px;
  font-weight: 600;
  color: #1D1D1F;
  letter-spacing: 0.5px;
}

.filter-card {
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.card {
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.empty-text {
  padding: 16px;
  text-align: center;
  font-size: 13px;
  color: #86868B;
}

.el-dropdown-link {
  cursor: pointer;
  color: #007AFF;
  display: inline-flex;
  align-items: center;
}

.text-muted {
  color: #86868B;
}

.order-wrapper {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.order-no {
  font-size: 13px;
  color: #1D1D1F;
  font-weight: 500;
}

.rules-alert {
  border-radius: 12px;
  background: rgba(0, 122, 255, 0.08);
  border: 1px solid rgba(0, 122, 255, 0.2);
}

.rules-wrapper {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.rules-title {
  font-weight: 600;
  color: #1D1D1F;
}

.rules-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
