import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router";
import Layout from "@/views/Layout.vue";
import Login from "@/views/Login.vue";
import Home from "@/views/Home.vue";
import Reservations from "@/views/Reservations.vue";
import Orders from "@/views/Orders.vue";
import AccountSettings from "@/views/AccountSettings.vue";
import Center from "@/views/Center.vue"; // 新增：个人信息页面
import { getMemberToken } from "@/utils/auth";

// 会员端路由配置
const routes: Array<RouteRecordRaw> = [
  // 登录页
  {
    path: "/login",
    name: "Login",
    component: Login,
    meta: {
      title: "会员登录",
    },
  },
  // 会员端主框架（Layout 包含顶部导航 / 底部等）
  {
    path: "/",
    component: Layout,
    children: [
      // 访问根路径时，重定向到 /home
      {
        path: "",
        redirect: "/home",
      },
      {
        path: "home",
        name: "Home",
        component: Home,
        meta: {
          title: "首页",
          requiresAuth: true,
        },
      },
      {
        path: "reservations",
        name: "Reservations",
        component: Reservations,
        meta: {
          title: "场地预约",
          requiresAuth: true,
        },
      },
        {
          path: "orders",
          name: "Orders",
          component: () => import("../views/MyOrders.vue"),
          meta: {
            title: "我的订单",
            requiresAuth: true,
          },
        },
      {
        path: "notifications",
        name: "MemberNotifications",
        component: () => import("../views/Notifications.vue"),
        meta: {
          title: "消息通知",
          requiresAuth: true,
        },
      },
      // 个人信息编辑页
      {
        path: "center",
        name: "Center",
        component: Center,
        meta: {
          title: "个人信息",
          requiresAuth: true,
        },
      },
      // 账号设置（修改密码）
      {
        path: "account",
        name: "AccountSettings",
        component: AccountSettings,
        meta: {
          title: "账号设置",
          requiresAuth: true,
        },
      },
    ],
  },
  // 兜底：找不到路由时回到首页
  {
    path: "/:pathMatch(.*)*",
    redirect: "/home",
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// 简单登录守卫
router.beforeEach((to, from, next) => {
  const token = getMemberToken?.();

  // 已登录情况下访问 /login，则直接跳到首页
  if (to.path === "/login") {
    if (token) {
      next("/home");
    } else {
      next();
    }
    return;
  }

  // 其他页面，如果需要登录且没有 token，则跳到登录页
  if (to.meta?.requiresAuth && !token) {
    next("/login");
    return;
  }

  // 其余情况正常放行
  next();
});

export default router;
