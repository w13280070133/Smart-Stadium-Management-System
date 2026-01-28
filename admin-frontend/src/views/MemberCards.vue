<template>
  <div class="page member-cards">
    <div class="page-header">
      <div>
        <h2>会员卡</h2>
        <p class="desc">管理计次卡 / 折扣卡，可快速开卡、扣次、续期</p>
      </div>
      <div class="actions">
        <el-select
          v-model="filters.memberId"
          placeholder="按会员筛选"
          filterable
          clearable
          size="small"
          style="width: 200px"
          @change="loadCards"
        >
          <el-option v-for="m in memberOptions" :key="m.id" :label="m.label" :value="m.id" />
        </el-select>
        <el-button type="primary" @click="openDialog()">新增会员卡</el-button>
      </div>
    </div>

    <el-card shadow="never" class="card-panel">
      <el-table v-loading="loading" :data="cards" border>
        <el-table-column prop="card_name" label="卡名称" min-width="140" />
        <el-table-column prop="member_name" label="会员" min-width="160">
          <template #default="scope">
            <div class="member-cell">
              <div class="name">{{ scope.row.member_name || "-" }}</div>
              <div class="phone">{{ scope.row.member_phone || "" }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="card_type" label="类型" width="110">
          <template #default="scope">
            <el-tag type="info" effect="plain">{{ renderType(scope.row.card_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="次数/折扣" min-width="150">
          <template #default="scope">
            <div v-if="scope.row.card_type === 'times'">
              <el-tag size="small" type="success">
                剩余 {{ scope.row.remaining_times ?? "-" }} / {{ scope.row.total_times ?? "-" }}
              </el-tag>
            </div>
            <div v-else-if="scope.row.card_type === 'discount'">
              <el-tag size="small" type="warning">{{ scope.row.discount }} 折</el-tag>
            </div>
            <div v-else>-</div>
          </template>
        </el-table-column>
        <el-table-column label="有效期" min-width="180">
          <template #default="scope">
            <div class="date-range">{{ scope.row.start_date }} ~ {{ scope.row.end_date }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="180" />
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="scope">
            <el-space>
              <el-button size="small" @click="openDialog(scope.row)">编辑</el-button>
              <el-button size="small" type="warning" @click="deductOnce(scope.row)" :disabled="!canDeduct(scope.row)">
                扣 1 次
              </el-button>
              <el-button size="small" @click="extend30(scope.row)">续期 30 天</el-button>
              <el-button size="small" type="danger" plain @click="handleDelete(scope.row)">删除</el-button>
            </el-space>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="dialogVisible" :title="form.id ? '编辑会员卡' : '新增会员卡'" width="520px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="会员" prop="member_id">
          <el-select v-model="form.member_id" placeholder="请选择会员" filterable style="width: 100%">
            <el-option v-for="m in memberOptions" :key="m.id" :label="m.label" :value="m.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="卡名称" prop="card_name">
          <el-input v-model="form.card_name" placeholder="如：羽毛球10次卡" />
        </el-form-item>
        <el-form-item label="类型" prop="card_type">
          <el-select v-model="form.card_type" placeholder="请选择" style="width: 100%">
            <el-option label="计次卡" value="times" />
            <el-option label="折扣卡" value="discount" />
            <el-option label="月卡" value="month" />
            <el-option label="年卡" value="year" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="form.card_type === 'times'" label="总次数">
          <el-input-number v-model="form.total_times" :min="0" :max="99999" controls-position="right" />
        </el-form-item>
        <el-form-item v-if="form.card_type === 'times'" label="剩余次数">
          <el-input-number v-model="form.remaining_times" :min="0" :max="99999" controls-position="right" />
        </el-form-item>
        <el-form-item v-if="form.card_type === 'discount'" label="折扣(如90=9折)">
          <el-input-number v-model="form.discount" :min="1" :max="100" :step="1" controls-position="right" />
        </el-form-item>
        <el-form-item label="有效期" required>
          <el-date-picker
            v-model="formDateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" rows="2" placeholder="备注限制/使用范围等" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import type { FormInstance, FormRules } from "element-plus";
import http from "../utils/http";

interface MemberOption {
  id: number;
  label: string;
}

interface CardItem {
  id?: number;
  member_id?: number;
  member_name?: string;
  member_phone?: string;
  card_name?: string;
  card_type?: string;
  total_times?: number | null;
  remaining_times?: number | null;
  discount?: number | null;
  start_date?: string;
  end_date?: string;
  remark?: string;
}

const loading = ref(false);
const dialogVisible = ref(false);
const formRef = ref<FormInstance>();
const cards = ref<CardItem[]>([]);
const memberOptions = ref<MemberOption[]>([]);
const filters = reactive({ memberId: undefined as number | undefined });

const form = reactive<CardItem>({
  id: undefined,
  member_id: undefined,
  card_name: "",
  card_type: "times",
  total_times: 0,
  remaining_times: 0,
  discount: 100,
  start_date: "",
  end_date: "",
  remark: "",
});

const formDateRange = ref<[string, string] | null>(null);

const rules: FormRules = {
  member_id: [{ required: true, message: "请选择会员", trigger: "change" }],
  card_name: [{ required: true, message: "请输入卡名称", trigger: "blur" }],
  card_type: [{ required: true, message: "请选择卡类型", trigger: "change" }],
};

const renderType = (t?: string) => {
  if (t === "times") return "计次卡";
  if (t === "discount") return "折扣卡";
  if (t === "month") return "月卡";
  if (t === "year") return "年卡";
  return t || "-";
};

const resetForm = () => {
  form.id = undefined;
  form.member_id = undefined;
  form.card_name = "";
  form.card_type = "times";
  form.total_times = 0;
  form.remaining_times = 0;
  form.discount = 100;
  form.start_date = "";
  form.end_date = "";
  form.remark = "";
  formDateRange.value = null;
};

const openDialog = (row?: CardItem) => {
  resetForm();
  if (row) {
    form.id = row.id;
    form.member_id = row.member_id;
    form.card_name = row.card_name;
    form.card_type = row.card_type;
    form.total_times = row.total_times ?? 0;
    form.remaining_times = row.remaining_times ?? 0;
    form.discount = row.discount ?? 100;
    form.start_date = row.start_date;
    form.end_date = row.end_date;
    form.remark = row.remark;
    formDateRange.value = row.start_date && row.end_date ? [row.start_date, row.end_date] : null;
  }
  dialogVisible.value = true;
};

const loadMembers = async () => {
  try {
    const res = await http.get("/members", { params: { page_size: 1000 } });
    const arr = res.data?.items || res.data || [];
    memberOptions.value = arr.map((m: any) => ({
      id: m.id,
      label: `${m.name || "未命名"}（${m.phone || ""}）`,
    }));
  } catch (e) {
    memberOptions.value = [];
  }
};

const loadCards = async () => {
  loading.value = true;
  try {
    const params: any = {};
    if (filters.memberId) params.member_id = filters.memberId;
    const res = await http.get("/member-cards", { params });
    cards.value = res.data || [];
  } catch (e) {
    cards.value = [];
  } finally {
    loading.value = false;
  }
};

const submitForm = async () => {
  if (!formRef.value) return;
  await formRef.value.validate(async (ok) => {
    if (!ok) return;
    if (formDateRange.value) {
      form.start_date = formDateRange.value[0];
      form.end_date = formDateRange.value[1];
    } else {
      ElMessage.error("请选择有效期");
      return;
    }
    const payload: any = { ...form };
    if (form.card_type !== "times") {
      payload.total_times = null;
      payload.remaining_times = null;
    }
    if (form.card_type !== "discount") {
      payload.discount = null;
    }
    try {
      if (form.id) {
        await http.put(`/member-cards/${form.id}`, payload);
        ElMessage.success("已更新");
      } else {
        await http.post("/member-cards", payload);
        ElMessage.success("已开卡");
      }
      dialogVisible.value = false;
      loadCards();
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.detail || "保存失败");
    }
  });
};

const canDeduct = (row: CardItem) => row.card_type === "times" && (row.remaining_times ?? 0) > 0;

const deductOnce = async (row: CardItem) => {
  if (!canDeduct(row)) {
    ElMessage.warning("剩余次数不足");
    return;
  }
  try {
    await http.put(`/member-cards/${row.id}`, { remaining_times: (row.remaining_times || 0) - 1 });
    ElMessage.success("已扣除 1 次");
    loadCards();
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "扣次失败");
  }
};

const extend30 = async (row: CardItem) => {
  const end = row.end_date ? new Date(row.end_date) : new Date();
  const newDate = new Date(end.getTime() + 30 * 24 * 60 * 60 * 1000);
  const y = newDate.getFullYear();
  const m = String(newDate.getMonth() + 1).padStart(2, "0");
  const d = String(newDate.getDate()).padStart(2, "0");
  const endStr = `${y}-${m}-${d}`;
  try {
    await http.put(`/member-cards/${row.id}`, { end_date: endStr });
    ElMessage.success("已续期 30 天");
    loadCards();
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "续期失败");
  }
};

const handleDelete = (row: CardItem) => {
  ElMessageBox.confirm(`确认删除会员卡「${row.card_name}」?`, "提示", { type: "warning" })
    .then(async () => {
      await http.delete(`/member-cards/${row.id}`);
      ElMessage.success("已删除");
      loadCards();
    })
    .catch(() => null);
};

watch(
  () => form.total_times,
  (val) => {
    if (!form.id && form.card_type === "times" && typeof val === "number") {
      form.remaining_times = val;
    }
  },
);

onMounted(() => {
  loadMembers();
  loadCards();
});
</script>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: #F2F2F7;
}
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.page-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1D1D1F;
}
.desc {
  margin: 4px 0 0;
  color: #86868B;
  font-size: 13px;
}
.actions {
  display: flex;
  gap: 10px;
  align-items: center;
}
.card-panel {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.member-cell .name {
  font-weight: 600;
  color: #1D1D1F;
}
.member-cell .phone {
  color: #86868B;
  font-size: 12px;
}
.date-range {
  color: #1D1D1F;
}
</style>
