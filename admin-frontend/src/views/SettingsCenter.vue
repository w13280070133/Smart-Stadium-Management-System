<template>
  <div class="settings-page">
    <div class="page-header">
      <div>
        <h2>系统设置中心</h2>
        <p class="sub-title">配置系统基础信息、业务规则、会员体系、权限控制及数据管理</p>
      </div>
      <el-button type="primary" size="large" :loading="saveLoading" @click="handleSave">
        保存所有设置
      </el-button>
    </div>

    <!-- 功能一：基础信息 -->
    <el-card shadow="hover" class="card">
      <template #header>
        <div class="card-header">功能一：基础信息</div>
      </template>
      <el-form :model="settings.basic" label-width="120px" class="form">
        <el-form-item label="系统标题">
          <el-input v-model="settings.basic.system_name" placeholder="健身馆管理系统" />
        </el-form-item>
        <el-form-item label="场馆名称">
          <el-input v-model="settings.basic.gym_name" placeholder="XX体育馆" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="settings.basic.contact_phone" placeholder="400-xxx-xxxx" />
        </el-form-item>
        <el-form-item label="场馆地址">
          <el-input v-model="settings.basic.address" placeholder="请输入详细地址" />
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 功能二：营业时间与预约规则 -->
    <el-card shadow="hover" class="card">
      <template #header>
        <div class="card-header">功能二：营业时间与预约规则</div>
      </template>
      <el-form :model="settings.business" label-width="220px" class="form">
        <el-form-item label="营业开始时间">
          <el-time-select
            v-model="settings.business.business_open_time"
            start="00:00"
            step="00:30"
            end="23:30"
            placeholder="选择时间"
          />
        </el-form-item>
        <el-form-item label="营业结束时间">
          <el-time-select
            v-model="settings.business.business_close_time"
            start="00:00"
            step="00:30"
            end="23:30"
            placeholder="选择时间"
          />
        </el-form-item>
        <el-form-item label="每次预约时长（分钟）">
          <el-input-number v-model="settings.business.reservation_slot_minutes" :min="10" :max="300" />
          <span class="tip">预约时必须是该时长的整数倍</span>
        </el-form-item>
        <el-form-item label="允许提前预约天数">
          <el-input-number v-model="settings.business.reservation_open_days" :min="1" :max="365" />
          <span class="tip">超过此天数的预约将被拒绝</span>
        </el-form-item>
        <el-form-item label="开场前禁止取消（小时）">
          <el-input-number v-model="settings.business.reservation_cancel_limit_hours" :min="0" :max="72" />
          <span class="tip">开场前多少小时内不能取消</span>
        </el-form-item>
        <el-form-item label="未支付自动取消（分钟）">
          <el-input-number v-model="settings.business.auto_cancel_minutes" :min="5" :max="600" />
          <span class="tip">超过此时间未支付自动取消</span>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 功能三：会员与卡种 -->
    <el-card shadow="hover" class="card">
      <template #header>
        <div class="card-header">功能三：会员与卡种</div>
      </template>
      
      <!-- 会员等级设置 -->
      <div class="section">
        <p class="section-desc">
          会员消费模式：新增会员 → 充值余额 → 使用余额预订场地<br/>
          等级折扣：100 = 原价，90 = 9折，80 = 8折
        </p>
        
        <el-form label-width="150px" class="form" style="margin-bottom: 12px">
          <el-form-item label="新会员默认等级">
            <el-select v-model="settings.member.default_level" placeholder="选择默认等级" style="width: 260px">
              <el-option
                v-for="level in memberLevels"
                :key="level.name"
                :label="level.name"
                :value="level.name"
                :disabled="!level.enabled"
              />
            </el-select>
            <span class="tip">新注册会员默认分配此等级</span>
          </el-form-item>
        </el-form>

        <el-table :data="memberLevels" border style="width: 100%; margin-bottom: 8px">
          <el-table-column prop="name" label="等级名称" min-width="160">
            <template #default="{ row }">
              <el-input v-model="row.name" placeholder="普通会员" />
            </template>
          </el-table-column>
          <el-table-column prop="code" label="等级编码" width="140">
            <template #default="{ row }">
              <el-input v-model="row.code" placeholder="normal" />
            </template>
          </el-table-column>
          <el-table-column prop="discount" label="折扣" width="120">
            <template #default="{ row }">
              <el-input-number v-model="row.discount" :min="1" :max="100" :step="5" />
            </template>
          </el-table-column>
          <el-table-column prop="enabled" label="启用" width="100" align="center">
            <template #default="{ row }">
              <el-switch v-model="row.enabled" />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" align="center">
            <template #default="{ $index }">
              <el-button type="danger" link size="small" @click="removeLevel($index)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-button @click="addLevel">+ 新增等级</el-button>
      </div>
    </el-card>

    <!-- 功能四：订单/日志 -->
    <el-card shadow="hover" class="card">
      <template #header>
        <div class="card-header">功能四：订单/日志</div>
      </template>
      <el-form label-width="220px" class="form">
        <el-form-item label="订单数据保留时间（天）">
          <el-input-number v-model="settings.order.keep_days" :min="30" :max="3650" />
          <span class="tip">超过此天数的订单可被清理</span>
        </el-form-item>
        <el-form-item label="日志数据保留时间（天）">
          <el-input-number v-model="settings.log.keep_days" :min="7" :max="365" />
          <span class="tip">超过此天数的日志可被清理</span>
        </el-form-item>
        <el-form-item label="操作">
          <el-button type="warning" @click="handleCleanOldData">清除过期数据</el-button>
          <span class="tip">根据上述保留时间清除旧数据</span>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 功能五：角色与菜单权限 -->
    <el-card shadow="hover" class="card">
      <template #header>
        <div class="card-header">功能五：角色与菜单权限</div>
      </template>
      <p class="section-desc">配置不同角色可访问的功能菜单和操作权限，可视化勾选配置</p>

      <el-table :data="roles" border style="width: 100%; margin-bottom: 8px">
        <el-table-column prop="name" label="角色名称" width="140">
          <template #default="{ row }">
            <el-input v-model="row.name" placeholder="管理员" />
          </template>
        </el-table-column>
        <el-table-column label="可访问菜单" min-width="280">
          <template #default="{ row }">
            <el-button link size="small" @click="openMenuDialog(row)">
              <span v-if="row.menus.includes('*')">全部菜单</span>
              <span v-else>{{ row.menus.length }} 个菜单</span>
              （点击配置）
            </el-button>
          </template>
        </el-table-column>
        <el-table-column label="可执行操作" min-width="280">
          <template #default="{ row }">
            <el-button link size="small" @click="openActionDialog(row)">
              <span v-if="row.actions.includes('*')">全部操作</span>
              <span v-else>{{ row.actions.length }} 个操作</span>
              （点击配置）
            </el-button>
          </template>
        </el-table-column>
        <el-table-column prop="data_scope" label="数据范围" width="140">
          <template #default="{ row }">
            <el-select v-model="row.data_scope" placeholder="选择" size="small">
              <el-option label="全部数据" value="all" />
              <el-option label="仅本人" value="own" />
              <el-option label="本部门" value="dept" />
            </el-select>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" align="center">
          <template #default="{ $index }">
            <el-button type="danger" link size="small" @click="removeRole($index)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-button @click="addRole">+ 新增角色</el-button>
    </el-card>

    <!-- 菜单权限配置弹窗 -->
    <el-dialog v-model="menuDialogVisible" title="配置可访问菜单" width="500px">
      <div v-if="currentEditRole">
        <el-checkbox
          v-model="menuAllChecked"
          :indeterminate="menuIndeterminate"
          @change="handleMenuCheckAll"
        >
          全选
        </el-checkbox>
        <el-divider />
        <el-checkbox-group v-model="currentEditRole.menus">
          <div v-for="menu in availableMenus" :key="menu.value" class="checkbox-item">
            <el-checkbox :label="menu.value">{{ menu.label }}</el-checkbox>
          </div>
        </el-checkbox-group>
      </div>
      <template #footer>
        <el-button @click="menuDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveMenuConfig">确定</el-button>
      </template>
    </el-dialog>

    <!-- 操作权限配置弹窗 -->
    <el-dialog v-model="actionDialogVisible" title="配置可执行操作" width="500px">
      <div v-if="currentEditRole">
        <el-checkbox
          v-model="actionAllChecked"
          :indeterminate="actionIndeterminate"
          @change="handleActionCheckAll"
        >
          全选
        </el-checkbox>
        <el-divider />
        <el-checkbox-group v-model="currentEditRole.actions">
          <div v-for="action in availableActions" :key="action.value" class="checkbox-item">
            <el-checkbox :label="action.value">{{ action.label }}</el-checkbox>
          </div>
        </el-checkbox-group>
      </div>
      <template #footer>
        <el-button @click="actionDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveActionConfig">确定</el-button>
      </template>
    </el-dialog>

    <!-- 功能六：系统数据格式化 -->
    <el-card shadow="hover" class="card">
      <template #header>
        <div class="card-header">功能六：系统数据格式化</div>
      </template>
      <el-alert
        title="危险操作警告"
        type="error"
        description="数据格式化操作不可逆，请谨慎选择！仅用于演示/测试环境，生产环境请勿使用！"
        :closable="false"
        style="margin-bottom: 16px"
      />
      <el-form label-width="200px" class="form">
        <el-form-item label="系统数据格式化">
          <div style="display: flex; flex-direction: column; gap: 12px; width: 100%">
            <div style="display: flex; align-items: center; gap: 12px">
              <el-button type="warning" @click="handleFormatData" style="min-width: 200px">
                清空业务数据（保留基础配置）
              </el-button>
              <span class="tip" style="color: #e6a23c">
                清空：预约、订单、流水、报名、签到、通知、日志<br />
                保留：会员、场地、商品、教练、学员、课程
              </span>
            </div>
            <div style="display: flex; align-items: center; gap: 12px">
              <el-button type="danger" @click="handleFormatDataAll" style="min-width: 200px">
                完全格式化（清空所有数据）
              </el-button>
              <span class="tip" style="color: #f56c6c">
                ⚠️ 清空所有数据（包括会员、场地、商品等基础配置）<br />
                仅保留：系统设置、管理员账号
              </span>
            </div>
          </div>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import http from "@/utils/http";

interface MemberLevel {
  name: string;
  code: string;
  discount: number;
  enabled: boolean;
}

interface RoleRow {
  code: string;
  name: string;
  menus: string[];
  actions: string[];
  data_scope: string;
}

const saveLoading = ref(false);

const settings = reactive({
  basic: {
    system_name: "健身馆管理系统",
    gym_name: "XX体育馆",
    contact_phone: "",
    address: "",
  },
  business: {
    business_open_time: "06:00",
    business_close_time: "22:00",
    reservation_slot_minutes: 60,
    reservation_open_days: 7,
    reservation_cancel_limit_hours: 4,
    auto_cancel_minutes: 30,
  },
  member: {
    default_level: "normal",
  },
  order: {
    keep_days: 365,
  },
  log: {
    keep_days: 90,
  },
});

const memberLevels = ref<MemberLevel[]>([
  { name: "普通会员", code: "normal", discount: 100, enabled: true },
  { name: "银卡会员", code: "silver", discount: 95, enabled: true },
  { name: "金卡会员", code: "gold", discount: 90, enabled: true },
  { name: "VIP会员", code: "vip", discount: 85, enabled: true },
]);

const roles = ref<RoleRow[]>([
  {
    code: "super_admin",
    name: "超级管理员",
    menus: ["*"],
    actions: ["*"],
    data_scope: "all",
  },
  {
    code: "admin",
    name: "管理员",
    menus: ["dashboard", "members", "reservations", "orders", "reports"],
    actions: ["view", "create", "edit", "delete"],
    data_scope: "all",
  },
  {
    code: "staff",
    name: "前台员工",
    menus: ["dashboard", "members", "reservations"],
    actions: ["view", "create"],
    data_scope: "own",
  },
]);

// 可用菜单列表
const availableMenus = [
  { value: "dashboard", label: "数据概览" },
  { value: "members", label: "会员管理" },
  { value: "reservations", label: "场地预约" },
  { value: "courts", label: "场地管理" },
  { value: "orders", label: "订单中心" },
  { value: "products", label: "商品管理" },
  { value: "sales", label: "商品售卖" },
  { value: "transactions", label: "会员流水" },
  { value: "reports", label: "收益报表" },
  { value: "coaches", label: "教练管理" },
  { value: "students", label: "学员管理" },
  { value: "courses", label: "课程管理" },
  { value: "enrollments", label: "报名管理" },
  { value: "attendances", label: "签到管理" },
  { value: "employees", label: "员工管理" },
  { value: "notifications", label: "通知中心" },
  { value: "logs", label: "日志中心" },
  { value: "settings", label: "系统设置" },
];

// 可用操作列表
const availableActions = [
  { value: "view", label: "查看" },
  { value: "create", label: "新增" },
  { value: "edit", label: "编辑" },
  { value: "delete", label: "删除" },
  { value: "export", label: "导出" },
  { value: "import", label: "导入" },
  { value: "refund", label: "退款" },
  { value: "approve", label: "审批" },
];

// 菜单权限配置
const menuDialogVisible = ref(false);
const currentEditRole = ref<RoleRow | null>(null);
const menuAllChecked = ref(false);
const menuIndeterminate = ref(false);

// 操作权限配置
const actionDialogVisible = ref(false);
const actionAllChecked = ref(false);
const actionIndeterminate = ref(false);

// 功能三：会员等级
const addLevel = () => {
  const timestamp = Date.now();
  memberLevels.value = [
    ...memberLevels.value,
    {
      name: "",
      code: `level_${timestamp}`,
      discount: 100,
      enabled: true,
    },
  ];
};

const removeLevel = (idx: number) => {
  if (memberLevels.value.length <= 1) {
    ElMessage.warning("至少保留一个等级");
    return;
  }
  memberLevels.value = memberLevels.value.filter((_, i) => i !== idx);
};

// 功能五：角色权限
const addRole = () => {
  roles.value = [
    ...roles.value,
    {
      code: `role_${Date.now()}`,
      name: "",
      menus: [],
      actions: [],
      data_scope: "own",
    },
  ];
};

const removeRole = (idx: number) => {
  if (roles.value.length <= 1) {
    ElMessage.warning("至少保留一个角色");
    return;
  }
  roles.value = roles.value.filter((_, i) => i !== idx);
};

// 打开菜单配置弹窗
const openMenuDialog = (role: RoleRow) => {
  currentEditRole.value = role;
  updateMenuCheckState();
  menuDialogVisible.value = true;
};

// 更新菜单全选状态
const updateMenuCheckState = () => {
  if (!currentEditRole.value) return;
  const menus = currentEditRole.value.menus;
  if (menus.includes("*") || menus.length === availableMenus.length) {
    menuAllChecked.value = true;
    menuIndeterminate.value = false;
  } else if (menus.length === 0) {
    menuAllChecked.value = false;
    menuIndeterminate.value = false;
  } else {
    menuAllChecked.value = false;
    menuIndeterminate.value = true;
  }
};

// 菜单全选/取消全选
const handleMenuCheckAll = (val: boolean) => {
  if (!currentEditRole.value) return;
  if (val) {
    currentEditRole.value.menus = availableMenus.map(m => m.value);
  } else {
    currentEditRole.value.menus = [];
  }
  updateMenuCheckState();
};

// 保存菜单配置
const saveMenuConfig = () => {
  updateMenuCheckState();
  menuDialogVisible.value = false;
  ElMessage.success("菜单权限已配置");
};

// 打开操作配置弹窗
const openActionDialog = (role: RoleRow) => {
  currentEditRole.value = role;
  updateActionCheckState();
  actionDialogVisible.value = true;
};

// 更新操作全选状态
const updateActionCheckState = () => {
  if (!currentEditRole.value) return;
  const actions = currentEditRole.value.actions;
  if (actions.includes("*") || actions.length === availableActions.length) {
    actionAllChecked.value = true;
    actionIndeterminate.value = false;
  } else if (actions.length === 0) {
    actionAllChecked.value = false;
    actionIndeterminate.value = false;
  } else {
    actionAllChecked.value = false;
    actionIndeterminate.value = true;
  }
};

// 操作全选/取消全选
const handleActionCheckAll = (val: boolean) => {
  if (!currentEditRole.value) return;
  if (val) {
    currentEditRole.value.actions = availableActions.map(a => a.value);
  } else {
    currentEditRole.value.actions = [];
  }
  updateActionCheckState();
};

// 保存操作配置
const saveActionConfig = () => {
  if (!currentEditRole.value) return;
  // 如果所有操作都被选中，可以简化为 "*"（可选，根据业务需求）
  // 这里保持为具体操作列表，更清晰
  updateActionCheckState();
  actionDialogVisible.value = false;
  ElMessage.success("操作权限已配置");
};

// 加载配置
const fetchSettings = async () => {
  try {
    const res = await http.get("/system-settings/grouped");
    const data = res.data || {};

    // 功能一：基础信息
    if (data.basic) {
      Object.assign(settings.basic, data.basic);
    }

    // 功能二：营业时间与预约规则
    if (data.business) {
      settings.business.business_open_time = data.business.business_open_time || data.time?.business_open_time || settings.business.business_open_time;
      settings.business.business_close_time = data.business.business_close_time || data.time?.business_close_time || settings.business.business_close_time;
      settings.business.reservation_slot_minutes = Number(data.business.reservation_slot_minutes ?? settings.business.reservation_slot_minutes);
      settings.business.reservation_open_days = Number(data.business.reservation_open_days ?? settings.business.reservation_open_days);
      settings.business.reservation_cancel_limit_hours = Number(data.business.reservation_cancel_limit_hours ?? settings.business.reservation_cancel_limit_hours);
      settings.business.auto_cancel_minutes = Number(data.business.auto_cancel_minutes ?? settings.business.auto_cancel_minutes);
    }

    // 功能三：会员等级
    if (data.member) {
      settings.member.default_level = data.member.default_level ?? settings.member.default_level;
    }
    if (Array.isArray(data.member_levels) && data.member_levels.length > 0) {
      memberLevels.value = data.member_levels;
    }

    // 功能四：订单/日志
    if (data.order) {
      settings.order.keep_days = Number(data.order.keep_days ?? settings.order.keep_days);
    }
    if (data.log) {
      settings.log.keep_days = Number(data.log.keep_days ?? settings.log.keep_days);
    }

    // 功能五：角色权限
    if (Array.isArray(data.roles) && data.roles.length > 0) {
      roles.value = data.roles;
    }

    ElMessage.success("配置加载成功");
  } catch (err: any) {
    console.error("Failed to load settings:", err);
    ElMessage.error("加载配置失败");
  }
};

// 保存所有设置
const handleSave = async () => {
  saveLoading.value = true;
  try {
    // 数据验证和清理
    const cleanLevels = memberLevels.value.filter(l => l.name && l.code);
    const cleanRoles = roles.value.filter(r => r.code && r.name);

    if (cleanLevels.length === 0) {
      ElMessage.warning("至少需要一个会员等级");
      return;
    }

    if (cleanRoles.length === 0) {
      ElMessage.warning("至少需要一个角色");
      return;
    }

    const payload = {
      basic: settings.basic,
      business: settings.business,
      member: settings.member,
      order: settings.order,
      log: settings.log,
      member_levels: cleanLevels,
      roles: cleanRoles,
    };

    await http.post("/system-settings/batch", payload);
    
    // 如果修改了角色权限，触发权限配置更新事件
    const rolesChanged = JSON.stringify(cleanRoles) !== JSON.stringify(roles.value);
    if (rolesChanged) {
      window.dispatchEvent(new CustomEvent('roles-config-updated'));
    }
    
    ElMessage.success({
      message: "所有设置已保存！角色权限已自动更新，无需刷新页面",
      duration: 5000,
      showClose: true,
    });
    await fetchSettings();
  } catch (err: any) {
    console.error("Save failed:", err);
    const msg = err?.response?.data?.detail || "保存失败";
    ElMessage.error(msg);
  } finally {
    saveLoading.value = false;
  }
};

// 功能四：清除过期数据
const handleCleanOldData = async () => {
  try {
    await ElMessageBox.confirm(
      `将清除 ${settings.order.keep_days} 天前的订单数据和 ${settings.log.keep_days} 天前的日志数据，确定继续吗？`,
      "清除过期数据",
      {
        confirmButtonText: "确定清除",
        cancelButtonText: "取消",
        type: "warning",
      }
    );

    await http.post("/system-settings/clean-old-data", {
      order_keep_days: settings.order.keep_days,
      log_keep_days: settings.log.keep_days,
    });
    ElMessage.success("过期数据已清除");
  } catch (err: any) {
    if (err !== "cancel") {
      console.error("Clean failed:", err);
      const msg = err?.response?.data?.detail || "清除失败";
      ElMessage.error(msg);
    }
  }
};

// 功能六：系统数据格式化
const handleFormatData = async () => {
  try {
    const { value: password } = await ElMessageBox.prompt(
      "此操作将清空所有业务数据（预约、订单、流水、通知、日志等），但保留基础配置（会员、场地、商品、教练、学员、课程）。请输入您的管理员登录密码确认继续",
      "数据格式化确认",
      {
        confirmButtonText: "确定格式化",
        cancelButtonText: "取消",
        inputType: "password",
        inputPlaceholder: "请输入管理员密码",
        inputPattern: /.+/,
        inputErrorMessage: "密码不能为空",
        type: "error",
      }
    );

    // 发送密码到后端验证并执行清理
    await http.post("/system-settings/data-clean", null, {
      params: { password },
    });
    ElMessage.success("系统数据已格式化，基础配置已保留");
  } catch (err: any) {
    if (err !== "cancel" && err !== "close") {
      console.error("Format failed:", err);
      const msg = err?.response?.data?.detail || "格式化失败";
      ElMessage.error(msg);
    }
  }
};

// 功能六：完全格式化（清空所有数据）
const handleFormatDataAll = async () => {
  try {
    // 第一次确认
    await ElMessageBox.confirm(
      "⚠️ 完全格式化将清空所有数据（包括会员、场地、商品、教练、学员、课程等基础配置），仅保留系统设置和管理员账号。此操作极度危险且不可逆！",
      "完全格式化警告",
      {
        confirmButtonText: "我确定要继续",
        cancelButtonText: "取消",
        type: "error",
        dangerouslyUseHTMLString: false,
      }
    );

    // 第二次确认：输入密码
    const { value: password } = await ElMessageBox.prompt(
      "这是最后的确认。完全格式化后，所有会员、场地、商品、教练、学员、课程等基础数据将全部丢失。请输入您的管理员登录密码确认继续",
      "完全格式化最终确认",
      {
        confirmButtonText: "确定格式化",
        cancelButtonText: "取消",
        inputType: "password",
        inputPlaceholder: "请输入管理员密码",
        inputPattern: /.+/,
        inputErrorMessage: "密码不能为空",
        type: "error",
      }
    );

    // 发送密码到后端验证并执行完全清理
    await http.post("/system-settings/data-clean-all", null, {
      params: { password },
    });
    ElMessage.success("所有数据已清空（仅保留系统设置和管理员账号）");
  } catch (err: any) {
    if (err !== "cancel" && err !== "close") {
      console.error("Complete format failed:", err);
      const msg = err?.response?.data?.detail || "完全格式化失败";
      ElMessage.error(msg);
    }
  }
};

onMounted(() => {
  fetchSettings();
});
</script>

<style scoped>
.settings-page {
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
  margin-bottom: 16px;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.card-header {
  font-size: 16px;
  font-weight: 600;
  color: #1D1D1F;
}

.form {
  max-width: 800px;
}

.section {
  margin-bottom: 16px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: #1D1D1F;
  margin-bottom: 8px;
}

.section-desc {
  font-size: 12px;
  color: #86868B;
  margin-bottom: 12px;
}

.tip {
  margin-left: 8px;
  font-size: 12px;
  color: #AEAEB2;
}

.checkbox-item {
  margin-bottom: 12px;
}
</style>
