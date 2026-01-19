<template>
  <div class="audit-page">
    <div class="page-header">
      <div>
        <h2>登录日志</h2>
        <p class="sub-title">查看后台账号的登录记录（成功 / 失败）</p>
      </div>
    </div>

    <!-- 筛选区 -->
    <el-card shadow="never" class="card filter-card">
      <div class="filter-bar">
        <div class="filter-left">
          <el-input
            v-model="username"
            placeholder="按用户名搜索"
            style="width: 200px"
            clearable
            @keyup.enter="reload"
          />
          <el-select
            v-model="success"
            placeholder="登录结果"
            clearable
            style="width: 140px; margin-left: 12px"
            @change="reload"
          >
            <el-option :value="undefined" label="全部结果" />
            <el-option :value="1" label="成功" />
            <el-option :value="0" label="失败" />
          </el-select>

          <el-button type="primary" text style="margin-left: 8px" @click="reload">
            查询
          </el-button>
        </div>

        <div class="filter-right">
          <el-button text @click="resetFilters">重置</el-button>
        </div>
      </div>
    </el-card>

    <!-- 列表 -->
    <el-card shadow="hover" class="card">
      <el-table
        :data="logs"
        border
        style="width: 100%"
        v-loading="loading"
      >
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="ip" label="IP 地址" width="140" />
        <el-table-column prop="user_agent" label="客户端" min-width="220">
          <template #default="{ row }">
            <span class="ua-text">{{ row.user_agent }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="success" label="结果" width="90">
          <template #default="{ row }">
            <el-tag
              v-if="row.success === 1"
              type="success"
              size="small"
              effect="plain"
            >
              成功
            </el-tag>
            <el-tag
              v-else
              type="danger"
              size="small"
              effect="plain"
            >
              失败
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="message" label="说明" min-width="160" />
        <el-table-column prop="created_at" label="时间" width="180" />
      </el-table>

      <div v-if="!loading && logs.length === 0" class="empty-tip">
        暂无登录日志记录。
      </div>

      <div class="pagination" v-if="total > 0">
        <el-pagination
          background
          layout="prev, pager, next, jumper, ->, total"
          :current-page="page"
          :page-size="pageSize"
          :total="total"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import axios from "axios";
import { ElMessage } from "element-plus";

interface LoginLog {
  id: number;
  user_id: number;
  username: string;
  ip: string | null;
  user_agent: string | null;
  success: number; // 1 成功 0 失败
  message: string | null;
  created_at: string;
}

const api = axios.create({
  baseURL: "http://localhost:9000/api",
});

function authHeaders() {
  const token = localStorage.getItem("token") || "";
  return { Authorization: `Bearer ${token}` };
}

const loading = ref(false);
const logs = ref<LoginLog[]>([]);
const total = ref(0);

const page = ref(1);
const pageSize = ref(20);

const username = ref<string>("");
const success = ref<number | undefined>(undefined);

async function loadLogs() {
  loading.value = true;
  try {
    const params: any = {
      page: page.value,
      page_size: pageSize.value,
    };
    if (username.value) params.username = username.value;
    if (success.value === 0 || success.value === 1) {
      params.success = success.value;
    }

    const res = await api.get("/audit/login-logs", {
      params,
      headers: authHeaders(),
    });
    total.value = res.data.total || 0;
    logs.value = res.data.items || [];
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "获取登录日志失败");
  } finally {
    loading.value = false;
  }
}

function handlePageChange(p: number) {
  page.value = p;
  loadLogs();
}

function resetFilters() {
  username.value = "";
  success.value = undefined;
  page.value = 1;
  loadLogs();
}

function reload() {
  page.value = 1;
  loadLogs();
}

onMounted(() => {
  loadLogs();
});
</script>

<style scoped>
.audit-page {
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

.filter-card {
  margin-bottom: 0;
}

.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.filter-left {
  display: flex;
  align-items: center;
}

.ua-text {
  display: inline-block;
  max-width: 260px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.empty-tip {
  margin-top: 16px;
  text-align: center;
  color: #9ca3af;
  font-size: 13px;
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
