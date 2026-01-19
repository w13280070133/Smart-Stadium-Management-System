# 会员端界面概览（MEMBER_UI_OVERVIEW）

## 1. 主要页面
- 首页：路由 / 或 /home -> src/views/Home.vue，展示欢迎卡片、余额/近期概览。
- 预约列表：/reservations -> src/views/Reservations.vue，查看/创建/取消场地预约，金额自动计算。
- 我的订单：/orders -> src/views/MyOrders.vue，用于 court/course/goods/refund 订单查看与筛选。
- 课程列表/报名：/courses -> src/views/Courses.vue，查看课程/班级并报名，金额由后端折扣/卡种计算。
- 我的课程：/my-courses -> src/views/MyCourses.vue，查看已报名课程/班级，发起退款（需后端接口支持）。
- 个人中心：/center -> src/views/Center.vue，资料与近期预约/订单/报名概览。
- 个人资料：/profile（如有）或 Center 内表单，编辑手机号/密码等。

## 2. 流程：会员登录 → 预约场地 → 查看预约 → 取消预约
1) 登录：
   - 页面：/login（Login.vue）。
   - 接口：POST /member-auth/login（手机号/密码获取 token）。
   - 体验问题：登录失败提示/记住登录状态的提示较弱。

2) 预约场地：
   - 页面：/reservations（Reservations.vue）。
   - 接口：POST /member/reservations；金额与折扣由后端计算（会员卡/等级）。
   - 体验问题：折扣/计价提示有限，缺少“使用了哪张卡/折扣”醒目标记；提交后的成功反馈和跳转不够明显。

3) 查看预约：
   - 页面：/reservations 列表或 Center 页近期预约区块。
   - 接口：GET /member/reservations。
   - 体验问题：状态文案与订单状态对应关系不够直观，筛选/分页较简。

4) 取消预约：
   - 页面：/reservations 列表的取消按钮。
   - 接口：POST /member/reservations/{id}/cancel（后端生成退款订单）。
   - 体验问题：取消后的退款结果需到“我的订单”核对，缺少明确提示或跳转；预约状态与订单状态可能存在不一致。