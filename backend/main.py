from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from routers import (
    auth,
    nhanvien,
    phongban,
    chucvu,
    hopdong,
    bangluong,
    thongke
)


app = FastAPI(
    title="API Quản lý nhân sự",
    description="Web API quản lý nhân sự sử dụng Python FastAPI và SQL Server",
    version="1.0.0"
)

# Thư mục giao diện nằm cùng cấp với file main.py
BASE_DIR = Path(__file__).resolve().parent
app.mount("/user", StaticFiles(directory=BASE_DIR / "user", html=True), name="user")
app.mount("/admin", StaticFiles(directory=BASE_DIR / "admin", html=True), name="admin")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# =========================
# AUTH
# =========================

app.include_router(
    auth.router,
    prefix="/api/auth",
    tags=["Đăng nhập - Đăng ký"]
)


# =========================
# NHÂN VIÊN
# =========================

app.include_router(
    nhanvien.router,
    prefix="/api/nhanvien",
    tags=["Nhân viên"]
)


# =========================
# PHÒNG BAN
# =========================

app.include_router(
    phongban.router,
    prefix="/api/phongban",
    tags=["Phòng ban"]
)


# =========================
# CHỨC VỤ
# =========================

app.include_router(
    chucvu.router,
    prefix="/api/chucvu",
    tags=["Chức vụ"]
)


# =========================
# HỢP ĐỒNG
# =========================

app.include_router(
    hopdong.router,
    prefix="/api/hopdong",
    tags=["Hợp đồng"]
)


# =========================
# BẢNG LƯƠNG
# =========================

app.include_router(
    bangluong.router,
    prefix="/api/bangluong",
    tags=["Bảng lương"]
)


# =========================
# THỐNG KÊ
# =========================

app.include_router(
    thongke.router,
    prefix="/api/thongke",
    tags=["Thống kê"]
)


@app.get("/")
def trang_chu():
    return {
        "message": "API Quản lý nhân sự đang hoạt động",
        "docs": "/docs",
        "api": {
            "auth": "/api/auth",
            "nhanvien": "/api/nhanvien",
            "phongban": "/api/phongban",
            "chucvu": "/api/chucvu",
            "hopdong": "/api/hopdong",
            "bangluong": "/api/bangluong",
            "thongke": "/api/thongke"
        }
    }