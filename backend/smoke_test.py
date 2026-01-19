import requests

BASE = "http://127.0.0.1:9000"
ADMIN_TOKEN = "在这里粘贴后台登录后的 token"
MEMBER_TOKEN = "在这里粘贴会员端登录后的 token"


def check(path, name="", token=None):
    url = BASE + path
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        ok = 200 <= resp.status_code < 300
        print(f"[{'OK' if ok else 'FAIL'}] {name or path} -> {resp.status_code}")
        if not ok:
            print(resp.text[:200])
    except Exception as e:
        print(f"[ERR] {name or path}: {e}")


def main():
    print("=== 基础健康检查 ===")
    check("/health", "健康检查")

    print("\n=== 后台管理端接口 ===")
    check("/api/reports/overview", "后台-数据总览", ADMIN_TOKEN)
    check("/api/courts", "后台-场地列表", ADMIN_TOKEN)
    check("/api/members", "后台-会员列表", ADMIN_TOKEN)
    check("/api/products", "后台-商品列表", ADMIN_TOKEN)
    check("/api/training-courses", "后台-培训课程列表", ADMIN_TOKEN)
    check("/api/system-settings/grouped", "后台-系统设置", ADMIN_TOKEN)
    check("/api/orders?page=1&page_size=10", "后台-订单中心", ADMIN_TOKEN)
    check("/api/audit/login-logs?page=1&page_size=10", "后台-登录日志", ADMIN_TOKEN)

    print("\n=== 会员端接口 ===")
    check("/api/member/profile", "会员-个人资料", MEMBER_TOKEN)
    check("/api/member/overview", "会员-首页概览", MEMBER_TOKEN)
    check("/api/member/reservations?limit=5", "会员-近期预约", MEMBER_TOKEN)
    check("/api/member/orders?limit=5", "会员-我的订单", MEMBER_TOKEN)
    check("/api/member/courts", "会员-可预约场地", MEMBER_TOKEN)
    check("/api/member/courses", "会员-可报名课程", MEMBER_TOKEN)


if __name__ == "__main__":
    main()
