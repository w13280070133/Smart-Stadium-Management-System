<template>
  <div class="coaches-page">
    <div class="page-header">
      <div>
        <h2>教练管理</h2>
        <p class="sub-title">管理教练信息、擅长项目和课时费</p>
      </div>
      <el-button type="primary" @click="handleAdd">新增教练</el-button>
    </div>

    <el-card shadow="hover" class="filter-card">
      <div class="filters">
        <el-input
          v-model="filters.keyword"
          placeholder="搜索姓名/电话"
          clearable
          style="width: 200px"
          @keyup.enter="onSearch"
        />
        <el-select v-model="filters.status" placeholder="状态" clearable style="width: 140px">
          <el-option label="全部" value="" />
          <el-option label="在职" value="在职" />
          <el-option label="离职" value="离职" />
          <el-option label="休假" value="休假" />
        </el-select>
        <el-select v-model="filters.specialty" placeholder="擅长项目" clearable style="width: 140px">
          <el-option v-for="s in specialtyOptions" :key="s" :label="s" :value="s" />
        </el-select>
        <el-button type="primary" @click="onSearch">查询</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </div>
    </el-card>

    <el-card shadow="hover" class="table-card">
      <el-table :data="coaches" border stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="phone" label="联系电话" width="130" />
        <el-table-column prop="gender" label="性别" width="80" />
        <el-table-column prop="specialties" label="擅长项目" min-width="150" />
        <el-table-column prop="hourly_rate" label="课时费" width="100">
          <template #default="{ row }">
            <span>¥{{ row.hourly_rate }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="statusTag(row.status)">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
            <el-popconfirm
              title="确定删除该教练吗？"
              @confirm="handleDelete(row.id)"
            >
              <template #reference>
                <el-button link type="danger" size="small">删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination" v-if="total > 0">
        <el-pagination
          background
          layout="total, prev, pager, next"
          :total="total"
          :page-size="pageSize"
          :current-page="page"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      :title="dialogTitle"
      v-model="dialogVisible"
      width="600px"
      @close="resetForm"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" placeholder="请输入教练姓名" />
        </el-form-item>
        <el-form-item label="联系电话" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入联系电话" />
        </el-form-item>
        <el-form-item label="性别" prop="gender">
          <el-radio-group v-model="form.gender">
            <el-radio label="男">男</el-radio>
            <el-radio label="女">女</el-radio>
            <el-radio label="未知">未知</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="擅长项目" prop="specialties">
          <el-input
            v-model="form.specialties"
            placeholder="例如：篮球、羽毛球（多个用逗号分隔）"
          />
        </el-form-item>
        <el-form-item label="课时费" prop="hourly_rate">
          <el-input-number
            v-model="form.hourly_rate"
            :min="0"
            :precision="2"
            placeholder="元/小时"
          />
        </el-form-item>
        <el-form-item label="资质证书">
          <el-input
            v-model="form.certificates"
            type="textarea"
            :rows="3"
            placeholder="例如：国家一级篮球裁判员"
          />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-select v-model="form.status" style="width: 100%">
            <el-option label="在职" value="在职" />
            <el-option label="离职" value="离职" />
            <el-option label="休假" value="休假" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from "vue";
import { ElMessage, type FormInstance, type FormRules } from "element-plus";
import http from "@/utils/http";

interface Coach {
  id: number;
  name: string;
  phone?: string;
  gender?: string;
  specialties?: string;
  hourly_rate?: number;
  certificates?: string;
  status: string;
  remark?: string;
}

const loading = ref(false);
const coaches = ref<Coach[]>([]);
const total = ref(0);
const page = ref(1);
const pageSize = 20;

const filters = reactive({
  keyword: "",
  status: "",
  specialty: "",
});

const specialtyOptions = ref<string[]>([]);

const dialogVisible = ref(false);
const dialogTitle = ref("新增教练");
const submitLoading = ref(false);
const formRef = ref<FormInstance>();

const form = reactive({
  id: null as number | null,
  name: "",
  phone: "",
  gender: "男",
  specialties: "",
  hourly_rate: 0,
  certificates: "",
  status: "在职",
  remark: "",
});

const rules: FormRules = {
  name: [{ required: true, message: "请输入教练姓名", trigger: "blur" }],
};

const statusTag = (status: string) => {
  const map: Record<string, string> = {
    在职: "success",
    离职: "info",
    休假: "warning",
  };
  return map[status] || "info";
};

const loadCoaches = async () => {
  loading.value = true;
  try {
    const params: any = { page: page.value, page_size: pageSize };
    if (filters.keyword) params.keyword = filters.keyword;
    if (filters.status) params.status = filters.status;
    if (filters.specialty) params.specialty = filters.specialty;

    const res = await http.get("/training/coaches", { params });
    coaches.value = res.data?.items || [];
    total.value = res.data?.total || 0;
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "获取教练列表失败");
  } finally {
    loading.value = false;
  }
};

const loadSpecialties = async () => {
  try {
    const res = await http.get("/training/coaches/specialties/list");
    specialtyOptions.value = res.data || [];
  } catch (e) {
    // 忽略错误
  }
};

const onSearch = () => {
  page.value = 1;
  loadCoaches();
};

const resetFilters = () => {
  filters.keyword = "";
  filters.status = "";
  filters.specialty = "";
  onSearch();
};

const handlePageChange = (p: number) => {
  page.value = p;
  loadCoaches();
};

const handleAdd = () => {
  dialogTitle.value = "新增教练";
  dialogVisible.value = true;
};

const handleEdit = (row: Coach) => {
  dialogTitle.value = "编辑教练";
  form.id = row.id;
  form.name = row.name;
  form.phone = row.phone || "";
  form.gender = row.gender || "男";
  form.specialties = row.specialties || "";
  form.hourly_rate = row.hourly_rate || 0;
  form.certificates = row.certificates || "";
  form.status = row.status;
  form.remark = row.remark || "";
  dialogVisible.value = true;
};

const handleSubmit = async () => {
  if (!formRef.value) return;
  await formRef.value.validate(async (valid) => {
    if (!valid) return;

    submitLoading.value = true;
    try {
      const data = { ...form };
      if (form.id) {
        await http.put(`/training/coaches/${form.id}`, data);
        ElMessage.success("教练信息已更新");
      } else {
        await http.post("/training/coaches", data);
        ElMessage.success("教练创建成功");
      }
      dialogVisible.value = false;
      loadCoaches();
      loadSpecialties();
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.detail || "操作失败");
    } finally {
      submitLoading.value = false;
    }
  });
};

const handleDelete = async (id: number) => {
  try {
    await http.delete(`/training/coaches/${id}`);
    ElMessage.success("教练已删除");
    loadCoaches();
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "删除失败");
  }
};

const resetForm = () => {
  form.id = null;
  form.name = "";
  form.phone = "";
  form.gender = "男";
  form.specialties = "";
  form.hourly_rate = 0;
  form.certificates = "";
  form.status = "在职";
  form.remark = "";
  formRef.value?.clearValidate();
};

onMounted(() => {
  loadCoaches();
  loadSpecialties();
});
</script>

<style scoped>
.coaches-page {
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

.filter-card,
.table-card {
  border-radius: 12px;
  background: #fff;
  border: none;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.filters {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>





