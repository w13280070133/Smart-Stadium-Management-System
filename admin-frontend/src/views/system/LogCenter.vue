<template>
  <div class="page log-center-page">
    <div class="page-header">
      <div>
        <h2>日志中心</h2>
        <p class="sub-title">以业务动作为主线，记录新增/修改/退款等关键操作，适合答辩展示</p>
      </div>
      <div class="header-actions">
        <el-button @click="reload">刷新</el-button>
        <el-button type="success" @click="exportLogs" :disabled="logs.length === 0">导出 CSV</el-button>
      </div>
    </div>

    <el-card shadow="hover" class="card filter-card">
      <div class="filter-row">
        <el-input
          v-model="filters.username"
          placeholder="操作者"
          size="small"
          clearable
        />
        <el-input
          v-model="filters.module"
          placeholder="模块"
          size="small"
          clearable
        />
        <el-input
          v-model="filters.action"
          placeholder="动作"
          size="small"
          clearable
        />
        <el-date-picker
          v-model="filters.dateRange"
          type="daterange"
          size="small"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
        />
        <el-button type="primary" size="small" @click="reload">应用筛选</el-button>
        <el-button size="small" @click="resetFilters">重置</el-button>
      </div>
    </el-card>

    <el-card shadow="hover" class="card log-card" v-loading="loading">
      <el-timeline>
        <el-timeline-item
          v-for="log in logs"
          :key="log.id"
          :timestamp="formatTime(log.created_at)"
          placement="top"
        >
          <div class="log-badge">
            <el-tag size="small" :type="tagType(log.module)">{{ log.module || "系统" }}</el-tag>
            <el-tag size="small" type="success">{{ actionLabel(log.action) }}</el-tag>
          </div>
          <div class="log-content">
            <div class="log-main">
              <span class="log-user">{{ log.username || "system" }}</span>
              <span>对</span>
              <span class="log-target">{{ log.target_desc || `ID:${log.target_id}` }}</span>
            </div>
            <div class="log-detail">{{ formatDetail(log.detail) }}</div>
            <div class="log-meta">
              <span>IP: {{ log.ip || "-" }}</span>
              <span>模块: {{ log.module || "-" }}</span>
              <span>动作: {{ log.action || "-" }}</span>
            </div>
          </div>
        </el-timeline-item>
      </el-timeline>
      <div v-if="!loading && logs.length === 0" class="empty-tip">暂无操作日志</div>
    </el-card>

    <div class="pagination" v-if="total > 0">
      <el-pagination
        background
        layout="prev, pager, next, jumper"
        :current-page="page"
        :page-size="pageSize"
        :total="total"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { ElMessage } from "element-plus";
import http from "../../utils/http";

interface LogRow {
  id: number;
  username: string;
  action: string;
  module: string;
  target_id: number | null;
  target_desc: string | null;
  detail: string | null;
  ip: string | null;
  created_at: string;
}

const logs = ref<LogRow[]>([]);
const loading = ref(false);
const total = ref(0);
const page = ref(1);
const pageSize = ref(15);

const filters = ref<{
  username: string;
  module: string;
  action: string;
  dateRange: [string, string] | null;
}>({
  username: "",
  module: "",
  action: "",
  dateRange: null,
});

const loadLogs = async () => {
  loading.value = true;
  try {
    const params: any = {
      page: page.value,
      page_size: pageSize.value,
    };
    if (filters.value.username) params.username = filters.value.username.trim();
    if (filters.value.module) params.module = filters.value.module.trim();
    if (filters.value.action) params.action = filters.value.action.trim();
    if (filters.value.dateRange) {
      params.start_date = filters.value.dateRange[0];
      params.end_date = filters.value.dateRange[1];
    }
    const res = await http.get("/audit/operation-logs", { params });
    logs.value = res.data.items || [];
    total.value = res.data.total || 0;
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "获取日志失败");
  } finally {
    loading.value = false;
  }
};

const reload = () => {
  page.value = 1;
  loadLogs();
};

const resetFilters = () => {
  filters.value = { username: "", module: "", action: "", dateRange: null };
  reload();
};

const exportLogs = () => {
  if (!logs.value.length) return;
  const headers = ["时间", "用户", "模块", "动作", "目标", "详情", "IP"];
  const rows = logs.value.map((log) => [
    formatTime(log.created_at),
    log.username || "system",
    log.module || "-",
    log.action || "-",
    log.target_desc || log.target_id || "-",
    (log.detail || "").replace(/\r?\n/g, " "),
    log.ip || "-",
  ]);
  const csv = [headers.join(","), ...rows.map((r) => r.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(","))].join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `logs_${Date.now()}.csv`;
  link.click();
  URL.revokeObjectURL(url);
};

const handlePageChange = (p: number) => {
  page.value = p;
  loadLogs();
};

const formatDetail = (detail: string | null) => {
  if (!detail) return "无详情";
  try {
    const parsed = JSON.parse(detail);
    return JSON.stringify(parsed, null, 0);
  } catch {
    return detail;
  }
};

const formatTime = (dt: string) => {
  return dt ? dt.replace("T", " ").slice(0, 19) : "";
};

const actionLabel = (code: string | null) => {
  if (!code) return "业务动作";
  const mapping: Record<string, string> = {
    CREATE_MEMBER: "新增会员",
    UPDATE_MEMBER: "更新会员",
    CREATE_RESERVATION: "新增预约",
    CANCEL_RESERVATION: "取消预约",
    CREATE_PRODUCT_SALE: "商品售卖",
  };
  return mapping[code] || code;
};

const tagType = (module: string | null) => {
  if (!module) return "info";
  if (module.includes("training")) return "success";
  if (module.includes("product")) return "warning";
  return "info";
};

loadLogs();
</script>

<style scoped>
.log-center-page {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px 24px 24px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.page-header h2 {
  color: #1D1D1F;
}
.sub-title {
  margin-top: 4px;
  font-size: 13px;
  color: #86868B;
}
.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.card {
  border-radius: 12px;
  background: #fff;
  border: none;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.filter-card {
  border-radius: 12px;
}
.filter-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
}
.log-card {
  padding-bottom: 24px;
}
.log-badge {
  display: flex;
  gap: 8px;
  margin-bottom: 6px;
}
.log-content {
  border: none;
  border-radius: 12px;
  padding: 12px;
  background: #F5F5F7;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.log-main {
  font-weight: 600;
  margin-bottom: 6px;
  color: #1D1D1F;
}
.log-user {
  color: #007AFF;
}
.log-target {
  color: #FF9500;
}
.log-detail {
  color: #1D1D1F;
  font-size: 13px;
  margin-bottom: 6px;
}
.log-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #86868B;
}
.empty-tip {
  text-align: center;
  padding: 16px;
  color: #86868B;
}
.pagination {
  display: flex;
  justify-content: flex-end;
}
</style>
