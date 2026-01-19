"""
体育馆管理系统 V2 - FastAPI 应用入口

这是整个后端服务的主入口文件，负责：
1. 创建 FastAPI 应用实例
2. 配置 CORS 跨域访问
3. 注册所有业务模块的路由
4. 提供健康检查和调试接口

系统架构：
- 前后端分离架构
- 管理端（admin-frontend）：运行在 5173 端口
- 会员端（member-frontend）：运行在 5175 端口
- 后端 API：运行在 9000 端口

核心业务模块：
- 场地管理与预约
- 会员管理与消费
- 商品售卖
- 教培系统（课程、学员、报名、签到）
- 订单中心（统一管理所有类型订单）
- 系统设置与权限控制

技术选型：
- FastAPI：高性能异步 Web 框架
- MySQL：关系型数据库
- JWT：用户认证
- RBAC：基于角色的访问控制
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import (
    auth,
    courts,
    court_reservations,
    products,
    members,
    member_transactions,
    product_sales,
    reports,
    system_settings,
    employees,
    orders,
    audit,
    notifications,
    member_auth,
    member_portal,
    member_cards,
    # 教培模块
    coaches,
    students,
    training_courses,
    training_schedules,
    training_enrollments,
    training_attendances,
)

app = FastAPI(
    title="Gym Management System V2",
    version="1.0.0",
)

# 配置 CORS 中间件，允许前端跨域访问
# 开发环境允许 localhost 和 127.0.0.1
# 生产环境需要配置实际的域名
origins = [
    "http://localhost:5173",  # 管理端开发服务器
    "http://127.0.0.1:5173",
    "http://localhost:5174",  # 管理端开发服务器（备用端口）
    "http://127.0.0.1:5174",
    "http://localhost:5175",  # 会员端开发服务器
    "http://127.0.0.1:5175",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,  # 允许携带 Cookie
    allow_methods=["*"],     # 允许所有 HTTP 方法
    allow_headers=["*"],     # 允许所有请求头
)

# ========== 路由注册 ==========
# 所有 API 路径都以 /api 为前缀

# 管理端认证
app.include_router(auth.router, prefix="/api")

# 基础业务模块
app.include_router(courts.router, prefix="/api")
app.include_router(members.router, prefix="/api")
app.include_router(court_reservations.router, prefix="/api")
app.include_router(member_transactions.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(product_sales.router, prefix="/api")
app.include_router(reports.router, prefix="/api")

# 系统配置、员工
app.include_router(system_settings.router, prefix="/api")
app.include_router(employees.router, prefix="/api")

# 订单、审计、通知
app.include_router(orders.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")

# 会员端认证 + 会员自助服务
app.include_router(member_auth.router, prefix="/api")
app.include_router(member_portal.router, prefix="/api")
app.include_router(member_cards.router, prefix="/api")

# 教培模块（管理端）
app.include_router(coaches.router, prefix="/api")
app.include_router(students.router, prefix="/api")
app.include_router(training_courses.router, prefix="/api")
app.include_router(training_schedules.router, prefix="/api")
app.include_router(training_enrollments.router, prefix="/api")
app.include_router(training_attendances.router, prefix="/api")


# ============ 健康检查 & 调试接口 ============

@app.get("/ping")
def ping():
    """简单调试接口，用于确认后端是否存活。"""
    return {"msg": "pong"}


@app.get("/health")
def health_check():
    """给监控用的健康检查接口。"""
    return {"status": "ok"}
