<template>
  <div class="members-page">
    <div class="page-header">
      <div>
        <h2>会员管理</h2>
        <p class="sub-title">管理会员信息、余额与办卡类型（计次 / 时限 / 折扣）</p>
      </div>
      <el-button type="primary" size="large" @click="openAddDialog">新增会员</el-button>
    </div>

    <el-row :gutter="20" class="stat-row">
      <el-col :span="8">
        <div class="stat-card">
          <div class="stat-label">会员总数</div>
          <div class="stat-value">{{ stats.totalMembers }}</div>
          <div class="stat-sub">系统中已登记的会员人数</div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-card">
          <div class="stat-label">账户总余额</div>
          <div class="stat-value">¥ {{ formatMoney(stats.totalBalance) }}</div>
          <div class="stat-sub">所有会员当前账户余额合计</div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="stat-card">
          <div class="stat-label">累计消费总额</div>
          <div class="stat-value">¥ {{ formatMoney(stats.totalSpent) }}</div>
          <div class="stat-sub">会员历史消费合计（来自消费记录）</div>
        </div>
      </el-col>
    </el-row>

    <el-card class="card" shadow="hover">
      <div class="table-toolbar">
        <el-input
          v-model="keyword"
          placeholder="按姓名或手机号搜索"
          clearable
          style="width: 260px"
          @clear="reload"
          @keyup.enter.native="reload"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <el-select
          v-model="statusFilter"
          placeholder="按状态筛选"
          clearable
          style="width: 150px; margin-left: 12px"
        >
          <el-option label="全部状态" value="" />
          <el-option label="正常" value="正常" />
          <el-option label="禁用" value="禁用" />
          <el-option label="注销" value="注销" />
        </el-select>

        <el-button style="margin-left: 12px" @click="reload">刷新</el-button>
      </div>

      <el-table :data="filteredMembers" border style="width: 100%" v-loading="loading">
        <el-table-column prop="id" label="编号" width="80" />
        <el-table-column prop="name" label="姓名" width="120" />
        <el-table-column prop="phone" label="手机号" width="140" />
        <el-table-column prop="gender" label="性别" width="80" />
        <el-table-column prop="level" label="等级" min-width="140">
          <template #default="{ row }">
            <el-tag type="info" effect="light">
              {{ renderLevelLabel(row) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="balance" label="余额(元)" width="120">
          <template #default="{ row }">¥ {{ formatMoney(row.balance) }}</template>
        </el-table-column>
        <el-table-column prop="total_spent" label="累计消费(元)" width="140">
          <template #default="{ row }">¥ {{ formatMoney(row.total_spent) }}</template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag
              :type="
                row.status === '正常'
                  ? 'success'
                  : row.status === '禁用'
                  ? 'warning'
                  : 'danger'
              "
              effect="light"
            >
              {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="160" />
        <el-table-column prop="created_at" label="创建时间" width="180" />

        <el-table-column label="操作" width="520" fixed="right">
          <template #default="{ row }">
            <el-button
              link
              type="primary"
              size="small"
              @click="openEditDialog(row)"
            >
              编辑信息
            </el-button>
            <el-divider direction="vertical" />
            <el-button
              link
              type="primary"
              size="small"
              @click="openRechargeDialog(row)"
            >
              充值 / 扣费
            </el-button>
            <el-divider direction="vertical" />
            <el-button
              link
              type="warning"
              size="small"
              @click="openPasswordDialog(row)"
            >
              设置登录密码
            </el-button>
            <el-divider direction="vertical" />
            <el-button
              link
              type="danger"
              size="small"
              @click="handleResetPassword(row)"
            >
              重置密码
            </el-button>
            <el-divider direction="vertical" />
            <el-button
              link
              type="danger"
              size="small"
              @click="confirmDeleteMember(row)"
            >
              删除会员
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="!loading && !filteredMembers.length" class="empty-text">
        暂无会员数据，请点击右上角「新增会员」创建
      </div>
    </el-card>

    <!-- 新增会员 -->
    <el-dialog v-model="addDialogVisible" title="新增会员" width="540px">
      <el-form :model="addForm" label-width="90px">
        <el-form-item label="姓名">
          <el-input v-model="addForm.name" placeholder="请输入会员姓名" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="addForm.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="性别">
          <el-select v-model="addForm.gender" placeholder="请选择" style="width: 200px">
            <el-option label="男" value="男" />
            <el-option label="女" value="女" />
            <el-option label="未知" value="未知" />
          </el-select>
        </el-form-item>
        <el-form-item label="生日">
          <el-date-picker
            v-model="addForm.birthday"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="会员等级">
          <el-select v-model="addForm.level" placeholder="选择会员等级" style="width: 260px">
            <el-option
              v-for="level in memberLevelOptions"
              :key="level.code"
              :label="`${level.name}（${level.discount / 10}折）`"
              :value="level.code"
              :disabled="!level.enabled"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="初始余额">
          <el-input-number v-model="addForm.initial_balance" :min="0" :step="10" :precision="2" />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="addForm.status" style="width: 200px">
            <el-option label="正常" value="正常" />
            <el-option label="禁用" value="禁用" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            v-model="addForm.remark"
            type="textarea"
            :rows="3"
            placeholder="可填写会员偏好、健康注意事项等"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="addDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="addLoading" @click="submitAdd">确认</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 编辑会员 -->
    <el-dialog v-model="editDialogVisible" title="编辑会员信息" width="520px">
      <el-form :model="editForm" label-width="90px">
        <el-form-item label="姓名">
          <el-input v-model="editForm.name" placeholder="请输入会员姓名" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="editForm.phone" placeholder="请输入手机号" />
        </el-form-item>
        <el-form-item label="性别">
          <el-select v-model="editForm.gender" placeholder="请选择" style="width: 200px">
            <el-option label="男" value="男" />
            <el-option label="女" value="女" />
            <el-option label="未知" value="未知" />
          </el-select>
        </el-form-item>
        <el-form-item label="生日">
          <el-date-picker
            v-model="editForm.birthday"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-form-item label="会员等级">
          <el-select v-model="editForm.level" placeholder="选择会员等级" style="width: 260px">
            <el-option
              v-for="level in memberLevelOptions"
              :key="level.code"
              :label="`${level.name}（${level.discount / 10}折）`"
              :value="level.code"
              :disabled="!level.enabled"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="editForm.status" style="width: 200px">
            <el-option label="正常" value="正常" />
            <el-option label="禁用" value="禁用" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            v-model="editForm.remark"
            type="textarea"
            :rows="3"
            placeholder="可填写会员偏好、健康注意事项等"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="editLoading" @click="submitEdit">确认</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 充值 / 扣费 -->
    <el-dialog v-model="rechargeDialogVisible" title="会员充值 / 扣费" width="480px">
      <div v-if="currentMemberForRecharge" class="recharge-header">
        <div class="name-line">
          会员：<strong>{{ currentMemberForRecharge.name }}</strong>
          <span class="phone">（{{ currentMemberForRecharge.phone }}）</span>
        </div>
        <div class="balance-line">
          当前余额：
          <span class="money">¥ {{ formatMoney(currentMemberForRecharge.balance) }}</span>
        </div>
      </div>

      <el-form :model="rechargeForm" label-width="90px">
        <el-form-item label="类型">
          <el-select v-model="rechargeForm.type" style="width: 200px">
            <el-option label="充值" value="充值" />
            <el-option label="扣费" value="扣费" />
            <el-option label="消费" value="消费" />
            <el-option label="退款" value="退款" />
          </el-select>
        </el-form-item>
        <el-form-item label="金额">
          <el-input-number v-model="rechargeForm.amount" :min="0" :step="10" :precision="2" />
          <span class="amount-tip">元（必须大于 0）</span>
        </el-form-item>
        <el-form-item label="变动后余额">
          <span class="money">¥ {{ formatMoney(previewBalance) }}</span>
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            v-model="rechargeForm.remark"
            type="textarea"
            :rows="3"
            placeholder="可填写充值方式、扣费原因等"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="rechargeDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="rechargeLoading" @click="submitRecharge">确认</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 设置登录密码 -->
    <el-dialog v-model="passwordDialogVisible" title="设置会员登录密码" width="420px">
      <div v-if="currentMemberForPassword" class="password-header">
        <div class="name-line">
          会员：<strong>{{ currentMemberForPassword.name }}</strong>
          <span class="phone">（{{ currentMemberForPassword.phone }}）</span>
        </div>
      </div>

      <el-form :model="passwordForm" label-width="90px">
        <el-form-item label="新密码">
          <el-input
            v-model="passwordForm.password"
            type="password"
            show-password
            placeholder="请输入新密码"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="passwordDialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="passwordLoading" @click="submitPassword">确认</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Search } from "@element-plus/icons-vue";
import http from "../utils/http";

interface Member {
  id: number;
  name: string;
  phone: string;
  gender: string;
  birthday?: string | null;
  balance: number;
  total_spent: number;
  status: string;
  remark?: string | null;
  created_at: string;
  level?: string;
  level_name?: string;
  level_discount?: number;
}

interface AddMemberForm {
  name: string;
  phone: string;
  gender: string;
  birthday: string | null;
  initial_balance: number;
  status: string;
  remark: string;
  level: string;
}

interface EditMemberForm {
  name: string;
  phone: string;
  gender: string;
  birthday: string | null;
  status: string;
  remark: string;
  level: string;
}

interface MemberLevelOption {
  name: string;
  code: string;
  discount: number;
  enabled: boolean;
}

type RechargeType = "充值" | "扣费" | "消费" | "退款";
interface RechargeForm {
  type: RechargeType;
  amount: number;
  remark: string;
}

const loading = ref(false);
const members = ref<Member[]>([]);

const stats = ref({
  totalMembers: 0,
  totalBalance: 0,
  totalSpent: 0,
});

const memberLevelOptions = ref<MemberLevelOption[]>([]);
const defaultLevelCode = ref("");

const keyword = ref("");
const statusFilter = ref<string>("");

const addDialogVisible = ref(false);
const addLoading = ref(false);
const addForm = ref<AddMemberForm>({
  name: "",
  phone: "",
  gender: "未知",
  birthday: null,
  initial_balance: 0,
  status: "正常",
  remark: "",
  level: "",
});

const editDialogVisible = ref(false);
const editLoading = ref(false);
const editingMemberId = ref<number | null>(null);
const editForm = ref<EditMemberForm>({
  name: "",
  phone: "",
  gender: "未知",
  birthday: null,
  status: "正常",
  remark: "",
  level: "",
});

const currentMemberForRecharge = ref<Member | null>(null);
const rechargeDialogVisible = ref(false);
const rechargeLoading = ref(false);
const rechargeForm = ref<RechargeForm>({
  type: "充值",
  amount: 0,
  remark: "",
});

const currentMemberForPassword = ref<Member | null>(null);
const passwordDialogVisible = ref(false);
const passwordLoading = ref(false);
const passwordForm = ref<{ password: string }>({ password: "" });

const formatMoney = (value: unknown) => {
  const n = Number(value || 0);
  if (Number.isNaN(n)) return "0.00";
  return n.toFixed(2);
};

const previewBalance = computed(() => {
  if (!currentMemberForRecharge.value) return 0;
  const origin = Number(currentMemberForRecharge.value.balance || 0);
  const amount = Number(rechargeForm.value.amount || 0);
  if (amount <= 0) return origin;
  if (rechargeForm.value.type === "充值" || rechargeForm.value.type === "退款") {
    return origin + amount;
  }
  return origin - amount;
});

const filteredMembers = computed(() => {
  let list = members.value.slice();
  if (keyword.value) {
    const kw = keyword.value.trim();
    list = list.filter(
      (m) =>
        m.name.includes(kw) ||
        (m.phone && m.phone.includes(kw)),
    );
  }
  if (statusFilter.value) {
    list = list.filter((m) => m.status === statusFilter.value);
  }
  return list;
});

const loadMembers = async () => {
  loading.value = true;
  try {
    // 后端现在返回分页格式 { total, items }
    const res = await http.get<{ total: number; items: Member[] } | Member[]>("/members", {
      params: {
        page: 1,
        page_size: 1000, // 获取所有数据（前端筛选）
        keyword: keyword.value || undefined,
        status: statusFilter.value || undefined,
      },
    });
    
    // 兼容新旧API格式
    const data = res.data;
    if (Array.isArray(data)) {
      // 旧格式：直接返回数组
      members.value = data;
    } else if (data && typeof data === 'object' && 'items' in data) {
      // 新格式：{ total, items }
      members.value = data.items || [];
    } else {
      members.value = [];
    }
    
    const totalMembers = members.value.length;
    const totalBalance = members.value.reduce(
      (sum, m) => sum + Number(m.balance || 0),
      0,
    );
    const totalSpent = members.value.reduce(
      (sum, m) => sum + Number(m.total_spent || 0),
      0,
    );
    stats.value = { totalMembers, totalBalance, totalSpent };
  } catch (err) {
    console.error(err);
    ElMessage.error("获取会员列表失败");
  } finally {
    loading.value = false;
  }
};

const reload = () => {
  loadMembers();
};

const loadMemberLevelOptions = async () => {
  try {
    const res = await http.get("/system-settings/member-config");
    const data = res.data || {};
    const levels = Array.isArray(data.member_levels) ? data.member_levels : [];
    memberLevelOptions.value = levels.map((item: any) => ({
      name: item.name || item.code || "未命名",
      code: item.code || item.name || "",
      discount: Number(item.discount || 100),
      enabled: item.enabled !== false,
    }));
    defaultLevelCode.value = data.default_level || "";
  } catch (err) {
    console.error(err);
    memberLevelOptions.value = [];
  }
};

const resolveDefaultLevel = () => {
  if (defaultLevelCode.value) return defaultLevelCode.value;
  const enabled = memberLevelOptions.value.find((lv) => lv.enabled);
  return enabled?.code || memberLevelOptions.value[0]?.code || "";
};

const renderLevelLabel = (member: Member) => {
  if (member.level_name) return `${member.level_name}${member.level_discount ? `（${member.level_discount / 10}折）` : ""}`;
  const found = memberLevelOptions.value.find(
    (lv) => lv.code === member.level || lv.name === member.level,
  );
  if (found) {
    return `${found.name}${found.discount ? `（${found.discount / 10}折）` : ""}`;
  }
  return member.level || "普通会员";
};

const openAddDialog = () => {
  addForm.value = {
    name: "",
    phone: "",
    gender: "未知",
    birthday: null,
    initial_balance: 0,
    status: "正常",
    remark: "",
    level: resolveDefaultLevel(),
  };
  addDialogVisible.value = true;
};

const submitAdd = async () => {
  if (!addForm.value.name || !addForm.value.phone) {
    ElMessage.warning("请填写姓名和手机号");
    return;
  }

  const payload = { ...addForm.value };

  try {
    addLoading.value = true;
    await http.post("/members", payload);
    ElMessage.success("新增会员成功");
    addDialogVisible.value = false;
    await loadMembers();
  } catch (err: any) {
    console.error(err);
    const msg =
      err?.response?.data?.detail || "新增会员失败，请稍后重试";
    ElMessage.error(msg);
  } finally {
    addLoading.value = false;
  }
};

const openEditDialog = (member: Member) => {
  editingMemberId.value = member.id;
  editForm.value = {
    name: member.name,
    phone: member.phone,
    gender: member.gender || "未知",
    birthday: member.birthday || null,
    status: member.status || "正常",
    remark: (member.remark as string) || "",
    level: member.level || resolveDefaultLevel(),
  };
  editDialogVisible.value = true;
};

const submitEdit = async () => {
  if (!editingMemberId.value) return;
  if (!editForm.value.name || !editForm.value.phone) {
    ElMessage.warning("请填写姓名和手机号");
    return;
  }
  try {
    editLoading.value = true;
    await http.put(`/members/${editingMemberId.value}`, editForm.value);
    ElMessage.success("会员信息已更新");
    editDialogVisible.value = false;
    await loadMembers();
  } catch (err: any) {
    console.error(err);
    const msg =
      err?.response?.data?.detail || "更新会员失败，请稍后重试";
    ElMessage.error(msg);
  } finally {
    editLoading.value = false;
  }
};

const openRechargeDialog = (member: Member) => {
  currentMemberForRecharge.value = member;
  rechargeForm.value = { type: "充值", amount: 0, remark: "" };
  rechargeDialogVisible.value = true;
};

const submitRecharge = async () => {
  if (!currentMemberForRecharge.value) return;
  const amount = Number(rechargeForm.value.amount || 0);
  if (!amount || amount <= 0) {
    ElMessage.warning("金额必须大于 0");
    return;
  }
  const payload = {
    member_id: currentMemberForRecharge.value.id,
    type: rechargeForm.value.type,
    amount,
    remark: rechargeForm.value.remark,
  };
  try {
    rechargeLoading.value = true;
    await http.post("/member-transactions", payload);
    ElMessage.success("操作成功");
    rechargeDialogVisible.value = false;
    await loadMembers();
  } catch (err: any) {
    console.error(err);
    const msg =
      err?.response?.data?.detail || "操作失败，请稍后重试";
    ElMessage.error(msg);
  } finally {
    rechargeLoading.value = false;
  }
};

const openPasswordDialog = (member: Member) => {
  currentMemberForPassword.value = member;
  passwordForm.value = { password: "" };
  passwordDialogVisible.value = true;
};

const submitPassword = async () => {
  if (!currentMemberForPassword.value) return;
  const pwd = (passwordForm.value.password || "").trim();
  if (!pwd) {
    ElMessage.warning("请输入密码");
    return;
  }
  if (pwd.length < 6) {
    ElMessage.warning("密码长度至少 6 位");
    return;
  }
  try {
    passwordLoading.value = true;
    await http.put(
      `/members/${currentMemberForPassword.value.id}/login-password`,
      { password: pwd },
    );
    ElMessage.success("设置密码成功");
    passwordDialogVisible.value = false;
  } catch (err: any) {
    console.error(err);
    const msg =
      err?.response?.data?.detail || "设置密码失败，请稍后重试";
    ElMessage.error(msg);
  } finally {
    passwordLoading.value = false;
  }
};

const handleResetPassword = (member: Member) => {
  ElMessageBox.confirm(
    `确定将会员【${member.name}】的登录密码重置为默认值吗？重置后将覆盖其原有密码。`,
    "重置密码确认",
    {
      type: "warning",
      confirmButtonText: "确定",
      cancelButtonText: "取消",
    },
  )
    .then(async () => {
      try {
        await http.post(`/members/${member.id}/reset-password`);
        ElMessage.success("密码重置成功，默认密码为 123456");
      } catch (err: any) {
        console.error(err);
        const msg =
          err?.response?.data?.detail ||
          "重置密码失败，请稍后重试";
        ElMessage.error(msg);
      }
    })
    .catch(() => {});
};

const confirmDeleteMember = async (member: Member) => {
  try {
    // 先获取关联数据统计
    const statsPromises = [
      http.get("/court-reservations", { params: { member_id: member.id, page_size: 1 } }),
      http.get("/orders", { params: { member_id: member.id, page_size: 1 } }),
      http.get("/member-transactions", { params: { member_id: member.id, page_size: 1 } }),
    ];
    
    const results = await Promise.all(statsPromises.map(p => 
      p.catch(() => ({ data: { total: 0 } }))
    ));
    
    const reservationCount = results[0]?.data?.total || 0;
    const orderCount = results[1]?.data?.total || 0;
    const transactionCount = results[2]?.data?.total || 0;
    
    const detailMsg = `
      <div style="text-align: left; line-height: 1.8;">
        <p style="margin-bottom: 12px;">确定要彻底删除会员【<strong>${member.name}</strong>】吗？</p>
        <p style="color: #f56c6c; margin-bottom: 8px;">⚠️ 此操作将同时删除以下关联数据：</p>
        <ul style="padding-left: 20px; margin: 0;">
          <li>${reservationCount} 条场地预约记录</li>
          <li>${orderCount} 条订单记录</li>
          <li>${transactionCount} 条流水记录</li>
          <li>该会员的所有卡片、通知等数据</li>
        </ul>
        <p style="color: #f56c6c; margin-top: 12px;">删除后数据将<strong>无法恢复</strong>！</p>
      </div>
    `;
    
    await ElMessageBox.confirm(detailMsg, "删除会员确认", {
      confirmButtonText: "确定删除",
      cancelButtonText: "取消",
      type: "error",
      dangerouslyUseHTMLString: true,
    });
    
    await handleDeleteMember(member);
  } catch (err: any) {
    if (err !== "cancel") {
      console.error(err);
      ElMessage.error("获取会员数据统计失败");
    }
  }
};

const handleDeleteMember = async (member: Member) => {
  try {
    await http.delete(`/members/${member.id}`);
    ElMessage.success("会员已删除");
    await loadMembers();
  } catch (err: any) {
    console.error(err);
    const msg =
      err?.response?.data?.detail ||
      "删除会员失败，请稍后重试";
    ElMessage.error(msg);
  }
};

onMounted(async () => {
  await loadMemberLevelOptions();
  addForm.value.level = resolveDefaultLevel();
  editForm.value.level = resolveDefaultLevel();
  loadMembers();
});
</script>

<style scoped>
/* ========== Apple iOS 风格浅色主题 ========== */
.members-page {
  padding: 0;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.page-header h2 {
  font-size: 28px;
  font-weight: 600;
  color: #1D1D1F;
  letter-spacing: -0.02em;
  margin: 0;
}

.sub-title {
  margin: 4px 0 0;
  color: #86868B;
  font-size: 14px;
}

.stat-row {
  margin-bottom: 24px;
}

.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.stat-label {
  font-size: 13px;
  color: #86868B;
  margin-bottom: 8px;
  font-weight: 500;
}

.stat-value {
  font-size: 28px;
  font-weight: 600;
  color: #1D1D1F;
  margin-bottom: 4px;
  letter-spacing: -0.02em;
}

.stat-sub {
  font-size: 12px;
  color: #AEAEB2;
}

.card {
  border-radius: 12px;
  background: #fff;
  border: none;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.table-toolbar {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.empty-text {
  padding: 24px;
  text-align: center;
  font-size: 14px;
  color: #86868B;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.recharge-header,
.password-header {
  margin-bottom: 16px;
  font-size: 14px;
  color: #1D1D1F;
}

.recharge-header .name-line,
.password-header .name-line {
  margin-bottom: 4px;
  font-weight: 500;
}

.recharge-header .phone,
.password-header .phone {
  color: #86868B;
}

.recharge-header .balance-line .money {
  color: #007AFF;
  font-weight: 600;
}

.amount-tip {
  margin-left: 8px;
  font-size: 12px;
  color: #86868B;
}

.money {
  color: #1D1D1F;
  font-weight: 600;
}
</style>
