<template>
  <div class="page">
    <!-- 顶部标题 -->
    <div class="page-header">
      <div>
        <h2>会员收支记录</h2>
        <p class="sub-title">查看所有会员的充值、扣费和消费流水。</p>
      </div>
    </div>

    <!-- 筛选区 -->
    <el-card class="filter-card" shadow="never">
      <div class="filter-row">
        <el-select
          v-model="filters.memberId"
          placeholder="按会员筛选"
          clearable
          filterable
          style="width: 220px"
        >
          <el-option
            v-for="m in memberOptions"
            :key="m.id"
            :label="m.name + '（' + m.phone + '）'"
            :value="m.id"
          />
        </el-select>

        <el-select
          v-model="filters.type"
          placeholder="按类型筛选"
          clearable
          style="width: 150px"
        >
          <el-option
            v-for="opt in typeOptions"
            :key="opt.value"
            :label="opt.label"
            :value="opt.value"
          />
        </el-select>

        <el-date-picker
          v-model="filters.dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          value-format="YYYY-MM-DD"
        />

        <el-button type="primary" @click="loadTransactions">查询</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </div>
    </el-card>

    <!-- 操作区：选择会员后才能充值/扣费 -->
    <el-card class="toolbar-card" shadow="never">
      <div class="toolbar">
        <el-select
          v-model="currentMemberId"
          placeholder="选择一个会员进行充值/扣费"
          filterable
          style="width: 260px"
        >
          <el-option
            v-for="m in memberOptions"
            :key="m.id"
            :label="m.name + '（' + m.phone + '）'"
            :value="m.id"
          />
        </el-select>

        <el-button
          type="primary"
          :disabled="!currentMember"
          @click="openChargeDialog"
        >
          充值 / 扣费
        </el-button>

        <div v-if="currentMember" class="balance-text">
          当前会员：
          <strong>{{ currentMember.name }}</strong>
          &nbsp;余额：
          <span class="money">¥ {{ formatAmount(currentMember.balance) }}</span>
        </div>
      </div>
    </el-card>

    <!-- 列表 -->
    <el-card class="table-card" shadow="hover">
      <el-table
        :data="transactions"
        border
        style="width: 100%"
        v-loading="loading"
      >
        <el-table-column prop="id" label="编号" width="80" />
        <el-table-column prop="member_name" label="会员" width="160" />
        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag
              v-if="row.type === '充值'"
              type="success"
              effect="light"
            >
              充值
            </el-tag>
            <el-tag
              v-else-if="row.type === '扣费'"
              type="danger"
              effect="light"
            >
              扣费
            </el-tag>
            <el-tag v-else type="warning" effect="light">
              消费
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="amount" label="金额（元）" width="120">
          <template #default="{ row }">
            <span :class="row.type === '充值' ? 'money-plus' : 'money-minus'">
              {{ row.type === '充值' ? '+' : '-' }}
              {{ formatAmount(row.amount) }}
            </span>
          </template>
        </el-table-column>

        <el-table-column prop="balance_after" label="变动后余额（元）" width="150">
          <template #default="{ row }">
            ¥ {{ formatAmount(row.balance_after) }}
          </template>
        </el-table-column>

        <el-table-column prop="remark" label="备注" />
        <el-table-column prop="created_at" label="时间" width="180" />
      </el-table>

      <div v-if="!loading && !transactions.length" class="empty-text">
        暂无收支记录。
      </div>
    </el-card>

    <!-- 充值 / 扣费弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      title="会员充值 / 扣费"
      width="480px"
    >
      <div v-if="currentMember" class="dialog-member-info">
        <div>会员：{{ currentMember.name }}（{{ currentMember.phone }}）</div>
        <div>当前余额：<span class="money">¥ {{ formatAmount(currentMember.balance) }}</span></div>
      </div>

      <el-form :model="form" label-width="80px">
        <el-form-item label="类型">
          <el-select v-model="form.type" style="width: 160px">
            <el-option label="充值" value="充值" />
            <el-option label="扣费" value="扣费" />
          </el-select>
        </el-form-item>

        <el-form-item label="金额">
          <el-input-number
            v-model="form.amount"
            :min="0.01"
            :step="10"
            :precision="2"
          />
        </el-form-item>

        <el-form-item label="备注">
          <el-input
            v-model="form.remark"
            type="textarea"
            :rows="3"
            placeholder="可填写充值方式、扣费原因等"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取 消</el-button>
          <el-button type="primary" :loading="saving" @click="submitCharge">
            确 定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { ElMessage } from "element-plus";
import http from "../utils/http";

interface MemberOption {
  id: number;
  name: string;
  phone: string;
  balance: number;
}

interface Transaction {
  id: number;
  member_id: number;
  member_name: string;
  type: string; // 充值 | 扣费 | 消费
  amount: number | string;
  balance_after: number | string;
  remark: string;
  created_at: string;
}

interface Filters {
  memberId: number | null;
  type: string;
  dateRange: string[]; // [start, end]
}

interface ChargeForm {
  type: "充值" | "扣费";
  amount: number;
  remark: string;
}

const loading = ref(false);
const transactions = ref<Transaction[]>([]);

const memberOptions = ref<MemberOption[]>([]);
const filters = ref<Filters>({
  memberId: null,
  type: "",
  dateRange: [],
});

const typeOptions = [
  { label: "全部类型", value: "" },
  { label: "充值", value: "充值" },
  { label: "扣费", value: "扣费" },
  { label: "消费", value: "消费" },
];

// 当前选中的“操作会员”
const currentMemberId = ref<number | null>(null);
const currentMember = computed(() =>
  memberOptions.value.find((m) => m.id === currentMemberId.value) || null
);

// 充值弹窗
const dialogVisible = ref(false);
const saving = ref(false);
const form = ref<ChargeForm>({
  type: "充值",
  amount: 0,
  remark: "",
});

const formatAmount = (v: unknown) => {
  const n = Number(v);
  if (Number.isNaN(n)) return "0.00";
  return n.toFixed(2);
};

// 加载会员列表
const loadMembers = async () => {
  try {
    const res = await http.get<any[]>("/members");
    memberOptions.value = (res.data || []).map((m: any) => ({
      id: m.id,
      name: m.name,
      phone: m.phone,
      balance: m.balance ?? 0,
    }));
  } catch (err) {
    console.error(err);
    ElMessage.error("获取会员列表失败");
  }
};

// 加载收支记录
const loadTransactions = async () => {
  loading.value = true;
  try {
    const params: any = {};
    if (filters.value.memberId) params.member_id = filters.value.memberId;
    if (filters.value.type) params.type = filters.value.type;
    if (filters.value.dateRange && filters.value.dateRange.length === 2) {
      params.start_date = filters.value.dateRange[0];
      params.end_date = filters.value.dateRange[1];
    }

    const res = await http.get<Transaction[]>("/member-transactions", {
      params,
    });
    transactions.value = res.data || [];
  } catch (err) {
    console.error(err);
    ElMessage.error("获取收支记录失败");
  } finally {
    loading.value = false;
  }
};

const resetFilters = () => {
  filters.value = {
    memberId: null,
    type: "",
    dateRange: [],
  };
  loadTransactions();
};

// 打开充值弹窗
const openChargeDialog = () => {
  if (!currentMember.value) {
    ElMessage.warning("请先在上方选择一个会员");
    return;
  }
  form.value = {
    type: "充值",
    amount: 0,
    remark: "",
  };
  dialogVisible.value = true;
};

// 提交充值 / 扣费
const submitCharge = async () => {
  if (!currentMember.value) {
    ElMessage.warning("未选择会员");
    return;
  }
  if (!form.value.amount || form.value.amount <= 0) {
    ElMessage.warning("请输入大于 0 的金额");
    return;
  }

  const payload = {
    member_id: currentMember.value.id,
    type: form.value.type, // 这里就是：'充值' 或 '扣费'
    amount: form.value.amount,
    remark: form.value.remark,
  };

  try {
    saving.value = true;
    await http.post("/member-transactions", payload);
    ElMessage.success("操作成功");

    dialogVisible.value = false;
    await Promise.all([loadMembers(), loadTransactions()]);
  } catch (err: any) {
    console.error(err);
    const msg = err?.response?.data?.detail || "操作失败，请稍后重试";
    ElMessage.error(msg);
  } finally {
    saving.value = false;
  }
};

onMounted(async () => {
  await Promise.all([loadMembers(), loadTransactions()]);
});
</script>

<style scoped>
.page {
  padding: 16px 24px 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sub-title {
  margin: 4px 0 0;
  font-size: 13px;
  color: #6b7280;
}

.filter-card,
.toolbar-card,
.table-card {
  border-radius: 16px;
}

.filter-row {
  display: flex;
  gap: 12px;
  align-items: center;
}

.toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
}

.balance-text {
  margin-left: auto;
  font-size: 14px;
  color: #4b5563;
}

.money {
  color: #10b981;
  font-weight: 600;
}

.money-plus {
  color: #16a34a;
  font-weight: 600;
}

.money-minus {
  color: #ef4444;
  font-weight: 600;
}

.empty-text {
  padding: 16px;
  text-align: center;
  font-size: 13px;
  color: #9ca3af;
}

.dialog-member-info {
  margin-bottom: 12px;
  padding: 8px 12px;
  background: #f3f4f6;
  border-radius: 10px;
  font-size: 14px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
