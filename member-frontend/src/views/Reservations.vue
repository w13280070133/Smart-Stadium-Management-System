<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h2>场地预约</h2>
        <p class="sub-title">
          会员端快速查看场地预约记录，金额由前台结算后记入会员卡 / 余额自动计算
        </p>
      </div>
      <el-button type="primary" size="large" @click="openReserveDialog">
        我要预约
      </el-button>
    </div>

    <el-card class="card" shadow="never">
      <div class="card-header">
        <div class="title">我的预约</div>
        <div class="actions">
          <el-select
            v-model="statusFilter"
            size="small"
            style="width: 140px"
          >
            <el-option label="全部状态" value="all" />
            <el-option label="已预约 / 使用中" value="active" />
            <el-option label="已完成" value="done" />
            <el-option label="已取消 / 已退款" value="closed" />
          </el-select>
          <el-button size="small" @click="loadReservations" :loading="loading">
            刷新
          </el-button>
        </div>
      </div>

      <el-table
        v-loading="loading"
        :data="filteredList"
        border
        style="width: 100%"
        empty-text="暂无预约记录"
      >
        <el-table-column type="index" width="60" label="#" />
        <el-table-column prop="court_name" label="场地" min-width="120" />
        <el-table-column prop="date" label="日期" min-width="120" />
        <el-table-column prop="time_range" label="时间" min-width="140" />
        <el-table-column prop="amount" label="金额（元）" min-width="120">
          <template #default="{ row }">
            <span>¥ {{ formatMoney(row.amount) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" min-width="100">
          <template #default="{ row }">
            <el-tag size="small">
              {{ row.status || "—" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="预约时间" min-width="160" />
        <el-table-column
          prop="remark"
          label="备注"
          min-width="160"
          show-overflow-tooltip
        />
  <el-table-column label="操作" width="120">
    <template #default="{ row }">
      <el-popconfirm
        title="确定要取消该预约吗？退款会原路退回余额"
        confirm-button-text="确认取消"
        cancel-button-text="再想想"
        @confirm="cancelReservation(row)"
        :disabled="!canCancelReservation(row)"
      >
        <template #reference>
          <el-button
            link
            type="danger"
            size="small"
            :disabled="!canCancelReservation(row)"
            :loading="cancelLoading === row.id"
          >
            取消预约
          </el-button>
        </template>
      </el-popconfirm>
    </template>
  </el-table-column>
      </el-table>
    </el-card>

    <!-- 预约弹窗 -->
    <el-dialog
      v-model="reserveDialogVisible"
      title="我要预约"
      width="480px"
      destroy-on-close
    >
      <el-form :model="reserveForm" label-width="80px">
        <el-form-item label="场地">
          <el-select
            v-model="reserveForm.court_id"
            placeholder="请选择场地"
            style="width: 260px"
          >
            <el-option
              v-for="c in courts"
              :key="c.id"
              :label="c.name"
              :value="c.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="日期">
          <el-date-picker
            v-model="reserveForm.date"
            type="date"
            placeholder="选择日期"
            style="width: 260px"
          />
        </el-form-item>

        <el-form-item label="时间段">
          <div class="time-row">
            <el-time-select
              v-model="reserveForm.start_time"
              placeholder="开始时间"
              start="06:00"
              end="23:00"
              step="00:30"
              style="width: 120px"
            />
            <span class="time-sep">至</span>
            <el-time-select
              v-model="reserveForm.end_time"
              placeholder="结束时间"
              start="06:00"
              end="23:00"
              step="00:30"
              style="width: 120px"
            />
          </div>
        </el-form-item>

        <el-form-item label="备注">
          <el-input
            v-model="reserveForm.remark"
            type="textarea"
            :rows="2"
            placeholder="可填写使用人、特殊说明等（可选）"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="reserveDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submitReserve">
          确认预约
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { ElMessage } from "element-plus";
import dayjs from "dayjs";
import http from "../utils/http";

interface ReservationItem {
  id: number;
  court_name: string;
  date: string;
  start_time: string | null;
  end_time: string | null;
  time_range?: string;
  amount: number;
  status: string;
  raw_status?: string;
  remark: string;
  created_at: string;
}

interface CourtItem {
  id: number;
  name: string;
}

interface ReserveForm {
  court_id: number | null;
  date: string | Date | null;
  start_time: string;
  end_time: string;
  remark: string;
}

const loading = ref(false);
const list = ref<ReservationItem[]>([]);
const statusFilter = ref<"all" | "active" | "done" | "closed">("all");

const reserveDialogVisible = ref(false);
const submitLoading = ref(false);
const courts = ref<CourtItem[]>([]);
const cancelLoading = ref<number | null>(null);
const reserveForm = ref<ReserveForm>({
  court_id: null,
  date: null,
  start_time: "09:00",
  end_time: "10:00",
  remark: "",
});

const formatMoney = (val: unknown) => {
  const n = Number(val);
  if (Number.isNaN(n)) return "0.00";
  return n.toFixed(2);
};

const filteredList = computed(() => {
  if (statusFilter.value === "all") return list.value;

  return list.value.filter((item) => {
    const raw = (item.raw_status || item.status || "").toLowerCase();
    if (statusFilter.value === "active") {
      return (
        raw.includes("reserved") ||
        raw.includes("using") ||
        raw.includes("pending") ||
        raw.includes("已预约")
      );
    }
    if (statusFilter.value === "done") {
      return raw.includes("completed") || raw.includes("done") || raw.includes("已完成");
    }
    if (statusFilter.value === "closed") {
      return (
        raw.includes("cancel") ||
        raw.includes("cancelled") ||
        raw.includes("refunded") ||
        raw.includes("已取消") ||
        raw.includes("已退款")
      );
    }
    return true;
  });
});

/**
 * 兼容多种返回结构：
 * - 直接数组 [...]
 * - { data: [...] }
 * - { code, data: [...] }
 * - { data: { code, data: [...] } }
 */
const extractList = (res: any): any[] => {
  if (Array.isArray(res)) return res;
  if (res && Array.isArray(res.data)) return res.data;
  if (res && res.data && Array.isArray(res.data.data)) return res.data.data;
  if (res && Array.isArray(res.items)) return res.items;
  if (res && res.data && Array.isArray(res.data.items)) return res.data.items;
  return [];
};

const loadReservations = async () => {
  loading.value = true;
  try {
    const res = await http.get<ReservationItem[]>("/member/reservations");
    const data = extractList(res);

    list.value = data.map((item: any) => {
      const start = item.start_time || "";
      const end = item.end_time || "";
      const timeRange = start && end ? `${start} - ${end}` : start || end || "";

      return {
        id: item.id,
        court_name: item.court_name || "",
        date: item.date || "",
        start_time: item.start_time || "",
        end_time: item.end_time || "",
        time_range: timeRange,
        amount: Number(item.amount || 0),
        status: item.status || "—",
        raw_status: String(item.raw_status || item.status || ""),
        remark: item.remark || "",
        created_at: item.created_at || "",
      } as ReservationItem;
    });
  } catch (err) {
    console.error(err);
    ElMessage.error("获取我的预约失败");
  } finally {
    loading.value = false;
  }
};

const loadCourts = async () => {
  try {
    const res = await http.get<any>("/courts");
    const data = extractList(res);
    courts.value = data.map((c: any) => ({
      id: c.id,
      name: c.name,
    }));
  } catch (err) {
    console.error(err);
    ElMessage.error("获取场地列表失败");
  }
};

const openReserveDialog = async () => {
  reserveDialogVisible.value = true;
  if (!courts.value.length) {
    await loadCourts();
  }
};

const canCancelReservation = (row: ReservationItem) => {
  const raw = (row.raw_status || row.status || "").toLowerCase();
  if (!row.id) return false;
  if (!raw) return true;
  if (
    raw.includes("取消") ||
    raw.includes("cancel") ||
    raw.includes("refunded") ||
    raw.includes("退款") ||
    raw.includes("completed") ||
    raw.includes("done") ||
    raw.includes("已完成")
  ) {
    return false;
  }

  const datePart = row.date || "";
  let composed = datePart;
  if (row.start_time) {
    if (dayjs(datePart).isValid() && datePart.includes(":")) {
      composed = datePart;
    } else {
      composed = `${datePart} ${row.start_time}`;
    }
  }
  const startMoment = dayjs(composed);
  if (startMoment.isValid() && startMoment.isBefore(dayjs())) {
    return false;
  }

  return true;
};

const cancelReservation = async (row: ReservationItem) => {
  if (!canCancelReservation(row)) return;
  cancelLoading.value = row.id;
  try {
    await http.post(`/member/reservations/${row.id}/cancel`, {
      remark: row.remark || "",
    });
    ElMessage.success("预约已取消并退款");
    loadReservations();
  } catch (err: any) {
    const msg =
      err?.response?.data?.detail ||
      err?.message ||
      "取消失败，请稍后再试";
    ElMessage.error(msg);
  } finally {
    cancelLoading.value = null;
  }
};

const submitReserve = async () => {
  if (!reserveForm.value.court_id) {
    ElMessage.warning("请选择场地");
    return;
  }
  if (!reserveForm.value.date) {
    ElMessage.warning("请选择日期");
    return;
  }
  if (!reserveForm.value.start_time || !reserveForm.value.end_time) {
    ElMessage.warning("请选择开始和结束时间");
    return;
  }

  const dateStr = dayjs(reserveForm.value.date).format("YYYY-MM-DD");

  const payload = {
    court_id: reserveForm.value.court_id,
    date: dateStr,
    start_time: reserveForm.value.start_time,
    end_time: reserveForm.value.end_time,
    remark: reserveForm.value.remark || "",
  };

  submitLoading.value = true;
  try {
    await http.post("/member/reservations", payload);
    ElMessage.success("预约成功");
    reserveDialogVisible.value = false;
    loadReservations();
  } catch (err: any) {
    console.error(err);
    const msg =
      err?.response?.data?.detail ||
      err?.message ||
      "预约失败，请稍后重试";
    ElMessage.error(msg);
  } finally {
    submitLoading.value = false;
  }
};

onMounted(() => {
  loadReservations();
});
</script>

<style scoped>
.page {
  padding: 16px 24px 24px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.sub-title {
  margin-top: 4px;
  font-size: 13px;
  color: #6b7280;
}
.card {
  margin-top: 16px;
  border-radius: 16px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.card-header .title {
  font-size: 15px;
  font-weight: 600;
}
.card-header .actions {
  display: flex;
  gap: 8px;
  align-items: center;
}
.time-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.time-sep {
  color: #6b7280;
  font-size: 13px;
}
</style>
