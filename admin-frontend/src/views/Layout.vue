<template>
  <el-container class="admin-layout">
    <el-header class="admin-header">
      <div class="logo-area">
        <div class="logo-circle">🏟</div>
        <div class="title-block">
          <div class="system-name">体育馆管理系统</div>
          <div class="system-sub">高端简约 · 一站式运营控制台</div>
        </div>
      </div>
      <div class="user-area">
        <el-popover placement="bottom" width="420" trigger="click" @show="loadNotifications">
          <template #reference>
            <div class="notif-entry">
              <el-icon :size="20"><Bell /></el-icon>
              <span v-if="unreadCount > 0" class="notif-badge">{{ unreadCount }}</span>
            </div>
          </template>
          <div class="notif-popover" v-loading="notifLoading">
            <div class="notif-list-header">
              <span class="notif-header-title">最新通知</span>
              <div class="notif-header-actions">
                <el-button text size="small" @click="handleMarkAllRead" :disabled="unreadCount === 0">
                  一键已读
                </el-button>
                <el-button text size="small" type="primary" @click="goNotifications">查看全部</el-button>
              </div>
            </div>
            <div v-if="notifItems.length === 0" class="notif-empty">暂无新通知</div>
            <div v-else class="notif-items">
              <div
                class="notif-item"
                v-for="item in notifItems"
                :key="item.id"
                :class="{ 'notif-unread': !item.is_read }"
                @click="handleNotifClick(item)"
              >
                <div class="notif-title">
                  <el-tag size="small" :type="levelTag(item.level)" effect="plain">
                    {{ renderLevel(item.level) }}
                  </el-tag>
                  <span class="notif-text">{{ item.title }}</span>
                  <span v-if="!item.is_read" class="unread-dot"></span>
                </div>
                <div class="notif-content">{{ item.content }}</div>
                <div class="notif-time">{{ formatNotifTime(item.created_at) }}</div>
              </div>
            </div>
          </div>
        </el-popover>

        <span class="role-label">{{ currentRoleName || "角色" }}</span>
        <el-divider direction="vertical" />
        <span class="user-name">{{ displayName }}</span>
        <el-dropdown trigger="click" @command="handleCommand">
          <span class="el-dropdown-link action-link">
            账号操作
            <i class="el-icon-arrow-down el-icon--right" />
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>

    <el-container>
      <el-aside width="230px" class="admin-sider">
        <el-menu class="admin-menu" :default-active="activeMenu" router unique-opened>
          <template v-for="group in filteredMenuGroups" :key="group.code">
            <el-sub-menu :index="group.code">
              <template #title>
                <span>{{ group.title }}</span>
              </template>
              <el-menu-item v-for="item in group.children" :key="item.path" :index="item.path">
                {{ item.title }}
              </el-menu-item>
            </el-sub-menu>
          </template>
        </el-menu>
      </el-aside>

      <el-main class="admin-main">
        <div class="page-wrapper">
          <router-view />
        </div>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { Bell } from "@element-plus/icons-vue";
import http from "../utils/http";

interface MenuItem {
  code: string;
  title: string;
  path: string;
}

interface MenuGroup {
  code: string;
  title: string;
  children: MenuItem[];
}

const route = useRoute();
const router = useRouter();

const roleConfig = ref<{ code: string; name: string; menus: string[]; actions?: string[] }[]>([]);
const allowedMenus = ref<string[]>(["*"]);
const currentRole = ref<string>("");
const currentRoleName = ref<string>("");
const notifItems = ref<any[]>([]);
const unreadCount = ref(0);
const notifLoading = ref(false);

const menuGroups: MenuGroup[] = [
  {
    code: "dashboard-group",
    title: "运营总览",
    children: [{ code: "dashboard", title: "数据概览", path: "/" }],
  },
  {
    code: "court-group",
    title: "场地与预约",
    children: [
      { code: "courts", title: "场地管理", path: "/courts" },
      { code: "court-reservations", title: "场地预约", path: "/court-reservations" },
      { code: "reservations-visual", title: "预约可视化", path: "/reservations-visual" },
    ],
  },
  {
    code: "member-group",
    title: "会员管理",
    children: [
      { code: "members", title: "会员管理", path: "/members" },
      { code: "member-transactions", title: "会员流水", path: "/member-transactions" },
    ],
  },
  {
    code: "goods-group",
    title: "商品与收入",
    children: [
      { code: "products", title: "商品管理", path: "/products" },
      { code: "product-sales", title: "商品售卖", path: "/product-sales" },
      { code: "revenue-report", title: "收入报表", path: "/revenue-report" },
      { code: "orders", title: "订单中心", path: "/orders" },
    ],
  },
  {
    code: "training-group",
    title: "教培管理",
    children: [
      { code: "training-coaches", title: "教练管理", path: "/training/coaches" },
      { code: "training-students", title: "学员管理", path: "/training/students" },
      { code: "training-courses", title: "课程管理", path: "/training/courses" },
      { code: "training-enrollments", title: "报名管理", path: "/training/enrollments" },
      { code: "training-attendances", title: "签到管理", path: "/training/attendances" },
    ],
  },
  {
    code: "system-group",
    title: "系统管理",
    children: [
      { code: "employees", title: "员工管理", path: "/employees" },
      { code: "system-settings", title: "系统设置", path: "/system-settings" },
      { code: "login-logs", title: "登录日志", path: "/login-logs" },
      { code: "operation-logs", title: "操作日志", path: "/operation-logs" },
      { code: "log-center", title: "日志中心", path: "/log-center" },
    ],
  },
];

const activeMenu = computed(() => route.path);
const displayName = computed(() => {
  const name = localStorage.getItem("admin_name") || localStorage.getItem("adminName") || "admin";
  return name;
});

const filteredMenuGroups = computed(() => {
  const allowAll = allowedMenus.value.includes("*");
  return menuGroups
    .map((g) => ({
      ...g,
      children: g.children.filter((item) => allowAll || allowedMenus.value.includes(item.code)),
    }))
    .filter((g) => g.children.length > 0);
});

const applyRolePermission = (role: string) => {
  if (!role) {
    allowedMenus.value = ["*"];
    currentRoleName.value = "";
    localStorage.setItem("allowed_menus", JSON.stringify(["*"]));
    localStorage.setItem("allowed_actions", JSON.stringify(["*"]));
    return;
  }
  
  // 超级管理员（角色代码为 "super_admin"）始终拥有全部权限
  if (role === "super_admin") {
    allowedMenus.value = ["*"];
    currentRoleName.value = "超级管理员";
    localStorage.setItem("allowed_menus", JSON.stringify(["*"]));
    localStorage.setItem("admin_role_name", "超级管理员");
    localStorage.setItem("allowed_actions", JSON.stringify(["*"]));
    return;
  }
  
  // 其他角色根据配置获取权限
  const found = roleConfig.value.find((r) => r.code === role);
  if (found) {
    // 如果 menus 是数组，直接使用（包括空数组和包含 "*" 的情况）
    let menus: string[];
    if (Array.isArray(found.menus)) {
      if (found.menus.length === 0) {
        // 空数组表示没有任何菜单权限
        menus = [];
      } else if (found.menus.includes("*")) {
        menus = ["*"];
      } else {
        menus = found.menus;
      }
    } else {
      // 不是数组，默认给全部权限（向后兼容）
      menus = ["*"];
    }
    
    // 同样的逻辑处理 actions
    let actions: string[];
    if (Array.isArray(found.actions)) {
      if (found.actions.length === 0) {
        actions = [];
      } else if (found.actions.includes("*")) {
        actions = ["*"];
      } else {
        actions = found.actions;
      }
    } else {
      actions = ["*"];
    }
    
    allowedMenus.value = menus;
    currentRoleName.value = found.name || role;
    localStorage.setItem("allowed_menus", JSON.stringify(menus));
    localStorage.setItem("admin_role_name", found.name || role);
    localStorage.setItem("allowed_actions", JSON.stringify(actions));
  } else {
    // 如果找不到角色配置，默认给全部权限（向后兼容，避免新角色无法访问）
    allowedMenus.value = ["*"];
    currentRoleName.value = role;
    localStorage.setItem("allowed_menus", JSON.stringify(["*"]));
    localStorage.setItem("allowed_actions", JSON.stringify(["*"]));
  }
};

const loadRoleConfig = async () => {
  try {
    const res = await http.get("/system-settings/roles-config");
    const roles = res.data?.roles || [];
    roleConfig.value = roles;
    const userStr = localStorage.getItem("user");
    const user = userStr ? JSON.parse(userStr) : null;
    currentRole.value = user?.role || "";
    applyRolePermission(currentRole.value);
  } catch (e) {
    allowedMenus.value = ["*"];
  }
};

const levelTag = (level?: string) => {
  if (!level) return "info";
  if (level === "warning") return "warning";
  if (level === "error" || level === "danger") return "danger";
  return "info";
};

const renderLevel = (level?: string) => {
  if (level === "warning") return "警告";
  if (level === "error" || level === "danger") return "错误";
  return "提示";
};

const loadNotifications = async () => {
  notifLoading.value = true;
  try {
    const res = await http.get("/notifications", {
      params: { page: 1, page_size: 10, is_read: 0 },
    });
    const data = res.data || {};
    notifItems.value = Array.isArray(data.items) ? data.items : [];
    unreadCount.value = Number(data.total || 0);
  } catch (e) {
    notifItems.value = [];
    unreadCount.value = 0;
  } finally {
    notifLoading.value = false;
  }
};

const formatNotifTime = (dt: string | null | undefined) => {
  if (!dt) return "";
  return dt.replace("T", " ").slice(0, 19);
};

const handleNotifClick = async (item: any) => {
  if (!item.is_read) {
    try {
      await http.put(`/notifications/${item.id}/read`);
      await loadNotifications();
    } catch (e) {
      console.error("标记已读失败", e);
    }
  }
};

const handleMarkAllRead = async () => {
  try {
    await http.put("/notifications/read-all");
    ElMessage.success("全部通知已标记为已读");
    await loadNotifications();
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || "操作失败");
  }
};

const goNotifications = () => {
  router.push("/notifications");
};

const handleCommand = (command: string) => {
  if (command === "logout") {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    localStorage.removeItem("admin_name");
    localStorage.removeItem("adminName");
    localStorage.removeItem("admin_role_name");
    localStorage.removeItem("allowed_menus");
    localStorage.removeItem("allowed_actions");
    router.push("/login");
  }
};

onMounted(() => {
  loadRoleConfig();
  loadNotifications();
  
  // 监听权限配置更新事件
  window.addEventListener('roles-config-updated', () => {
    loadRoleConfig();
  });
});
</script>

<style scoped>
/* ========== Apple iOS 风格浅色主题 ========== */
.admin-layout {
  min-height: 100vh;
  background: var(--gs-color-background);
  color: var(--gs-color-text);
}

/* ========== 顶部导航栏 ========== */
.admin-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 64px;
  background: rgba(255, 255, 255, 0.92);
  border-bottom: 1px solid var(--gs-color-border);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  position: sticky;
  top: 0;
  z-index: 100;
}

.logo-area {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo-circle {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: var(--gs-color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
}

.title-block .system-name {
  font-size: 17px;
  font-weight: 600;
  color: var(--gs-color-text);
  letter-spacing: -0.02em;
}

.title-block .system-sub {
  font-size: 12px;
  color: var(--gs-color-text-secondary);
  margin-top: 2px;
}

/* ========== 用户区域 ========== */
.user-area {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 14px;
  color: var(--gs-color-text-secondary);
}

.role-label {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 6px;
  background: var(--gs-color-background);
  color: var(--gs-color-text-secondary);
  font-weight: 500;
}

.user-name {
  font-weight: 600;
  color: var(--gs-color-text);
}

.action-link {
  cursor: pointer;
  font-size: 14px;
  color: var(--gs-color-primary);
  transition: opacity 0.2s;
}

.action-link:hover {
  opacity: 0.7;
}

/* ========== 通知按钮 ========== */
.notif-entry {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  color: var(--gs-color-text-secondary);
  cursor: pointer;
  transition: background 0.2s;
}

.notif-entry:hover {
  background: var(--gs-color-background);
  color: var(--gs-color-text);
}

.notif-badge {
  position: absolute;
  top: 0;
  right: 0;
  background: var(--gs-color-danger);
  color: #fff;
  border-radius: 10px;
  padding: 0 5px;
  font-size: 11px;
  font-weight: 600;
  min-width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* ========== 通知弹出框 ========== */
.notif-popover {
  max-height: 400px;
  overflow: auto;
}

.notif-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 12px;
  margin-bottom: 12px;
  border-bottom: 1px solid var(--gs-color-border);
}

.notif-header-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--gs-color-text);
}

.notif-header-actions {
  display: flex;
  gap: 8px;
}

.notif-empty {
  text-align: center;
  color: var(--gs-color-text-secondary);
  padding: 32px 0;
  font-size: 14px;
}

.notif-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.notif-item {
  padding: 12px;
  border-radius: 10px;
  background: var(--gs-color-background);
  cursor: pointer;
  transition: background 0.2s;
}

.notif-item:hover {
  background: #E5E5EA;
}

.notif-item.notif-unread {
  background: rgba(0, 122, 255, 0.08);
}

.notif-item.notif-unread:hover {
  background: rgba(0, 122, 255, 0.12);
}

.notif-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 14px;
  color: var(--gs-color-text);
}

.notif-text {
  flex: 1;
}

.unread-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--gs-color-primary);
  flex-shrink: 0;
}

.notif-content {
  color: var(--gs-color-text-secondary);
  font-size: 13px;
  margin-top: 6px;
  line-height: 1.5;
}

.notif-time {
  color: var(--gs-color-text-tertiary);
  font-size: 12px;
  margin-top: 6px;
}

/* ========== 侧边栏 ========== */
.admin-sider {
  background: #fff;
  border-right: 1px solid var(--gs-color-border);
}

.admin-menu {
  border-right: none;
  padding: 8px 0;
  background: transparent;
}

.admin-menu :deep(.el-sub-menu__title) {
  height: 44px;
  line-height: 44px;
  font-size: 13px;
  font-weight: 600;
  color: var(--gs-color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.admin-menu :deep(.el-menu-item) {
  height: 40px;
  line-height: 40px;
  font-size: 14px;
  border-radius: 8px;
  margin: 2px 8px;
  color: var(--gs-color-text);
  transition: background 0.2s;
}

.admin-menu :deep(.el-menu-item:hover) {
  background: var(--gs-color-background);
}

.admin-menu :deep(.el-menu-item.is-active) {
  background: var(--gs-color-primary);
  color: #fff;
  font-weight: 500;
}

/* ========== 主内容区 ========== */
.admin-main {
  padding: 24px;
  background: var(--gs-color-background);
  min-height: calc(100vh - 64px);
}

.page-wrapper {
  max-width: 1400px;
  margin: 0 auto;
}
</style>
