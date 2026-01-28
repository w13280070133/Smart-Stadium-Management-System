<template>
  <div class="page">
    <!-- 顶部标题 -->
    <div class="page-header">
      <div>
        <h2>场地管理</h2>
        <p class="sub-title">管理场地信息、价格与状态</p>
      </div>

      <el-button type="primary" @click="openAddDialog">
        新增场地
      </el-button>
    </div>

    <!-- 场地列表 -->
    <el-card class="card" shadow="hover">
      <el-table :data="courts" border style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="身份证" width="90" />
        <el-table-column prop="name" label="名称" width="160" />
        <el-table-column prop="type" label="类型" width="140" />
        <el-table-column
          prop="price_per_hour"
          label="每小时价格（元）"
          width="160"
        >
          <template #default="{ row }">
            ¥ {{ formatPrice(row.price_per_hour) }}
          </template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="120">
          <template #default="{ row }">
            <el-tag
              :type="
                row.status === '可用'
                  ? 'success'
                  : row.status === '维护'
                  ? 'warning'
                  : 'info'
              "
            >
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="location" label="位置" width="160" />
        <el-table-column prop="remark" label="备注" />

        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>

        <!-- 操作列：编辑 / 删除 + 状态设置 -->
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              size="small"
              @click="openEditDialog(row)"
            >
              编辑
            </el-button>

            <el-button
              link
              type="danger"
              size="small"
              @click="handleDelete(row)"
            >
              删除
            </el-button>

            <el-divider direction="vertical" />

            <el-dropdown @command="onStatusCommand($event, row)">
              <span class="el-dropdown-link">
                状态设置
                <el-icon class="el-icon--right">
                  <ArrowDown />
                </el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="可用">设为可用</el-dropdown-item>
                  <el-dropdown-item command="维护">设为维护</el-dropdown-item>
                  <el-dropdown-item command="停用">设为停用</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增 / 编辑场地弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '新增场地' : '编辑场地'"
      width="480px"
    >
      <el-form :model="form" label-width="90px">
        <el-form-item label="场地名称">
          <el-input v-model="form.name" placeholder="请输入场地名称" />
        </el-form-item>

        <el-form-item label="场地类型">
          <el-input v-model="form.type" placeholder="如：羽毛球、篮球" />
        </el-form-item>

        <el-form-item label="每小时价格">
          <el-input-number
            v-model="form.price_per_hour"
            :min="0"
            :step="10"
            :precision="2"
          />
        </el-form-item>

        <el-form-item label="位置">
          <el-input v-model="form.location" placeholder="如：一楼A区" />
        </el-form-item>

        <el-form-item label="备注">
          <el-input
            type="textarea"
            v-model="form.remark"
            :rows="3"
            placeholder="可填写用途说明等"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取 消</el-button>
          <el-button type="primary" :loading="saving" @click="submitForm">
            确 定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { ArrowDown } from "@element-plus/icons-vue";
import http from "../utils/http";

type DialogMode = "create" | "edit";

interface Court {
  id: number;
  name: string;
  type: string;
  price_per_hour: number;
  status: string;
  location?: string | null;
  remark?: string | null;
  created_at: string;
}

interface CourtForm {
  name: string;
  type: string;
  price_per_hour: number;
  location: string;
  remark: string;
}

const courts = ref<Court[]>([]);
const loading = ref(false);

const dialogVisible = ref(false);
const saving = ref(false);
const dialogMode = ref<DialogMode>("create");
const editingId = ref<number | null>(null);

const form = ref<CourtForm>({
  name: "",
  type: "",
  price_per_hour: 0,
  location: "",
  remark: "",
});

// 价格格式化，避免 toFixed 报错
const formatPrice = (value: unknown) => {
  const n = Number(value);
  if (Number.isNaN(n)) return "0.00";
  return n.toFixed(2);
};

// 时间格式化
const formatTime = (t: string) => {
  if (!t) return "";
  return t.replace("T", " ").slice(0, 19);
};

// 加载场地列表
const loadCourts = async () => {
  try {
    loading.value = true;
    const res = await http.get<Court[]>("/courts");
    courts.value = res.data || [];
  } catch (err) {
    console.error(err);
    ElMessage.error("获取场地列表失败");
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  loadCourts();
});

// 打开新增弹窗
const openAddDialog = () => {
  dialogMode.value = "create";
  editingId.value = null;
  form.value = {
    name: "",
    type: "",
    price_per_hour: 0,
    location: "",
    remark: "",
  };
  dialogVisible.value = true;
};

// 打开编辑弹窗
const openEditDialog = (row: Court) => {
  dialogMode.value = "edit";
  editingId.value = row.id;
  form.value = {
    name: row.name,
    type: row.type,
    price_per_hour: Number(row.price_per_hour) || 0,
    location: row.location || "",
    remark: row.remark || "",
  };
  dialogVisible.value = true;
};

// 提交表单（新增 / 编辑）
const submitForm = async () => {
  if (!form.value.name || !form.value.type) {
    ElMessage.warning("请填写场地名称和类型");
    return;
  }

  try {
    saving.value = true;

    if (dialogMode.value === "create") {
      await http.post("/courts", form.value);
      ElMessage.success("新增场地成功");
    } else if (dialogMode.value === "edit" && editingId.value !== null) {
      await http.put(`/courts/${editingId.value}`, form.value);
      ElMessage.success("修改场地成功");
    }

    dialogVisible.value = false;
    loadCourts();
  } catch (err) {
    console.error(err);
    ElMessage.error("保存失败，请稍后重试");
  } finally {
    saving.value = false;
  }
};

// 删除场地
const handleDelete = (row: Court) => {
  ElMessageBox.confirm(
    `确定要删除场地「${row.name}」吗？`,
    "删除确认",
    {
      type: "warning",
      confirmButtonText: "删除",
      cancelButtonText: "取消",
    }
  )
    .then(async () => {
      try {
        await http.delete(`/courts/${row.id}`);
        ElMessage.success("删除成功");
        loadCourts();
      } catch (err) {
        console.error(err);
        ElMessage.error("删除失败，请稍后重试");
      }
    })
    .catch(() => {
      /* 用户取消 */
    });
};

// 状态下拉菜单的命令
const handleStatusCommand = async (cmd: string, row: Court) => {
  try {
    await http.put(`/courts/${row.id}/status`, { status: cmd });
    ElMessage.success("更新场地状态成功");
    loadCourts();
  } catch (err) {
    console.error(err);
    ElMessage.error("更新状态失败，请稍后重试");
  }
};

const onStatusCommand = (cmd: string, row: Court) => {
  handleStatusCommand(cmd, row);
};
</script>

<style scoped>
.page {
  padding: 16px 24px 24px;
  background: #F2F2F7;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.page-header h2 {
  margin: 0;
  color: #1D1D1F;
}

.sub-title {
  margin: 4px 0 0;
  color: #86868B;
  font-size: 13px;
}

.card {
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.el-dropdown-link {
  cursor: pointer;
  color: #FF9500;
  display: inline-flex;
  align-items: center;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
