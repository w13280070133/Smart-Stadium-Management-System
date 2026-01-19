<template>
  <div class="audit-page">
    <div class="page-header">
      <div>
        <h2>操作日志</h2>
        <p class="sub-title">记录后台关键操作（新增 / 修改 / 删除等）</p>
      </div>
    </div>

    <!-- 筛选区 -->
    <el-card shadow="never" class="card filter-card">
      <div class="filter-bar">
        <div class="filter-left">
          <el-input
            v-model="username"
            placeholder="按用户名搜索"
            style="width: 180px"
            clearable
            @keyup.enter="reload"
          />
          <el-input
            v-model="module"
            placeholder="模块（如 employee / product）"
            style="width: 200px; margin-left: 12px"
            clearable
            @keyup.enter="reload"
          />
          <el-input
            v-model="action"
            placeholder="动作（如 CREATE_EMPLOYEE）"
            style="width: 220px; margin-left: 12px"
            clearable
            @keyup.enter="reload"
          />

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
        <el-table-column prop="username" label="操作人" width="130" />
        <el-table-column prop="module" label="模块" width="120" />
        <el-table-column prop="action" label="动作" width="180">
          <template #default="{ row }">
            {{ actionMap[row.action] || row.action }}
          </template>
        </el-table-column>
        <el-table-column prop="target_id" label="目标ID" width="90" />
        <el-table-column prop="target_desc" label="目标说明" width="160" />
        <el-table-column prop="detail" label="详细变更" min-width="260">
          <template #default="{ row }">
            <span class="detail-text">{{ formatDetail(row.detail) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="ip" label="IP" width="140" />
        <el-table-column prop="created_at" label="时间" width="180" />
      </el-table>

      <div v-if="!loading && logs.length === 0" class="empty-tip">
        暂无操作日志记录。
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

interface OperationLog {
  id: number;
  user_id: number;
  username: string;
  action: string;
  module: string;
  target_id: number | null;
  target_desc: string | null;
  detail: string | null; // JSON 字符串
  ip: string | null;
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
const logs = ref<OperationLog[]>([]);
const total = ref(0);

const page = ref(1);
const pageSize = ref(20);

const username = ref<string>("");
const module = ref<string>("");
const action = ref<string>("");

// 动作名称映射（英文 -> 中文）
const actionMap: Record<string, string> = {
  // 通用操作
  "CREATE": "新增",
  "UPDATE": "更新",
  "DELETE": "删除",
  "VIEW": "查看",
  "EXPORT": "导出",
  // 会员相关
  "CREATE_MEMBER": "新增会员",
  "UPDATE_MEMBER": "更新会员",
  "DELETE_MEMBER": "删除会员",
  "RECHARGE": "会员充值",
  // 员工相关
  "CREATE_EMPLOYEE": "新增员工",
  "UPDATE_EMPLOYEE": "更新员工",
  "DELETE_EMPLOYEE": "删除员工",
  // 商品相关
  "CREATE_PRODUCT": "新增商品",
  "UPDATE_PRODUCT": "更新商品",
  "DELETE_PRODUCT": "删除商品",
  "CREATE_PRODUCT_SALE": "商品售卖",
  "REFUND_PRODUCT_SALE": "商品退款",
  // 场地相关
  "CREATE_COURT": "新增场地",
  "UPDATE_COURT": "更新场地",
  "DELETE_COURT": "删除场地",
  "CREATE_RESERVATION": "新增预约",
  "CANCEL_RESERVATION": "取消预约",
  // 培训相关
  "CREATE_COURSE": "新增课程",
  "UPDATE_COURSE": "更新课程",
  "DELETE_COURSE": "删除课程",
  "CREATE_ENROLLMENT": "课程报名",
  "REFUND_ENROLLMENT": "课程退费",
  "CREATE_ATTENDANCE": "签到",
  "DELETE_ATTENDANCE": "撤销签到",
  // 系统相关
  "UPDATE_SETTINGS": "更新设置",
  "DATA_CLEAN": "数据格式化",
  "LOGIN": "登录",
  "LOGOUT": "登出",
  // 中文动作（直接显示）
  "签到": "签到",
  "创建": "创建",
  "退费": "退费",
};

function formatDetail(detail: string | null): string {
  if (!detail) return "—";
  try {
    const obj = JSON.parse(detail);
    const str = JSON.stringify(obj);
    return str.length > 80 ? str.slice(0, 80) + "..." : str;
  } catch {
    return detail.length > 80 ? detail.slice(0, 80) + "..." : detail;
  }
}

async function loadLogs() {
  loading.value = true;
  try {
    const params: any = {
      page: page.value,
      page_size: pageSize.value,
    };
    if (username.value) params.username = username.value;
    if (module.value) params.module = module.value;
    if (action.value) params.action = action.value;

    const res = await api.get("/audit/operation-logs", {
      params,
      headers: authHeaders(),
    });
    total.value = res.data.total || 0;
    logs.value = res.data.items || [];
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "获取操作日志失败");
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
  module.value = "";
  action.value = "";
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

.detail-text {
  display: inline-block;
  max-width: 360px;
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
