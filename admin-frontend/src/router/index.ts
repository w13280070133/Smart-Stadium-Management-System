// src/router/index.ts
import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";
import { ElMessage } from "element-plus";

import Login from "../views/Login.vue";
import Layout from "../views/Layout.vue";
import Dashboard from "../views/Dashboard.vue";

const routes: RouteRecordRaw[] = [
  {
    path: "/login",
    name: "Login",
    component: Login,
    meta: { public: true, title: "管理后台登录" },
  },
  {
    path: "/",
    component: Layout,
    children: [
      {
        path: "",
        name: "Dashboard",
        component: Dashboard,
        meta: { title: "数据概览", menuCode: "dashboard" },
      },
      {
        path: "courts",
        name: "Courts",
        component: () => import("../views/Courts.vue"),
        meta: { title: "场地管理", menuCode: "courts" },
      },
      {
        path: "court-reservations",
        name: "CourtReservations",
        component: () => import("../views/CourtReservations.vue"),
        meta: { title: "场地预约", menuCode: "court-reservations" },
      },
      {
        path: "reservations-visual",
        name: "ReservationCalendar",
        component: () => import("../views/ReservationCalendar.vue"),
        meta: { title: "预约可视化", menuCode: "reservations-visual" },
      },
      {
        path: "members",
        name: "Members",
        component: () => import("../views/Members.vue"),
        meta: { title: "会员管理", menuCode: "members" },
      },
      // 原来的 member-cards 路由已删除
      {
        path: "member-transactions",
        name: "MemberTransactions",
        component: () => import("../views/MemberTransactions.vue"),
        meta: { title: "会员流水", menuCode: "member-transactions" },
      },
      {
        path: "products",
        name: "Products",
        component: () => import("../views/Products.vue"),
        meta: { title: "商品管理", menuCode: "products" },
      },
      {
        path: "product-sales",
        name: "ProductSales",
        component: () => import("../views/ProductSales.vue"),
        meta: { title: "商品售卖", menuCode: "product-sales" },
      },
      {
        path: "revenue-report",
        name: "RevenueReport",
        component: () => import("../views/RevenueReport.vue"),
        meta: { title: "收入报表", menuCode: "revenue-report" },
      },
      {
        path: "orders",
        name: "Orders",
        component: () => import("../views/finance/Orders.vue"),
        meta: { title: "订单中心", menuCode: "orders" },
      },
      {
        path: "employees",
        name: "Employees",
        component: () => import("../views/Employees.vue"),
        meta: { requiresRole: "admin", title: "员工管理", menuCode: "employees" },
      },
      {
        path: "system-settings",
        name: "SystemSettings",
        component: () => import("../views/SettingsCenter.vue"),
        meta: { requiresRole: "admin", title: "系统设置", menuCode: "system-settings" },
      },
      {
        path: "notifications",
        name: "Notifications",
        component: () => import("../views/system/Notifications.vue"),
        meta: { title: "通知中心", menuCode: "notifications" },
      },
      {
        path: "login-logs",
        name: "LoginLogs",
        component: () => import("../views/audit/LoginLogs.vue"),
        meta: { requiresRole: "admin", title: "登录日志", menuCode: "login-logs" },
      },
      {
        path: "operation-logs",
        name: "OperationLogs",
        component: () => import("../views/audit/OperationLogs.vue"),
        meta: { requiresRole: "admin", title: "操作日志", menuCode: "operation-logs" },
      },
      {
        path: "log-center",
        name: "LogCenter",
        component: () => import("../views/system/LogCenter.vue"),
        meta: { requiresRole: "admin", title: "日志中心", menuCode: "log-center" },
      },
      // 教培模块
      {
        path: "training/coaches",
        name: "TrainingCoaches",
        component: () => import("../views/training/Coaches.vue"),
        meta: { title: "教练管理", menuCode: "training-coaches" },
      },
      {
        path: "training/students",
        name: "TrainingStudents",
        component: () => import("../views/training/Students.vue"),
        meta: { title: "学员管理", menuCode: "training-students" },
      },
      {
        path: "training/courses",
        name: "TrainingCourses",
        component: () => import("../views/training/Courses.vue"),
        meta: { title: "课程管理", menuCode: "training-courses" },
      },
      {
        path: "training/enrollments",
        name: "TrainingEnrollments",
        component: () => import("../views/training/Enrollments.vue"),
        meta: { title: "报名管理", menuCode: "training-enrollments" },
      },
      {
        path: "training/attendances",
        name: "TrainingAttendances",
        component: () => import("../views/training/Attendances.vue"),
        meta: { title: "签到管理", menuCode: "training-attendances" },
      },
    ],
  },
  { path: "/:pathMatch(.*)*", redirect: "/" },
];

const router = createRouter({ history: createWebHistory(), routes });

router.beforeEach((to, _from, next) => {
  const meta = (to.meta || {}) as any;
  const isPublic = meta.public;
  const token = localStorage.getItem("token");
  const userStr = localStorage.getItem("user");
  const user = userStr ? JSON.parse(userStr) : null;
  const allowedMenusStr = localStorage.getItem("allowed_menus");
  const allowedMenus: string[] = allowedMenusStr ? JSON.parse(allowedMenusStr) : ["*"];

  if (!isPublic && !token) return next({ path: "/login" });
  if (to.path === "/login" && token) return next({ path: "/" });

  const requireRole = meta.requiresRole;
  if (requireRole) {
    // 超级管理员（super_admin）拥有所有权限，包括需要 admin 角色的页面
    if (user?.role !== requireRole && user?.role !== "super_admin") {
      ElMessage.error("权限不足，无法访问该页面");
      return next({ path: "/" });
    }
  }

  const menuCode = meta.menuCode;
  const allowAll = allowedMenus.includes("*");
  if (menuCode && !allowAll && !allowedMenus.includes(menuCode)) {
    ElMessage.error("当前角色不可访问该菜单");
    return next({ path: "/" });
  }

  next();
});

export default router;
