<template>
  <div class="page">
    <div class="page-header">
      <div>
        <div class="page-header-title">消息通知</div>
        <div class="page-header-subtitle">查看预约、报名、退款等系统提醒</div>
      </div>
    </div>

    <el-card shadow="hover" class="page-card">
      <div class="filters">
        <el-radio-group v-model="filterRead" size="small" @change="loadData">
          <el-radio-button :label="''">全部</el-radio-button>
          <el-radio-button label="unread">未读</el-radio-button>
          <el-radio-button label="read">已读</el-radio-button>
        </el-radio-group>
      </div>

      <el-table
        :data="list"
        border
        style="width: 100%"
        size="small"
        v-loading="loading"
      >
        <el-table-column prop="title" label="标题" min-width="180" />
        <el-table-column prop="content" label="内容" min-width="280" />
        <el-table-column prop="created_at" label="时间" width="170" />
        <el-table-column prop="is_read" label="状态" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="row.is_read ? 'info' : 'success'">
              {{ row.is_read ? "已读" : "未读" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
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
            <span v-else class="muted">-</span>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && !list.length" class="empty">
        暂无通知
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { ElMessage } from "element-plus";
import api from "@/utils/api";

interface Notif {
  id: number;
  title: string;
  content: string;
  level?: string;
  is_read: 0 | 1;
  created_at?: string;
}

const list = ref<Notif[]>([]);
const loading = ref(false);
const filterRead = ref<"" | "read" | "unread">("");

const loadData = async () => {
  loading.value = true;
  try {
    const params: any = {};
    if (filterRead.value === "read") params.is_read = 1;
    if (filterRead.value === "unread") params.is_read = 0;
    const res = await api.get("/member/notifications", { params });
    const payload = res.data;
    if (Array.isArray(payload)) {
      list.value = payload;
    } else if (payload?.items && Array.isArray(payload.items)) {
      list.value = payload.items;
    } else if (payload?.data && Array.isArray(payload.data)) {
      list.value = payload.data;
    } else {
      list.value = [];
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "加载通知失败");
  } finally {
    loading.value = false;
  }
};

const markRead = async (row: Notif) => {
  try {
    await api.put(`/member/notifications/${row.id}/read`);
    row.is_read = 1;
    ElMessage.success("已标记为已读");
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "操作失败");
  }
};

onMounted(loadData);
</script>

<style scoped>
.page {
  width: 100%;
}

.page-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: 12px;
}

.page-header-title {
  font-size: 18px;
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

.filters {
  margin-bottom: 10px;
}

.empty {
  text-align: center;
  padding: 18px 0;
  color: #9ca3af;
}

.muted {
  color: #9ca3af;
  font-size: 12px;
}
</style>
