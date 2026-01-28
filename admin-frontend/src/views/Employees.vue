<template>
  <div class="employees-page">
    <div class="page-header">
      <div>
        <h2>员工 & 账号管理</h2>
        <p class="sub-title">维护后台登录账号、角色与在职状态</p>
      </div>
      <el-button type="primary" size="large" @click="openAddDialog" :disabled="!canCreate">新增账号</el-button>
    </div>

    <el-card shadow="hover" class="card">
      <el-table :data="employees" border style="width: 100%">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column prop="position" label="岗位" width="140" />
        <el-table-column prop="phone" label="手机号" width="140" />
        <el-table-column prop="username" label="登录账号" width="160" />
        <el-table-column prop="role" label="角色" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.role === 'admin'" type="danger" effect="plain">管理员</el-tag>
            <el-tag v-else type="info" effect="plain">员工</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.is_active && row.user_active ? 'success' : 'info'" effect="plain">
              {{ row.is_active && row.user_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="hire_date" label="入职日期" width="140" />
        <el-table-column label="操作" fixed="right" width="220">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="openEditDialog(row)" :disabled="!canEdit">
              编辑
            </el-button>
            <el-button
              link
              type="warning"
              size="small"
              @click="toggleActive(row)"
              :disabled="!canEdit"
            >
              {{ row.is_active && row.user_active ? '禁用' : '启用' }}
            </el-button>
            <el-popconfirm
              title="确认删除该员工（将同时删除对应账号）？"
              confirm-button-text="删除"
              cancel-button-text="取消"
              @confirm="removeEmployee(row)"
              :disabled="!canDelete"
            >
              <template #reference>
                <el-button link type="danger" size="small" :disabled="!canDelete">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="employees.length === 0" class="empty-tip">
        暂无员工账号，请点击右上角「新增账号」添加
      </div>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑员工' : '新增员工账号'" width="520px">
      <el-form :model="form" label-width="90px" class="form">
        <el-form-item label="姓名">
          <el-input v-model="form.name" placeholder="如：张三" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="form.phone" placeholder="用于联系员工" />
        </el-form-item>
        <el-form-item label="岗位">
          <el-input v-model="form.position" placeholder="如：前台 / 教练 / 运营" />
        </el-form-item>
        <el-form-item label="入职日期">
          <el-date-picker v-model="form.hire_date" type="date" placeholder="选择日期" style="width: 100%" />
        </el-form-item>
        <el-form-item label="登录账号">
          <el-input v-model="form.username" :disabled="isEdit" placeholder="用于后台登录" />
        </el-form-item>
        <el-form-item v-if="!isEdit" label="初始密码">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item v-else label="重置密码">
          <el-input
            v-model="form.reset_password"
            type="password"
            show-password
            placeholder="留空则不修改密码"
          />
        </el-form-item>
        <el-form-item label="角色">
          <el-radio-group v-model="form.role">
            <el-radio label="admin">管理员</el-radio>
            <el-radio label="staff">员工</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :disabled="!canEdit">
          {{ isEdit ? '保存修改' : '确认创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import axios from "axios";
import { ElMessage } from "element-plus";
import { hasAction } from "@/utils/permission";

interface EmployeeRow {
  id: number;
  user_id: number;
  name: string;
  position?: string;
  phone?: string;
  hire_date?: string;
  is_active: number;
  username: string;
  role: "admin" | "staff";
  user_active: number;
}

const api = axios.create({
  baseURL: "http://localhost:9000/api",
});

function authHeaders() {
  const token = localStorage.getItem("token") || "";
  return { Authorization: `Bearer ${token}` };
}

const employees = ref<EmployeeRow[]>([]);
const dialogVisible = ref(false);
const isEdit = ref(false);
const currentId = ref<number | null>(null);

const form = ref<any>({
  name: "",
  phone: "",
  position: "",
  hire_date: null as any,
  username: "",
  password: "",
  reset_password: "",
  role: "staff",
});

const canCreate = hasAction("employee.create");
const canEdit = hasAction("employee.edit");
const canDelete = hasAction("employee.delete");

async function loadEmployees() {
  const res = await api.get<EmployeeRow[]>("/employees", {
    headers: authHeaders(),
  });
  employees.value = res.data;
}

function openAddDialog() {
  if (!canCreate) return;
  isEdit.value = false;
  currentId.value = null;
  form.value = {
    name: "",
    phone: "",
    position: "",
    hire_date: null,
    username: "",
    password: "",
    reset_password: "",
    role: "staff",
  };
  dialogVisible.value = true;
}

function openEditDialog(row: EmployeeRow) {
  if (!canEdit) return;
  isEdit.value = true;
  currentId.value = row.id;
  form.value = {
    name: row.name,
    phone: row.phone || "",
    position: row.position || "",
    hire_date: row.hire_date ? new Date(row.hire_date) : null,
    username: row.username,
    password: "",
    reset_password: "",
    role: row.role,
  };
  dialogVisible.value = true;
}

function formatDate(date: Date | null): string | null {
  if (!date) return null;
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

async function submitForm() {
  if (!canEdit && isEdit.value) return;
  try {
    const payload: any = {
      name: form.value.name,
      phone: form.value.phone,
      position: form.value.position,
      hire_date: formatDate(form.value.hire_date),
      role: form.value.role,
    };

    if (!isEdit.value) {
      if (!form.value.username || !form.value.password) {
        ElMessage.error("请填写登录账号和初始密码");
        return;
      }
      payload.username = form.value.username;
      payload.password = form.value.password;
      await api.post("/employees", payload, { headers: authHeaders() });
      ElMessage.success("创建成功");
    } else {
      if (form.value.reset_password) {
        payload.reset_password = form.value.reset_password;
      }
      await api.put(`/employees/${currentId.value}`, payload, {
        headers: authHeaders(),
      });
      ElMessage.success("保存成功");
    }

    dialogVisible.value = false;
    await loadEmployees();
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "操作失败");
  }
}

async function toggleActive(row: EmployeeRow) {
  if (!canEdit) return;
  try {
    const newActive = !(row.is_active && row.user_active);
    await api.put(
      `/employees/${row.id}`,
      { is_active: newActive },
      { headers: authHeaders() }
    );
    ElMessage.success(newActive ? "已启用" : "已禁用");
    await loadEmployees();
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "操作失败");
  }
}

async function removeEmployee(row: EmployeeRow) {
  if (!canDelete) return;
  try {
    await api.delete(`/employees/${row.id}`, { headers: authHeaders() });
    ElMessage.success("删除成功");
    await loadEmployees();
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "删除失败");
  }
}

onMounted(() => {
  loadEmployees();
});
</script>

<style scoped>
.employees-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: #F2F2F7;
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
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.empty-tip {
  margin-top: 16px;
  text-align: center;
  color: #86868B;
  font-size: 13px;
}

.form :deep(.el-input),
.form :deep(.el-select),
.form :deep(.el-date-editor) {
  width: 100%;
}
</style>
