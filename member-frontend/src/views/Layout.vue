<template>
  <el-container class="member-layout">
    <!-- 顶部栏 -->
    <el-header class="member-header">
      <div class="logo-area">
        <div class="logo-circle">
          <span class="logo-text">🏸</span>
        </div>
        <div class="title-block">
          <div class="system-name">会员自助服务</div>
          <div class="system-sub">自助预约场地 · 查看订单 · 管理账号</div>
        </div>
      </div>
      <div class="user-area">
        <span class="user-name">{{ displayName }}</span>
        <el-divider direction="vertical" />
        <el-button type="text" @click="handleLogout">退出登录</el-button>
      </div>
    </el-header>

    <!-- 左侧菜单 + 右侧内容 -->
    <el-container>
      <el-aside width="200px" class="member-sider">
        <el-menu
          class="member-menu"
          :default-active="activeMenu"
          router
        >
          <el-menu-item index="/home">
            <span>个人中心</span>
          </el-menu-item>
          <el-menu-item index="/reservations">
            <span>我的预约</span>
          </el-menu-item>
          <el-menu-item index="/orders">
            <span>我的订单</span>
          </el-menu-item>
          <el-menu-item index="/notifications">
            <span>消息通知</span>
          </el-menu-item>
          <el-menu-item index="/account">
            <span>账号设置</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <el-main class="member-main">
        <div class="page-wrapper">
          <router-view />
        </div>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

const route = useRoute();
const router = useRouter();

const activeMenu = computed(() => {
  return route.path.startsWith("/") ? route.path : `/${route.path}`;
});

const displayName = computed(() => {
  const name =
    localStorage.getItem("member_name") ||
    localStorage.getItem("memberName") ||
    "";
  const cardNo =
    localStorage.getItem("member_card_no") ||
    localStorage.getItem("memberCardNo") ||
    "";
  if (name && cardNo) {
    return `${name} (${cardNo})`;
  }
  if (name) return name;
  return "会员用户";
});

const handleLogout = () => {
  localStorage.clear();
  router.push("/login");
};
</script>

<style scoped>
.member-layout {
  height: 100vh;
}

/* 顶部条 */
.member-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  border-bottom: 1px solid #ebeef5;
  background-color: #ffffff;
}

.logo-area {
  display: flex;
  align-items: center;
}

.logo-circle {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  background: linear-gradient(135deg, #409eff, #36cfc9);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  margin-right: 12px;
  font-size: 20px;
}

.title-block .system-name {
  font-size: 18px;
  font-weight: 600;
}

.title-block .system-sub {
  font-size: 12px;
  color: #909399;
}

.user-area {
  display: flex;
  align-items: center;
  font-size: 14px;
  color: #606266;
}

.user-name {
  margin-right: 4px;
}

/* 左侧菜单 */
.member-sider {
  background-color: #f8fafc;
  border-right: 1px solid #ebeef5;
}

.member-menu {
  border-right: none;
}

.member-menu :deep(.el-menu-item) {
  height: 44px;
  line-height: 44px;
}

/* 右侧主内容区：浅灰背景 + 内边距 */
.member-main {
  padding: 16px 20px 24px;
  background-color: #f5f7fb;
}

.page-wrapper {
  min-height: calc(100vh - 60px);
}
</style>
