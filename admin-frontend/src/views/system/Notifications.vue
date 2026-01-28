<template>
  <div class="notifications-page">
    <div class="page-header">
      <div>
        <h2>通知中心</h2>
        <p class="sub-title">查看系统提醒和业务通知</p>
      </div>
      <div class="header-actions">
        <el-button @click="reload">刷新</el-button>
        <el-button type="primary" @click="markAllRead" :disabled="items.length === 0">全部标记已读</el-button>
        <el-button type="success" @click="exportCsv" :disabled="items.length === 0">导出 CSV</el-button>
      </div>
    </div>

    <el-card shadow="hover" class="card">
      <div class="filters">
        <el-select
          v-model="filterRead"
          placeholder="全部"
          style="width: 140px"
        >
          <el-option label="全部" :value="-1" />
          <el-option label="未读" :value="0" />
          <el-option label="已读" :value="1" />
        </el-select>

        <el-select v-model="filterLevel" placeholder="级别" style="width: 140px" clearable>
          <el-option label="全部" value="" />
          <el-option label="提示" value="info" />
          <el-option label="警告" value="warning" />
          <el-option label="错误" value="error" />
        </el-select>

        <el-input
          v-model="filterKeyword"
          placeholder="标题 / 内容关键字"
          clearable
          style="width: 220px"
        />
      </div>

      <el-table
        :data="items"
        border
        stripe
        v-loading="loading"
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column label="级别" width="90">
          <template #default="{ row }">
            <el-tag
              :type="levelTagType(row.level)"
              effect="plain"
            >
              {{ renderLevel(row.level) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" width="200" />
        <el-table-column
          prop="content"
          label="内容"
          min-width="260"
          show-overflow-tooltip
        />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.is_read ? 'info' : 'success'" effect="plain">
              {{ row.is_read ? "已读" : "未读" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="170">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="阅读时间" width="170">
          <template #default="{ row }">
            {{ row.read_at ? formatDateTime(row.read_at) : "-" }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="!row.is_read"
              link
              type="primary"
              size="small"
              @click="markRead(row)"
            >
              标记已读
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && items.length === 0" class="empty-tip">
        暂无通知。
      </div>

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
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onBeforeUnmount } from "vue";
import { ElMessage } from "element-plus";
import http from "@/utils/http";

interface NotificationItem {
  id: number;
  title: string;
  content: string;
  level: string;
  is_read: number;
  created_at: string | null;
  read_at: string | null;
}

const loading = ref(false);
const items = ref<NotificationItem[]>([]);
const total = ref(0);
const page = ref(1);
const pageSize = 20;
const filterRead = ref(-1); // -1 全部，0 未读，1 已读
const filterLevel = ref<string>("");
const filterKeyword = ref("");

function formatDateTime(val: string | null): string {
  if (!val) return "";
  return val.replace("T", " ").slice(0, 19);
}

function renderLevel(level: string | null | undefined): string {
  switch (level) {
    case "warning":
      return "警告";
    case "error":
      return "错误";
    default:
      return "提示";
  }
}

function levelTagType(level: string | null | undefined): "info" | "warning" | "danger" | "success" {
  switch (level) {
    case "warning":
      return "warning";
    case "error":
      return "danger";
    default:
      return "info";
  }
}

async function loadList() {
  loading.value = true;
  try {
    const params: any = {
      page: page.value,
      page_size: pageSize,
    };
    if (filterRead.value === 0 || filterRead.value === 1) {
      params.is_read = filterRead.value;
    }
    if (filterLevel.value) {
      params.level = filterLevel.value;
    }
    if (filterKeyword.value.trim()) {
      params.keyword = filterKeyword.value.trim();
    }

    const res = await http.get("/notifications", { params });
    const data = res.data || {};
    items.value = Array.isArray(data.items) ? data.items : [];
    total.value = Number(data.total || 0);
  } catch (e: any) {
    console.error(e);
    ElMessage.error(e?.response?.data?.detail || "获取通知失败");
  } finally {
    loading.value = false;
  }
}

function handlePageChange(p: number) {
  page.value = p;
  loadList();
}

function reload() {
  page.value = 1;
  loadList();
}

async function markRead(row: NotificationItem) {
  try {
    await http.put(`/notifications/${row.id}/read`);
    ElMessage.success("已标记为已读");
    loadList();
  } catch (e: any) {
    console.error(e);
    ElMessage.error(e?.response?.data?.detail || "操作失败");
  }
}

async function markAllRead() {
  if (!items.value.length) return;
  try {
    await http.put("/notifications/read-all");
    ElMessage.success("全部通知已标记为已读");
    loadList();
  } catch (e: any) {
    console.error(e);
    ElMessage.error(e?.response?.data?.detail || "操作失败");
  }
}

function exportCsv() {
  if (!items.value.length) return;
  const headers = ["ID", "标题", "内容", "级别", "状态", "创建时间", "阅读时间"];
  const rows = items.value.map((item) => [
    item.id,
    `"${item.title.replace(/"/g, '""')}"`,
    `"${(item.content || "").replace(/"/g, '""')}"`,
    renderLevel(item.level),
    item.is_read ? "已读" : "未读",
    formatDateTime(item.created_at),
    formatDateTime(item.read_at),
  ]);
  const csvContent = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `notifications_${Date.now()}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

watch([filterRead, filterLevel], () => {
  page.value = 1;
  loadList();
});

let keywordTimer: number | null = null;
watch(filterKeyword, () => {
  if (keywordTimer) window.clearTimeout(keywordTimer);
  keywordTimer = window.setTimeout(() => {
    page.value = 1;
    loadList();
  }, 400);
});

onBeforeUnmount(() => {
  if (keywordTimer) window.clearTimeout(keywordTimer);
});

loadList();
</script>

<style scoped>
.notifications-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.page-header h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  color: #1D1D1F;
}

.sub-title {
  margin-top: 4px;
  font-size: 13px;
  color: #86868B;
}

.card {
  border-radius: 12px;
  background: #fff;
  border: none;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.filters {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.empty-tip {
  margin-top: 16px;
  text-align: center;
  color: #86868B;
  font-size: 13px;
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
