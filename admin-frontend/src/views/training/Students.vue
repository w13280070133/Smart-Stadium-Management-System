<template>
  <div class="students-page">
    <div class="page-header">
      <div>
        <h2>学员管理</h2>
        <p class="sub-title">管理学员信息和报名记录</p>
      </div>
      <el-button type="primary" @click="handleAdd">新增学员</el-button>
    </div>

    <el-card shadow="hover" class="filter-card">
      <div class="filters">
        <el-input
          v-model="filters.keyword"
          placeholder="搜索姓名/电话/监护人"
          clearable
          style="width: 220px"
          @keyup.enter="onSearch"
        />
        <el-select v-model="filters.status" placeholder="状态" clearable style="width: 120px">
          <el-option label="全部" value="" />
          <el-option label="在读" value="在读" />
          <el-option label="毕业" value="毕业" />
          <el-option label="退学" value="退学" />
        </el-select>
        <el-button type="primary" @click="onSearch">查询</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </div>
    </el-card>

    <el-card shadow="hover" class="table-card">
      <el-table :data="students" border stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="phone" label="联系电话" width="130" />
        <el-table-column prop="gender" label="性别" width="70" />
        <el-table-column prop="birthday" label="出生日期" width="110" />
        <el-table-column prop="guardian_name" label="监护人" width="100" />
        <el-table-column prop="guardian_phone" label="监护人电话" width="130" />
        <el-table-column prop="active_enrollments" label="在读课程" width="90" align="center" />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === '在读' ? 'success' : 'info'">
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleView(row)">查看</el-button>
            <el-button link type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
            <el-popconfirm title="确定删除该学员吗？" @confirm="handleDelete(row.id)">
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
    <el-dialog :title="dialogTitle" v-model="dialogVisible" width="600px" @close="resetForm">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="姓名" prop="name">
          <el-input v-model="form.name" placeholder="请输入学员姓名" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="form.phone" placeholder="请输入联系电话" />
        </el-form-item>
        <el-form-item label="性别">
          <el-radio-group v-model="form.gender">
            <el-radio label="男">男</el-radio>
            <el-radio label="女">女</el-radio>
            <el-radio label="未知">未知</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="出生日期">
          <el-date-picker
            v-model="form.birthday"
            type="date"
            placeholder="选择日期"
            style="width: 100%"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="监护人姓名">
          <el-input v-model="form.guardian_name" placeholder="未成年人必填" />
        </el-form-item>
        <el-form-item label="监护人电话">
          <el-input v-model="form.guardian_phone" placeholder="监护人联系方式" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" style="width: 100%">
            <el-option label="在读" value="在读" />
            <el-option label="毕业" value="毕业" />
            <el-option label="退学" value="退学" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="如特殊需求、健康状况" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">保存</el-button>
      </template>
    </el-dialog>

    <!-- 查看详情对话框 -->
    <el-dialog title="学员详情" v-model="detailVisible" width="700px">
      <el-descriptions :column="2" border v-if="currentStudent">
        <el-descriptions-item label="姓名">{{ currentStudent.name }}</el-descriptions-item>
        <el-descriptions-item label="性别">{{ currentStudent.gender }}</el-descriptions-item>
        <el-descriptions-item label="联系电话">{{ currentStudent.phone || "-" }}</el-descriptions-item>
        <el-descriptions-item label="出生日期">{{ currentStudent.birthday || "-" }}</el-descriptions-item>
        <el-descriptions-item label="监护人">{{ currentStudent.guardian_name || "-" }}</el-descriptions-item>
        <el-descriptions-item label="监护人电话">{{ currentStudent.guardian_phone || "-" }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="currentStudent.status === '在读' ? 'success' : 'info'">
            {{ currentStudent.status }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ currentStudent.remark || "-" }}</el-descriptions-item>
      </el-descriptions>

      <h4 style="margin-top: 20px">报名记录</h4>
      <el-table :data="currentStudent?.enrollments || []" border stripe size="small">
        <el-table-column prop="course_name" label="课程名称" />
        <el-table-column prop="course_type" label="类型" width="100" />
        <el-table-column label="课时" width="150">
          <template #default="{ row }">
            剩余 {{ row.remaining_lessons }} / 总 {{ row.total_lessons }}
          </template>
        </el-table-column>
        <el-table-column prop="paid_amount" label="金额" width="100">
          <template #default="{ row }">¥{{ row.paid_amount }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === '在读' ? 'success' : 'info'">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from "vue";
import { ElMessage, type FormInstance, type FormRules } from "element-plus";
import http from "@/utils/http";

const loading = ref(false);
const students = ref<any[]>([]);
const total = ref(0);
const page = ref(1);
const pageSize = 20;

const filters = reactive({
  keyword: "",
  status: "",
});

const dialogVisible = ref(false);
const dialogTitle = ref("新增学员");
const submitLoading = ref(false);
const formRef = ref<FormInstance>();

const form = reactive({
  id: null as number | null,
  name: "",
  phone: "",
  gender: "男",
  birthday: "",
  guardian_name: "",
  guardian_phone: "",
  status: "在读",
  remark: "",
});

const rules: FormRules = {
  name: [{ required: true, message: "请输入学员姓名", trigger: "blur" }],
};

const detailVisible = ref(false);
const currentStudent = ref<any>(null);

const loadStudents = async () => {
  loading.value = true;
  try {
    const params: any = { page: page.value, page_size: pageSize };
    if (filters.keyword) params.keyword = filters.keyword;
    if (filters.status) params.status = filters.status;

    const res = await http.get("/training/students", { params });
    students.value = res.data?.items || [];
    total.value = res.data?.total || 0;
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "获取学员列表失败");
  } finally {
    loading.value = false;
  }
};

const onSearch = () => {
  page.value = 1;
  loadStudents();
};

const resetFilters = () => {
  filters.keyword = "";
  filters.status = "";
  onSearch();
};

const handlePageChange = (p: number) => {
  page.value = p;
  loadStudents();
};

const handleAdd = () => {
  dialogTitle.value = "新增学员";
  dialogVisible.value = true;
};

const handleEdit = (row: any) => {
  dialogTitle.value = "编辑学员";
  Object.assign(form, {
    id: row.id,
    name: row.name,
    phone: row.phone || "",
    gender: row.gender || "男",
    birthday: row.birthday || "",
    guardian_name: row.guardian_name || "",
    guardian_phone: row.guardian_phone || "",
    status: row.status,
    remark: row.remark || "",
  });
  dialogVisible.value = true;
};

const handleView = async (row: any) => {
  try {
    const res = await http.get(`/training/students/${row.id}`);
    currentStudent.value = res.data;
    detailVisible.value = true;
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "获取学员详情失败");
  }
};

const handleSubmit = async () => {
  if (!formRef.value) return;
  await formRef.value.validate(async (valid) => {
    if (!valid) return;

    submitLoading.value = true;
    try {
      const data = { ...form };
      if (form.id) {
        await http.put(`/training/students/${form.id}`, data);
        ElMessage.success("学员信息已更新");
      } else {
        await http.post("/training/students", data);
        ElMessage.success("学员创建成功");
      }
      dialogVisible.value = false;
      loadStudents();
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.detail || "操作失败");
    } finally {
      submitLoading.value = false;
    }
  });
};

const handleDelete = async (id: number) => {
  try {
    await http.delete(`/training/students/${id}`);
    ElMessage.success("学员已删除");
    loadStudents();
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "删除失败");
  }
};

const resetForm = () => {
  Object.assign(form, {
    id: null,
    name: "",
    phone: "",
    gender: "男",
    birthday: "",
    guardian_name: "",
    guardian_phone: "",
    status: "在读",
    remark: "",
  });
  formRef.value?.clearValidate();
};

onMounted(() => {
  loadStudents();
});
</script>

<style scoped>
.students-page {
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

.filter-card,
.table-card {
  border-radius: 12px;
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


