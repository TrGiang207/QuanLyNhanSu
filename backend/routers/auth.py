from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database import get_connection


router = APIRouter()


class LoginModel(BaseModel):
    TenDangNhap: str
    MatKhau: str


@router.post("/login")
def login(data: LoginModel):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                MaTaiKhoan,
                MaNhanVien,
                TenDangNhap,
                VaiTro,
                TrangThai
            FROM TaiKhoan
            WHERE TenDangNhap = ?
            AND MatKhau = ?
        """,
            data.TenDangNhap,
            data.MatKhau
        )

        row = cursor.fetchone()

        if row is None:
            raise HTTPException(
                status_code=401,
                detail="Tên đăng nhập hoặc mật khẩu không đúng"
            )

        # TrangThai trong SQL là BIT
        if not row.TrangThai:
            raise HTTPException(
                status_code=403,
                detail="Tài khoản đã bị khóa"
            )

        return {
            "message": "Đăng nhập thành công",
            "MaTaiKhoan": row.MaTaiKhoan,
            "MaNhanVien": row.MaNhanVien,
            "TenDangNhap": row.TenDangNhap,
            "VaiTro": row.VaiTro,
            "TrangThai": row.TrangThai
        }

    finally:
        conn.close()


class RegisterModel(BaseModel):
    MaNhanVien: int | None = None
    TenDangNhap: str
    MatKhau: str


@router.post("/register")
def register(data: RegisterModel):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        # Kiểm tra tên đăng nhập
        cursor.execute("""
            SELECT 1
            FROM TaiKhoan
            WHERE TenDangNhap = ?
        """, data.TenDangNhap)

        if cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail="Tên đăng nhập đã tồn tại"
            )

        # Nếu có mã nhân viên thì kiểm tra nhân viên
        if data.MaNhanVien is not None:
            cursor.execute("""
                SELECT 1
                FROM NhanVien
                WHERE MaNhanVien = ?
            """, data.MaNhanVien)

            if cursor.fetchone() is None:
                raise HTTPException(
                    status_code=400,
                    detail="Mã nhân viên không tồn tại"
                )

        cursor.execute("""
            INSERT INTO TaiKhoan
            (
                MaNhanVien,
                TenDangNhap,
                MatKhau,
                VaiTro,
                TrangThai
            )
            VALUES (?, ?, ?, 'User', 1)
        """,
            data.MaNhanVien,
            data.TenDangNhap,
            data.MatKhau
        )

        conn.commit()

        return {
            "message": "Đăng ký tài khoản thành công"
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Lỗi đăng ký: {e}"
        )

    finally:
        conn.close()