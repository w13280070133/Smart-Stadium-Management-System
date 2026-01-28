# 管理端前端 (Admin Frontend)

健身房管理系统的管理后台，基于 Vue 3 + TypeScript + Element Plus 构建。

## 技术栈

- Vue 3.4 + Composition API
- TypeScript 5
- Vite 5
- Element Plus 2
- Pinia 状态管理
- Vue Router 4

## 开发启动

```bash
npm install
npm run dev
```

访问 http://localhost:5173

## 构建部署

```bash
npm run build
```

构建产物在 `dist/` 目录

## 主要页面

| 路由 | 页面 | 说明 |
|------|------|------|
| / | Dashboard | 数据概览仪表盘 |
| /courts | Courts | 场地管理 |
| /court-reservations | CourtReservations | 场地预约管理 |
| /members | Members | 会员管理 |
| /products | Products | 商品管理 |
| /product-sales | ProductSales | 商品售卖/收银 |
| /orders | Orders | 订单中心 |
| /employees | Employees | 员工管理 |
| /system-settings | SettingsCenter | 系统设置 |

## 目录结构

```
src/
├── views/          # 页面组件
├── router/         # 路由配置
├── stores/         # Pinia 状态
├── utils/          # 工具函数
├── theme/          # 主题样式
└── App.vue         # 根组件
```
