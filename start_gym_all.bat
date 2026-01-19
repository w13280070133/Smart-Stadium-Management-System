@echo off
setlocal

REM === 改这里：你的项目根目录 ===
set BASE=D:\GymSystemV2

REM === 后端：FastAPI ===
start "Backend - FastAPI" cmd /k ^
 "cd /d %BASE%\backend && call venv\Scripts\activate.bat && uvicorn app.main:app --reload --host 0.0.0.0 --port 9000"

REM === 管理端前端 ===
start "Admin Frontend" cmd /k ^
 "cd /d %BASE%\admin-frontend && npm run dev -- --host 0.0.0.0 --port 5173"

REM === 会员端前端 ===
start "Member Frontend" cmd /k ^
 "cd /d %BASE%\member-frontend && npm run dev -- --host 0.0.0.0 --port 5175"

endlocal
exit /b
