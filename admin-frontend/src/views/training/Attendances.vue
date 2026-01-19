<template>
  <div class="attendances-page">
    <el-card shadow="hover" class="filter-card">
      <template #header>
        <div class="card-header">
          <span>签到管理</span>
          <el-button type="primary" @click="showAttendanceDialog = true">快速签到</el-button>
        </div>
      </template>

      <el-form :inline="true" class="filter-form">
        <el-form-item label="学员">
          <el-select v-model="filters.student_id" placeholder="选择学员" clearable filterable style="width: 200px">
            <el-option v-for="item in students" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="课程">
          <el-select v-model="filters.course_id" placeholder="选择课程" clearable filterable style="width: 200px">
            <el-option v-for="item in courses" :key="item.id" :label="item.name" :value="item.id" />
          </el-select>
        </el-form-item>

        <el-form-item label="日期范围">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 240px"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="loadAttendances">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card shadow="hover" class="table-card" style="margin-top: 16px">
      <el-table :data="attendances" v-loading="loading" stripe style="width: 100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="student_name" label="学员姓名" width="120" />
        <el-table-column prop="student_phone" label="联系方式" width="120" />
        <el-table-column prop="course_name" label="课程名称" width="150" />
        <el-table-column prop="course_type" label="课程类型" width="100" />
        <el-table-column label="上课时间" width="180">
          <template #default="{ row }">
            {{ row.schedule_date }} {{ String(row.start_time || '').substring(0, 5) }}-{{ String(row.end_time || '').substring(0, 5) }}
          </template>
        </el-table-column>
        <el-table-column prop="attended_at" label="签到时间" width="160" />
        <el-table-column label="剩余课时" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.remaining_lessons > 5 ? 'success' : row.remaining_lessons > 0 ? 'warning' : 'danger'">
              {{ row.remaining_lessons }} 节
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-tag type="success" size="small">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="120" show-overflow-tooltip />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="viewDetail(row)">详情</el-button>
            <el-button link type="warning" size="small" @click="editRemark(row)">备注</el-button>
            <el-popconfirm
              title="确定撤销此签到记录吗？课时将会恢复。"
              confirm-button-text="确定撤销"
              cancel-button-text="取消"
              @confirm="deleteAttendance(row.id)"
            >
              <template #reference>
                <el-button link type="danger" size="small">撤销</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.page_size"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="loadAttendances"
        @current-change="loadAttendances"
        style="margin-top: 16px; justify-content: flex-end"
      />
    </el-card>

    <!-- 快速签到对话框 -->
    <el-dialog v-model="showAttendanceDialog" title="快速签到" width="500px">
      <el-form :model="attendanceForm" label-width="100px">
        <el-form-item label="选择学员" required>
          <el-select
            v-model="attendanceForm.enrollment_id"
            placeholder="选择报名记录"
            filterable
            style="width: 100%"
            @change="onEnrollmentChange"
          >
            <el-option
              v-for="item in enrollments"
              :key="item.id"
              :label="`${item.student_name} - ${item.course_name} (剩余${item.remaining_lessons}节)`"
              :value="item.id"
              :disabled="item.status !== '在读' || item.remaining_lessons <= 0"
            />
          </el-select>
          <div style="margin-top: 8px; font-size: 12px; color: #909399">
            只显示"在读"且有剩余课时的报名
          </div>
        </el-form-item>

        <el-form-item label="选择排期" required>
          <el-select
            v-model="attendanceForm.schedule_id"
            placeholder="选择上课时间"
            filterable
            style="width: 100%"
            :disabled="!selectedEnrollment"
          >
            <el-option
              v-for="item in schedules"
              :key="item.id"
              :label="`${item.date} ${String(item.start_time || '').substring(0, 5)}-${String(item.end_time || '').substring(0, 5)}`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="备注">
          <el-input v-model="attendanceForm.remark" type="textarea" :rows="3" placeholder="选填，如：按时到课" />
        </el-form-item>

        <el-alert
          v-if="selectedEnrollment"
          :title="`当前剩余课时：${selectedEnrollment.remaining_lessons} 节`"
          type="info"
          :closable="false"
          style="margin-bottom: 16px"
        />
      </el-form>

      <template #footer>
        <el-button @click="showAttendanceDialog = false">取消</el-button>
        <el-button
          type="primary"
          @click="createAttendance"
          :disabled="!attendanceForm.enrollment_id || !attendanceForm.schedule_id"
        >
          确认签到
        </el-button>
      </template>
    </el-dialog>

    <!-- 详情对话框 -->
    <el-dialog v-model="showDetailDialog" title="签到详情" width="600px">
      <el-descriptions v-if="currentAttendance" :column="2" border>
        <el-descriptions-item label="签到ID">{{ currentAttendance.id }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag type="success">{{ currentAttendance.status }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="学员姓名">{{ currentAttendance.student_name }}</el-descriptions-item>
        <el-descriptions-item label="联系方式">{{ currentAttendance.student_phone }}</el-descriptions-item>
        <el-descriptions-item label="课程名称">{{ currentAttendance.course_name }}</el-descriptions-item>
        <el-descriptions-item label="课程类型">{{ currentAttendance.course_type }}</el-descriptions-item>
        <el-descriptions-item label="上课日期">{{ currentAttendance.schedule_date }}</el-descriptions-item>
        <el-descriptions-item label="上课时间">
          {{ currentAttendance.start_time?.substring(0, 5) }} - {{ currentAttendance.end_time?.substring(0, 5) }}
        </el-descriptions-item>
        <el-descriptions-item label="签到时间" :span="2">{{ currentAttendance.attended_at }}</el-descriptions-item>
        <el-descriptions-item label="剩余课时">
          <el-tag
            :type="
              currentAttendance.remaining_lessons > 5
                ? 'success'
                : currentAttendance.remaining_lessons > 0
                ? 'warning'
                : 'danger'
            "
          >
            {{ currentAttendance.remaining_lessons }} / {{ currentAttendance.total_lessons }} 节
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">
          {{ currentAttendance.remark || "无" }}
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <!-- 编辑备注对话框 -->
    <el-dialog v-model="showRemarkDialog" title="编辑备注" width="500px">
      <el-input v-model="remarkForm.remark" type="textarea" :rows="4" placeholder="请输入备注" />
      <template #footer>
        <el-button @click="showRemarkDialog = false">取消</el-button>
        <el-button type="primary" @click="updateRemark">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from "vue";
import { ElMessage } from "element-plus";
import http from "../../utils/http";

interface Attendance {
  id: number;
  enrollment_id: number;
  schedule_id: number;
  attended_at: string;
  status: string;
  student_name: string;
  student_phone: string;
  course_name: string;
  course_type: string;
  remaining_lessons: number;
  total_lessons?: number;
  schedule_date: string;
  start_time: string;
  end_time: string;
  remark?: string;
}

interface Student {
  id: number;
  name: string;
  phone: string;
}

interface Course {
  id: number;
  name: string;
  type: string;
}

interface Enrollment {
  id: number;
  student_id: number;
  student_name: string;
  course_id: number;
  course_name: string;
  remaining_lessons: number;
  total_lessons: number;
  status: string;
}

interface Schedule {
  id: number;
  course_id: number;
  date: string;
  start_time: string;
  end_time: string;
}

const loading = ref(false);
const attendances = ref<Attendance[]>([]);
const students = ref<Student[]>([]);
const courses = ref<Course[]>([]);
const enrollments = ref<Enrollment[]>([]);
const schedules = ref<Schedule[]>([]);

const filters = reactive({
  student_id: undefined as number | undefined,
  course_id: undefined as number | undefined,
});

const dateRange = ref<string[]>([]);

const pagination = reactive({
  page: 1,
  page_size: 20,
  total: 0,
});

const showAttendanceDialog = ref(false);
const showDetailDialog = ref(false);
const showRemarkDialog = ref(false);
const currentAttendance = ref<Attendance | null>(null);

const attendanceForm = reactive({
  enrollment_id: undefined as number | undefined,
  schedule_id: undefined as number | undefined,
  remark: "",
});

const remarkForm = reactive({
  id: 0,
  remark: "",
});

const selectedEnrollment = computed(() => {
  return enrollments.value.find((e) => e.id == attendanceForm.enrollment_id);
});

async function loadAttendances() {
  loading.value = true;
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.page_size,
    };

    if (filters.student_id) params.student_id = filters.student_id;
    if (dateRange.value && dateRange.value.length === 2) {
      params.date_from = dateRange.value[0];
      params.date_to = dateRange.value[1];
    }

    const res = await http.get("/training/attendances", { params });
    attendances.value = res.data.items || [];
    pagination.total = res.data.total || 0;
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "加载签到记录失败");
  } finally {
    loading.value = false;
  }
}

async function loadStudents() {
  try {
    const res = await http.get("/training/students", { params: { page_size: 100 } });
    students.value = res.data.items || [];
  } catch (e) {
    console.error("加载学员列表失败", e);
  }
}

async function loadCourses() {
  try {
    const res = await http.get("/training/courses", { params: { page_size: 100 } });
    courses.value = res.data.items || [];
  } catch (e) {
    console.error("加载课程列表失败", e);
  }
}

async function loadEnrollments() {
  try {
    const res = await http.get("/training/enrollments", { params: { page_size: 100, status: "在读" } });
    enrollments.value = res.data.items || [];
  } catch (e) {
    console.error("加载报名列表失败", e);
  }
}

async function onEnrollmentChange() {
  attendanceForm.schedule_id = undefined;
  schedules.value = [];

  if (!selectedEnrollment.value) return;

  try {
    const res = await http.get("/training/schedules", {
      params: { course_id: selectedEnrollment.value.course_id, page_size: 100 },
    });
    schedules.value = res.data.items || [];
  } catch (e) {
    console.error("加载排期失败", e);
  }
}

async function createAttendance() {
  try {
    const res = await http.post("/training/attendances", {
      enrollment_id: attendanceForm.enrollment_id,
      schedule_id: attendanceForm.schedule_id,
      remark: attendanceForm.remark || undefined,
    });

    ElMessage.success(res.data.message || "签到成功");
    showAttendanceDialog.value = false;

    attendanceForm.enrollment_id = undefined;
    attendanceForm.schedule_id = undefined;
    attendanceForm.remark = "";

    loadAttendances();
    loadEnrollments();
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "签到失败");
  }
}

async function deleteAttendance(id: number) {
  try {
    await http.delete(`/training/attendances/${id}`);
    ElMessage.success("签到已撤销，课时已恢复");
    loadAttendances();
    loadEnrollments();
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "撤销失败");
  }
}

async function viewDetail(row: Attendance) {
  try {
    const res = await http.get(`/training/attendances/${row.id}`);
    currentAttendance.value = res.data;
    showDetailDialog.value = true;
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "加载详情失败");
  }
}

function editRemark(row: Attendance) {
  remarkForm.id = row.id;
  remarkForm.remark = row.remark || "";
  showRemarkDialog.value = true;
}

async function updateRemark() {
  try {
    await http.put(`/training/attendances/${remarkForm.id}`, { remark: remarkForm.remark });
    ElMessage.success("备注已更新");
    showRemarkDialog.value = false;
    loadAttendances();
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "更新失败");
  }
}

function resetFilters() {
  filters.student_id = undefined;
  filters.course_id = undefined;
  dateRange.value = [];
  pagination.page = 1;
  loadAttendances();
}

onMounted(() => {
  loadAttendances();
  loadStudents();
  loadCourses();
  loadEnrollments();
});
</script>

<style scoped>
.attendances-page {
  padding: 20px;
}

.filter-card,
.table-card {
  border-radius: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

:deep(.el-table) {
  font-size: 14px;
}

:deep(.el-pagination) {
  display: flex;
}
</style>

