<template>
  <div class="courses-page">
    <div class="page-header">
      <div>
        <h2>课程管理</h2>
        <p class="sub-title">管理课程信息、报名学员和排期安排</p>
      </div>
      <el-button type="primary" @click="handleAdd">新建课程</el-button>
    </div>

    <el-card shadow="hover" class="filter-card">
      <div class="filters">
        <el-input v-model="filters.keyword" placeholder="搜索课程名称" clearable style="width: 200px" @keyup.enter="onSearch" />
        <el-select v-model="filters.type" placeholder="课程类型" clearable style="width: 140px" allow-create filterable>
          <el-option v-for="t in courseTypes" :key="t" :label="t" :value="t" />
        </el-select>
        <el-select v-model="filters.status" placeholder="状态" clearable style="width: 120px">
          <el-option label="全部" value="" />
          <el-option label="草稿" value="草稿" />
          <el-option label="招生中" value="招生中" />
          <el-option label="进行中" value="进行中" />
          <el-option label="已结束" value="已结束" />
        </el-select>
        <el-button type="primary" @click="onSearch">查询</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </div>
    </el-card>

    <el-card shadow="hover" class="table-card">
      <el-table :data="courses" border stripe v-loading="loading">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="课程名称" min-width="150" />
        <el-table-column prop="type" label="类型" width="100" />
        <el-table-column prop="coach_name" label="教练" width="100" />
        <el-table-column label="课时/价格" width="120">
          <template #default="{ row }">
            {{ row.total_lessons }}节 / ¥{{ row.price }}
          </template>
        </el-table-column>
        <el-table-column label="在读学员" width="90" align="center">
          <template #default="{ row }">
            <span style="color: #409eff; font-weight: 600">{{ row.active_students }}</span> / {{ row.max_students }}
          </template>
        </el-table-column>
        <el-table-column prop="total_revenue" label="总收入" width="100">
          <template #default="{ row }">¥{{ row.total_revenue || 0 }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="statusTag(row.status)">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleView(row)">详情</el-button>
            <el-button link type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
            <el-popconfirm title="确定删除该课程吗？" @confirm="handleDelete(row.id)">
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
    <el-dialog :title="dialogTitle" v-model="dialogVisible" width="650px" @close="resetForm">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="课程名称" prop="name">
          <el-input v-model="form.name" placeholder="例如：少儿篮球基础班" />
        </el-form-item>
        <el-form-item label="课程类型" prop="type">
          <el-select v-model="form.type" placeholder="选择或输入类型" filterable allow-create style="width: 100%">
            <el-option v-for="t in courseTypes" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="默认教练">
          <el-select v-model="form.coach_id" placeholder="选择教练" clearable filterable style="width: 100%">
            <el-option v-for="coach in coaches" :key="coach.id" :label="coach.name" :value="coach.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="总课时" prop="total_lessons">
          <el-input-number v-model="form.total_lessons" :min="1" :max="200" style="width: 100%" />
        </el-form-item>
        <el-form-item label="总价" prop="price">
          <el-input-number v-model="form.price" :min="0" :precision="2" style="width: 100%" />
        </el-form-item>
        <el-form-item label="最大学员数">
          <el-input-number v-model="form.max_students" :min="1" :max="100" style="width: 100%" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="form.status" style="width: 100%">
            <el-option label="草稿" value="草稿" />
            <el-option label="招生中" value="招生中" />
            <el-option label="进行中" value="进行中" />
            <el-option label="已结束" value="已结束" />
          </el-select>
        </el-form-item>
        <el-form-item label="课程描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="课程简介、适合人群等" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">保存</el-button>
      </template>
    </el-dialog>

    <!-- 课程详情对话框 -->
    <el-dialog title="课程详情" v-model="detailVisible" width="900px">
      <el-tabs v-if="currentCourse">
        <el-tab-pane label="基本信息">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="课程名称">{{ currentCourse.name }}</el-descriptions-item>
            <el-descriptions-item label="类型">{{ currentCourse.type || "-" }}</el-descriptions-item>
            <el-descriptions-item label="教练">{{ currentCourse.coach_name || "-" }}</el-descriptions-item>
            <el-descriptions-item label="总课时">{{ currentCourse.total_lessons }}节</el-descriptions-item>
            <el-descriptions-item label="总价">¥{{ currentCourse.price }}</el-descriptions-item>
            <el-descriptions-item label="最大学员">{{ currentCourse.max_students }}人</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="statusTag(currentCourse.status)">{{ currentCourse.status }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="统计信息">
              在读 {{ currentCourse.stats?.active_enrollments || 0 }} 人 / 总收入 ¥{{ currentCourse.stats?.total_revenue || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="课程描述" :span="2">{{ currentCourse.description || "-" }}</el-descriptions-item>
          </el-descriptions>
        </el-tab-pane>
        <el-tab-pane label="报名学员">
          <el-table :data="currentCourse.enrollments || []" border stripe size="small">
            <el-table-column prop="student_name" label="学员姓名" width="100" />
            <el-table-column prop="student_phone" label="联系电话" width="130" />
            <el-table-column label="课时" width="150">
              <template #default="{ row }">
                剩余 <span style="color: #f56c6c; font-weight: 600">{{ row.remaining_lessons }}</span> / 总 {{ row.total_lessons }}
              </template>
            </el-table-column>
            <el-table-column prop="paid_amount" label="金额" width="100">
              <template #default="{ row }">¥{{ row.paid_amount }}</template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="90">
              <el-tag :type="row.status === '在读' ? 'success' : 'info'" size="small">{{ row.status }}</el-tag>
            </el-table-column>
            <el-table-column prop="enrolled_at" label="报名时间" width="160" />
          </el-table>
        </el-tab-pane>
        <el-tab-pane label="排期列表">
          <div style="margin-bottom: 12px;">
            <el-button type="primary" size="small" @click="showAddScheduleDialog = true">新增排期</el-button>
          </div>
          <el-table :data="currentCourse.schedules || []" border stripe size="small">
            <el-table-column prop="date" label="日期" width="110" />
            <el-table-column label="时间" width="150">
              <template #default="{ row }">{{ row.start_time }} ~ {{ row.end_time }}</template>
            </el-table-column>
            <el-table-column prop="venue" label="地点" width="120" />
            <el-table-column prop="coach_name" label="教练" width="100" />
            <el-table-column prop="status" label="状态" width="90">
              <template #default="{ row }">
                <el-tag :type="row.status === '正常' ? 'success' : 'info'" size="small">{{ row.status }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80">
              <template #default="{ row }">
                <el-button link type="danger" size="small" @click="deleteSchedule(row.id)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </el-dialog>

    <!-- 新增排期对话框 -->
    <el-dialog v-model="showAddScheduleDialog" title="新增排期" width="480px">
      <el-form :model="scheduleForm" label-width="80px">
        <el-form-item label="日期" required>
          <el-date-picker
            v-model="scheduleForm.date"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="开始时间" required>
          <el-time-picker
            v-model="scheduleForm.start_time"
            placeholder="开始时间"
            format="HH:mm"
            value-format="HH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="结束时间" required>
          <el-time-picker
            v-model="scheduleForm.end_time"
            placeholder="结束时间"
            format="HH:mm"
            value-format="HH:mm:ss"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="地点">
          <el-input v-model="scheduleForm.venue" placeholder="如：1号教室" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="scheduleForm.remark" type="textarea" :rows="2" placeholder="选填" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddScheduleDialog = false">取消</el-button>
        <el-button type="primary" @click="submitSchedule" :loading="scheduleLoading">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from "vue";
import { ElMessage, type FormInstance, type FormRules } from "element-plus";
import http from "@/utils/http";

const loading = ref(false);
const courses = ref<any[]>([]);
const total = ref(0);
const page = ref(1);
const pageSize = 20;

const filters = reactive({
  keyword: "",
  type: "",
  status: "",
});

const courseTypes = ref<string[]>([]);
const coaches = ref<any[]>([]);

const dialogVisible = ref(false);

// 排期相关
const showAddScheduleDialog = ref(false);
const scheduleLoading = ref(false);
const scheduleForm = reactive({
  date: "",
  start_time: "",
  end_time: "",
  venue: "",
  remark: "",
});
const dialogTitle = ref("新建课程");
const submitLoading = ref(false);
const formRef = ref<FormInstance>();

const form = reactive({
  id: null as number | null,
  name: "",
  type: "",
  description: "",
  coach_id: null as number | null,
  total_lessons: 12,
  price: 0,
  max_students: 20,
  status: "招生中",
  remark: "",
});

const rules: FormRules = {
  name: [{ required: true, message: "请输入课程名称", trigger: "blur" }],
  total_lessons: [{ required: true, message: "请输入总课时", trigger: "blur" }],
  price: [{ required: true, message: "请输入总价", trigger: "blur" }],
};

const detailVisible = ref(false);
const currentCourse = ref<any>(null);

const statusTag = (status: string) => {
  const map: Record<string, string> = {
    草稿: "info",
    招生中: "success",
    进行中: "warning",
    已结束: "info",
  };
  return map[status] || "info";
};

const loadCourses = async () => {
  loading.value = true;
  try {
    const params: any = { page: page.value, page_size: pageSize };
    if (filters.keyword) params.keyword = filters.keyword;
    if (filters.type) params.type = filters.type;
    if (filters.status) params.status = filters.status;

    const res = await http.get("/training/courses", { params });
    courses.value = res.data?.items || [];
    total.value = res.data?.total || 0;
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "获取课程列表失败");
  } finally {
    loading.value = false;
  }
};

const loadCourseTypes = async () => {
  try {
    const res = await http.get("/training/courses/types/list");
    courseTypes.value = res.data || [];
  } catch (e) {}
};

const loadCoaches = async () => {
  try {
    const res = await http.get("/training/coaches", { params: { page: 1, page_size: 100, status: "在职" } });
    coaches.value = res.data?.items || [];
  } catch (e) {}
};

const onSearch = () => {
  page.value = 1;
  loadCourses();
};

const resetFilters = () => {
  Object.assign(filters, { keyword: "", type: "", status: "" });
  onSearch();
};

const handlePageChange = (p: number) => {
  page.value = p;
  loadCourses();
};

const handleAdd = () => {
  dialogTitle.value = "新建课程";
  dialogVisible.value = true;
};

const handleEdit = (row: any) => {
  dialogTitle.value = "编辑课程";
  Object.assign(form, {
    id: row.id,
    name: row.name,
    type: row.type || "",
    description: row.description || "",
    coach_id: row.coach_id,
    total_lessons: row.total_lessons,
    price: row.price,
    max_students: row.max_students,
    status: row.status,
    remark: row.remark || "",
  });
  dialogVisible.value = true;
};

const handleView = async (row: any) => {
  try {
    const res = await http.get(`/training/courses/${row.id}`);
    currentCourse.value = res.data;
    detailVisible.value = true;
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "获取课程详情失败");
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
        await http.put(`/training/courses/${form.id}`, data);
        ElMessage.success("课程信息已更新");
      } else {
        await http.post("/training/courses", data);
        ElMessage.success("课程创建成功");
      }
      dialogVisible.value = false;
      loadCourses();
      loadCourseTypes();
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.detail || "操作失败");
    } finally {
      submitLoading.value = false;
    }
  });
};

const handleDelete = async (id: number) => {
  try {
    await http.delete(`/training/courses/${id}`);
    ElMessage.success("课程已删除");
    loadCourses();
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "删除失败");
  }
};

const resetForm = () => {
  Object.assign(form, {
    id: null,
    name: "",
    type: "",
    description: "",
    coach_id: null,
    total_lessons: 12,
    price: 0,
    max_students: 20,
    status: "招生中",
    remark: "",
  });
  formRef.value?.clearValidate();
};

// 提交新增排期
async function submitSchedule() {
  if (!scheduleForm.date || !scheduleForm.start_time || !scheduleForm.end_time) {
    ElMessage.warning("请填写日期和时间");
    return;
  }
  if (!currentCourse.value?.id) {
    ElMessage.warning("课程信息错误");
    return;
  }

  scheduleLoading.value = true;
  try {
    await http.post("/training/schedules", {
      course_id: currentCourse.value.id,
      date: scheduleForm.date,
      start_time: scheduleForm.start_time,
      end_time: scheduleForm.end_time,
      venue: scheduleForm.venue || undefined,
      remark: scheduleForm.remark || undefined,
    });
    ElMessage.success("排期添加成功");
    showAddScheduleDialog.value = false;
    // 重置表单
    scheduleForm.date = "";
    scheduleForm.start_time = "";
    scheduleForm.end_time = "";
    scheduleForm.venue = "";
    scheduleForm.remark = "";
    // 刷新课程详情
    await handleView(currentCourse.value);
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "添加排期失败");
  } finally {
    scheduleLoading.value = false;
  }
}

// 删除排期
async function deleteSchedule(scheduleId: number) {
  try {
    await http.delete(`/training/schedules/${scheduleId}`);
    ElMessage.success("排期已删除");
    // 刷新课程详情
    if (currentCourse.value?.id) {
      await handleView(currentCourse.value);
    }
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "删除排期失败");
  }
}

onMounted(() => {
  loadCourses();
  loadCourseTypes();
  loadCoaches();
});
</script>

<style scoped>
.courses-page {
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

