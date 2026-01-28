<template>
  <div class="calendar-page">
    <!-- 顶部：标题 + 控件 -->
    <div class="page-header">
      <div>
        <h2>场地预约可视化</h2>
        <p class="sub-title">
          按月查看每天的预约数量，点击日期查看当天预约详情。
        </p>
      </div>

      <div class="header-actions">
        <!-- 月份选择 -->
        <el-date-picker
          v-model="currentMonth"
          type="month"
          value-format="YYYY-MM"
          format="YYYY 年 MM 月"
          placeholder="选择月份"
          @change="handleMonthChange"
          style="width: 180px"
        />
        <!-- 场地选择 -->
        <el-select
          v-model="activeCourtId"
          placeholder="全部场地"
          clearable
          style="width: 160px; margin-left: 8px"
        >
          <el-option :value="'all'" label="全部场地" />
          <el-option
            v-for="c in courtOptions"
            :key="c.id"
            :label="c.name"
            :value="c.id"
          />
        </el-select>
      </div>
    </div>

    <el-row :gutter="16" class="main-row">
      <!-- 左侧：日历 -->
      <el-col :span="14">
        <el-card shadow="hover" class="calendar-card">
          <el-calendar v-model="calendarDate">
            <template #date-cell="{ data }">
              <div
                class="date-cell"
                :class="{
                  'is-selected': data.day === selectedDate,
                  'has-reservation': dailyMap[data.day]
                }"
                @click="handleDayClick(data.day)"
              >
                <div class="date-header">
                  <span class="day-number">
                    {{ data.day.split('-').slice(-1)[0] }}
                  </span>
                  <span
                    v-if="dailyMap[data.day]"
                    class="badge"
                  >
                    {{ dailyMap[data.day] }} 单
                  </span>
                </div>

                <div
                  v-if="dailyMap[data.day]"
                  class="mini-bar"
                >
                  <div class="fill"></div>
                </div>
              </div>
            </template>
          </el-calendar>
        </el-card>
      </el-col>

      <!-- 右侧：选中日期的预约明细 -->
      <el-col :span="10">
        <el-card shadow="hover" class="detail-card">
          <div class="detail-header">
            <div class="detail-title">
              <div class="label">选中日期：</div>
              <div class="value">{{ selectedDate }}</div>
            </div>
            <div class="detail-sub">
              共 {{ reservationsOfSelectedDay.length }} 条预约
            </div>
          </div>

          <el-table
            :data="reservationsOfSelectedDay"
            v-loading="loading"
            border
            size="small"
            style="width: 100%"
          >
            <el-table-column prop="court_name" label="场地" width="120" />
            <el-table-column prop="member_name" label="会员" width="120">
              <template #default="{ row }">
                <span v-if="row.member_name">{{ row.member_name }}</span>
                <span v-else class="text-muted">散客</span>
              </template>
            </el-table-column>
            <el-table-column prop="start_time" label="开始时间" width="150" />
            <el-table-column prop="end_time" label="结束时间" width="150" />
            <el-table-column prop="status" label="状态" width="90">
              <template #default="{ row }">
                <el-tag
                  v-if="row.status === '已预约'"
                  type="warning"
                  size="small"
                  effect="light"
                >
                  已预约
                </el-tag>
                <el-tag
                  v-else-if="row.status === '进行中'"
                  type="success"
                  size="small"
                  effect="light"
                >
                  进行中
                </el-tag>
                <el-tag
                  v-else-if="row.status === '已完成'"
                  type="info"
                  size="small"
                  effect="light"
                >
                  已完成
                </el-tag>
                <el-tag v-else type="danger" size="small" effect="light">
                  已取消
                </el-tag>
              </template>
            </el-table-column>
          </el-table>

          <div
            v-if="!loading && !reservationsOfSelectedDay.length"
            class="empty-text"
          >
            该日期暂无预约记录。
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import http from "../utils/http";

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
}

interface CourtOption {
  id: number;
  name: string;
}

// ====== 工具：日期格式 ======
const now = new Date();
const pad = (n: number) => (n < 10 ? `0${n}` : `${n}`);
const todayStr = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(
  now.getDate()
)}`;
const thisMonthStr = `${now.getFullYear()}-${pad(now.getMonth() + 1)}`;

// ====== 状态 ======
const loading = ref(false);
const reservations = ref<Reservation[]>([]);
const courtOptions = ref<CourtOption[]>([]);

// 当前月份（YYYY-MM） & 日历组件绑定的日期对象
const currentMonth = ref<string>(thisMonthStr);
const calendarDate = ref<Date>(new Date());

// 当前过滤场地（all 表示全部）
const activeCourtId = ref<number | "all">("all");

// 当前选中的具体日期（YYYY-MM-DD）
const selectedDate = ref<string>(todayStr);

// ====== 计算：当前月份 + 场地 的预约列表 ======
const reservationsForMonth = computed(() => {
  const month = currentMonth.value; // 'YYYY-MM'
  return reservations.value.filter((r) => {
    if (!r.start_time || !r.start_time.startsWith(month)) return false;
    if (activeCourtId.value !== "all" && r.court_id !== activeCourtId.value) {
      return false;
    }
    return true;
  });
});

// 每天的预约数量 map： { '2025-11-01': 3, ... }
const dailyMap = computed(() => {
  const map: Record<string, number> = {};
  reservationsForMonth.value.forEach((r) => {
    if (!r.start_time) return;
    const day = r.start_time.slice(0, 10);
    map[day] = (map[day] || 0) + 1;
  });
  return map;
});

// 选中日期的预约明细
const reservationsOfSelectedDay = computed(() =>
  reservationsForMonth.value.filter(
    (r) => r.start_time && r.start_time.slice(0, 10) === selectedDate.value
  )
);

// ====== 加载数据 ======
const loadReservations = async () => {
  try {
    loading.value = true;
    const res = await http.get<Reservation[]>("/court-reservations");
    reservations.value = res.data || [];
  } catch (err) {
    console.error(err);
  } finally {
    loading.value = false;
  }
};

const loadCourts = async () => {
  try {
    const res = await http.get<any[]>("/courts");
    courtOptions.value = (res.data || []).map((c: any) => ({
      id: c.id,
      name: c.name,
    }));
  } catch (err) {
    console.error(err);
  }
};

onMounted(() => {
  loadReservations();
  loadCourts();
});

// ====== 交互 ======
const handleMonthChange = () => {
  // 月份变了，把日历组件的日期跳到当月 1 号
  if (currentMonth.value) {
    calendarDate.value = new Date(`${currentMonth.value}-01T00:00:00`);
    // 同时把选中的日期重置为当月 1 号（如果你希望）
    selectedDate.value = `${currentMonth.value}-01`;
  }
};

const handleDayClick = (day: string) => {
  selectedDate.value = day;
};

// 如果切换了场地，但当前选中的日期在这个月没记录了，也没关系，右侧会显示“暂无记录”
watch(activeCourtId, () => {
  // 这里只需要触发 recomputed，不必重新请求接口
});
</script>

<style scoped>
.calendar-page {
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

.header-actions {
  display: flex;
  align-items: center;
}

.main-row {
  margin-top: 4px;
}

.calendar-card,
.detail-card {
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

/* 日历单元格样式 */
.date-cell {
  height: 64px;
  padding: 4px 6px;
  border-radius: 10px;
  transition: background-color 0.15s ease, box-shadow 0.15s ease;
  cursor: pointer;
}

.date-cell:hover {
  background-color: rgba(0, 122, 255, 0.08);
}

.date-cell.is-selected {
  background-color: rgba(0, 122, 255, 0.15);
  box-shadow: 0 0 0 1px #007AFF inset;
}

.date-cell.has-reservation:not(.is-selected) {
  background-color: rgba(0, 122, 255, 0.06);
}

.date-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.day-number {
  font-size: 14px;
  font-weight: 500;
  color: #1D1D1F;
}

.badge {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 999px;
  background-color: #FF9500;
  color: #fff;
}

.mini-bar {
  margin-top: 6px;
  height: 6px;
  border-radius: 999px;
  background-color: #E5E5EA;
  overflow: hidden;
}

.mini-bar .fill {
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, #FF9500, #34C759);
}

.detail-header {
  margin-bottom: 12px;
}

.detail-title {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.detail-title .label {
  font-size: 13px;
  color: #86868B;
}

.detail-title .value {
  font-size: 16px;
  font-weight: 600;
  color: #1D1D1F;
}

.detail-sub {
  margin-top: 2px;
  font-size: 12px;
  color: #86868B;
}

.empty-text {
  padding: 16px;
  text-align: center;
  font-size: 13px;
  color: #86868B;
}

.text-muted {
  color: #86868B;
}
</style>
