<template>
  <div class="enrollments-page">
    <div class="page-header">
      <div>
        <h2>报名管理</h2>
        <p class="sub-title">学员报名、退费和课时管理</p>
      </div>
      <el-button type="primary" @click="handleAdd">新增报名</el-button>
    </div>

    <el-card shadow="hover" class="filter-card">
      <div class="filters">
        <el-input v-model="filters.keyword" placeholder="搜索学员/课程" clearable style="width: 200px" @keyup.enter="onSearch" />
        <el-select v-model="filters.status" placeholder="状态" clearable style="width: 120px">
          <el-option label="全部" value="" />
          <el-option label="在读" value="在读" />
          <el-option label="退费" value="退费" />
          <el-option label="结业" value="结业" />
        </el-select>
        <el-button type="primary" @click="onSearch">查询</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </div>
    </el-card>

    <el-card shadow="hover" class="table-card">
      <el-table :data="enrollments" border stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="student_name" label="学员姓名" width="100" />
        <el-table-column prop="student_phone" label="联系电话" width="130" />
        <el-table-column prop="course_name" label="课程名称" min-width="150" />
        <el-table-column prop="course_type" label="类型" width="100" />
        <el-table-column label="课时" width="150">
          <template #default="{ row }">
            <span :style="{ color: row.remaining_lessons < 3 ? '#f56c6c' : '#409eff', fontWeight: 600 }">
              {{ row.remaining_lessons }}
            </span>
            / {{ row.total_lessons }}
          </template>
        </el-table-column>
        <el-table-column prop="paid_amount" label="金额" width="100">
          <template #default="{ row }">¥{{ row.paid_amount }}</template>
        </el-table-column>
        <el-table-column prop="attendance_count" label="已上" width="80" align="center" />
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === '在读' ? 'success' : 'info'">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleView(row)">详情</el-button>
            <el-button link type="warning" size="small" @click="handleRefund(row)" v-if="row.status === '在读'">退费</el-button>
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

    <!-- 新增报名对话框 -->
    <el-dialog title="新增报名" v-model="dialogVisible" width="550px" @close="resetForm">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="选择学员" prop="student_id">
          <el-select v-model="form.student_id" placeholder="选择学员" filterable style="width: 100%">
            <el-option v-for="s in students" :key="s.id" :label="`${s.name} (${s.phone})`" :value="s.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="选择课程" prop="course_id">
          <el-select v-model="form.course_id" placeholder="选择课程" filterable style="width: 100%" @change="handleCourseChange">
            <el-option v-for="c in courses" :key="c.id" :label="`${c.name} (${c.type})`" :value="c.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="购买课时" prop="total_lessons">
          <el-input-number v-model="form.total_lessons" :min="1" :max="200" style="width: 100%" />
        </el-form-item>
        <el-form-item label="实付金额" prop="paid_amount">
          <el-input-number v-model="form.paid_amount" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">确认报名</el-button>
      </template>
    </el-dialog>

    <!-- 详情对话框 -->
    <el-dialog title="报名详情" v-model="detailVisible" width="700px">
      <el-descriptions :column="2" border v-if="currentEnrollment">
        <el-descriptions-item label="学员姓名">{{ currentEnrollment.student_name }}</el-descriptions-item>
        <el-descriptions-item label="联系电话">{{ currentEnrollment.student_phone }}</el-descriptions-item>
        <el-descriptions-item label="课程名称">{{ currentEnrollment.course_name }}</el-descriptions-item>
        <el-descriptions-item label="课程类型">{{ currentEnrollment.course_type }}</el-descriptions-item>
        <el-descriptions-item label="总课时">{{ currentEnrollment.total_lessons }}节</el-descriptions-item>
        <el-descriptions-item label="剩余课时">
          <span style="color: #f56c6c; font-weight: 600">{{ currentEnrollment.remaining_lessons }}</span>节
        </el-descriptions-item>
        <el-descriptions-item label="实付金额">¥{{ currentEnrollment.paid_amount }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="currentEnrollment.status === '在读' ? 'success' : 'info'">{{ currentEnrollment.status }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="报名时间" :span="2">{{ currentEnrollment.enrolled_at }}</el-descriptions-item>
      </el-descriptions>

      <h4 style="margin-top: 20px">签到记录</h4>
      <el-table :data="currentEnrollment?.attendances || []" border stripe size="small">
        <el-table-column prop="date" label="日期" width="110" />
        <el-table-column label="时间" width="150">
          <template #default="{ row }">{{ row.start_time }} ~ {{ row.end_time }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === '已签到' ? 'success' : 'warning'" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="lessons_deducted" label="扣课时" width="80" align="center" />
        <el-table-column prop="attended_at" label="签到时间" width="160" />
      </el-table>
    </el-dialog>

    <!-- 退费对话框 -->
    <el-dialog title="退费确认" v-model="refundVisible" width="500px">
      <el-alert type="warning" :closable="false" style="margin-bottom: 16px">
        <template #title>
          <div>退费后学员将无法继续上课，请谨慎操作！</div>
        </template>
      </el-alert>
      <div v-if="refundEnrollment" style="padding: 16px; background: #f5f7fa; border-radius: 8px; margin-bottom: 16px">
        <p><strong>学员：</strong>{{ refundEnrollment.student_name }}</p>
        <p><strong>课程：</strong>{{ refundEnrollment.course_name }}</p>
        <p><strong>剩余课时：</strong>{{ refundEnrollment.remaining_lessons }} / {{ refundEnrollment.total_lessons }}</p>
        <p><strong>预计退款：</strong>¥{{ calculateRefund(refundEnrollment) }}</p>
      </div>
      <el-input v-model="refundRemark" type="textarea" :rows="3" placeholder="退费原因（选填）" />
      <template #footer>
        <el-button @click="refundVisible = false">取消</el-button>
        <el-button type="danger" @click="confirmRefund" :loading="refundLoading">确认退费</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from "vue";
import { ElMessage, type FormInstance, type FormRules } from "element-plus";
import http from "@/utils/http";

const loading = ref(false);
const enrollments = ref<any[]>([]);
const total = ref(0);
const page = ref(1);
const pageSize = 20;

const filters = reactive({
  keyword: "",
  status: "",
});

const students = ref<any[]>([]);
const courses = ref<any[]>([]);

const dialogVisible = ref(false);
const submitLoading = ref(false);
const formRef = ref<FormInstance>();

const form = reactive({
  student_id: null as number | null,
  course_id: null as number | null,
  total_lessons: 12,
  paid_amount: 0,
  remark: "",
});

const rules: FormRules = {
  student_id: [{ required: true, message: "请选择学员", trigger: "change" }],
  course_id: [{ required: true, message: "请选择课程", trigger: "change" }],
  total_lessons: [{ required: true, message: "请输入课时", trigger: "blur" }],
  paid_amount: [{ required: true, message: "请输入金额", trigger: "blur" }],
};

const detailVisible = ref(false);
const currentEnrollment = ref<any>(null);

const refundVisible = ref(false);
const refundEnrollment = ref<any>(null);
const refundRemark = ref("");
const refundLoading = ref(false);

const loadEnrollments = async () => {
  loading.value = true;
  try {
    const params: any = { page: page.value, page_size: pageSize };
    if (filters.keyword) params.keyword = filters.keyword;
    if (filters.status) params.status = filters.status;

    const res = await http.get("/training/enrollments", { params });
    enrollments.value = res.data?.items || [];
    total.value = res.data?.total || 0;
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "获取报名列表失败");
  } finally {
    loading.value = false;
  }
};

const loadStudents = async () => {
  try {
    const res = await http.get("/training/students", { params: { page: 1, page_size: 100, status: "在读" } });
    students.value = res.data?.items || [];
  } catch (e) {}
};

const loadCourses = async () => {
  try {
    const res = await http.get("/training/courses", { params: { page: 1, page_size: 100, status: "招生中" } });
    courses.value = res.data?.items || [];
  } catch (e) {}
};

const onSearch = () => {
  page.value = 1;
  loadEnrollments();
};

const resetFilters = () => {
  Object.assign(filters, { keyword: "", status: "" });
  onSearch();
};

const handlePageChange = (p: number) => {
  page.value = p;
  loadEnrollments();
};

const handleAdd = () => {
  dialogVisible.value = true;
};

const handleCourseChange = (courseId: number) => {
  const course = courses.value.find((c) => c.id === courseId);
  if (course) {
    form.total_lessons = course.total_lessons || 12;
    form.paid_amount = course.price || 0;
  }
};

const handleSubmit = async () => {
  if (!formRef.value) return;
  await formRef.value.validate(async (valid) => {
    if (!valid) return;

    submitLoading.value = true;
    try {
      await http.post("/training/enrollments", form);
      ElMessage.success("报名成功");
      dialogVisible.value = false;
      loadEnrollments();
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.detail || "报名失败");
    } finally {
      submitLoading.value = false;
    }
  });
};

const handleView = async (row: any) => {
  try {
    const res = await http.get(`/training/enrollments/${row.id}`);
    currentEnrollment.value = res.data;
    detailVisible.value = true;
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "获取详情失败");
  }
};

const handleRefund = (row: any) => {
  refundEnrollment.value = row;
  refundVisible.value = true;
};

const calculateRefund = (enrollment: any) => {
  if (!enrollment) return 0;
  const { paid_amount, total_lessons, remaining_lessons } = enrollment;
  return ((paid_amount / total_lessons) * remaining_lessons).toFixed(2);
};

const confirmRefund = async () => {
  if (!refundEnrollment.value) return;

  refundLoading.value = true;
  try {
    await http.post(`/training/enrollments/${refundEnrollment.value.id}/refund`, {
      remark: refundRemark.value,
    });
    ElMessage.success("退费成功");
    refundVisible.value = false;
    loadEnrollments();
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "退费失败");
  } finally {
    refundLoading.value = false;
  }
};

const resetForm = () => {
  Object.assign(form, {
    student_id: null,
    course_id: null,
    total_lessons: 12,
    paid_amount: 0,
    remark: "",
  });
  formRef.value?.clearValidate();
};

onMounted(() => {
  loadEnrollments();
  loadStudents();
  loadCourses();
});
</script>

<style scoped>
.enrollments-page {
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


