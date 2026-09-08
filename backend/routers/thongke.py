from fastapi import APIRouter, HTTPException
from database import get_connection

router = APIRouter()


# Tổng quan
@router.get("/tong-quan")
def tong_quan():
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM NhanVien")
        tong_nhan_vien = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM NhanVien WHERE TrangThai = 1"
        )
        nhan_vien_dang_lam = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM PhongBan")
        tong_phong_ban = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM ChucVu")
        tong_chuc_vu = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM HopDong WHERE TrangThai = 1"
        )
        hop_dong_dang_hieu_luc = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT ISNULL(SUM(
                LuongCoBan + PhuCap + Thuong - KhauTru
            ), 0)
            FROM BangLuong
            WHERE Thang = MONTH(GETDATE())
              AND Nam = YEAR(GETDATE())
            """
        )

        tong_luong_thang_nay = cursor.fetchone()[0]

        return {
            "tongNhanVien": tong_nhan_vien,
            "nhanVienDangLam": nhan_vien_dang_lam,
            "tongPhongBan": tong_phong_ban,
            "tongChucVu": tong_chuc_vu,
            "hopDongDangHieuLuc": hop_dong_dang_hieu_luc,
            "tongLuongThangNay": float(tong_luong_thang_nay or 0)
        }

    finally:
        conn.close()


# Nhân viên theo phòng ban
@router.get("/nhan-vien-theo-phong-ban")
def nhan_vien_theo_phong_ban():
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                pb.MaPhongBan,
                pb.TenPhongBan,
                COUNT(nv.MaNhanVien) AS SoNhanVien
            FROM PhongBan pb
            LEFT JOIN NhanVien nv
                ON pb.MaPhongBan = nv.MaPhongBan
            GROUP BY
                pb.MaPhongBan,
                pb.TenPhongBan
            ORDER BY pb.MaPhongBan
            """
        )

        data = []

        for row in cursor.fetchall():
            data.append({
                "MaPhongBan": row.MaPhongBan,
                "TenPhongBan": row.TenPhongBan,
                "SoNhanVien": row.SoNhanVien
            })

        return {
            "data": data
        }

    finally:
        conn.close()


# Lương theo phòng ban
@router.get("/luong-theo-phong-ban")
def luong_theo_phong_ban():
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                pb.MaPhongBan,
                pb.TenPhongBan,
                ISNULL(
                    SUM(
                        bl.LuongCoBan
                        + bl.PhuCap
                        + bl.Thuong
                        - bl.KhauTru
                    ),
                    0
                ) AS TongLuong
            FROM PhongBan pb
            LEFT JOIN NhanVien nv
                ON pb.MaPhongBan = nv.MaPhongBan
            LEFT JOIN BangLuong bl
                ON nv.MaNhanVien = bl.MaNhanVien
            GROUP BY
                pb.MaPhongBan,
                pb.TenPhongBan
            ORDER BY pb.MaPhongBan
            """
        )

        data = []

        for row in cursor.fetchall():
            data.append({
                "MaPhongBan": row.MaPhongBan,
                "TenPhongBan": row.TenPhongBan,
                "TongLuong": float(row.TongLuong or 0)
            })

        return {
            "data": data
        }

    finally:
        conn.close()


# Dashboard tổng hợp
@router.get("/dashboard")
def dashboard():
    conn = get_connection()

    try:
        cursor = conn.cursor()

        # Tổng nhân viên
        cursor.execute("SELECT COUNT(*) FROM NhanVien")
        tong_nhan_vien = cursor.fetchone()[0]

        # Nhân viên đang làm
        cursor.execute(
            "SELECT COUNT(*) FROM NhanVien WHERE TrangThai = 1"
        )
        dang_lam = cursor.fetchone()[0]

        # Phòng ban
        cursor.execute("SELECT COUNT(*) FROM PhongBan")
        tong_phong_ban = cursor.fetchone()[0]

        # Chức vụ
        cursor.execute("SELECT COUNT(*) FROM ChucVu")
        tong_chuc_vu = cursor.fetchone()[0]

        # Hợp đồng
        cursor.execute(
            "SELECT COUNT(*) FROM HopDong WHERE TrangThai = 1"
        )
        hop_dong = cursor.fetchone()[0]

        # Tổng lương tháng hiện tại
        cursor.execute(
            """
            SELECT ISNULL(
                SUM(
                    LuongCoBan
                    + PhuCap
                    + Thuong
                    - KhauTru
                ), 0
            )
            FROM BangLuong
            WHERE Thang = MONTH(GETDATE())
              AND Nam = YEAR(GETDATE())
            """
        )

        tong_luong = cursor.fetchone()[0]

        return {
            "tongNhanVien": tong_nhan_vien,
            "dangLam": dang_lam,
            "tongPhongBan": tong_phong_ban,
            "tongChucVu": tong_chuc_vu,
            "hopDong": hop_dong,
            "tongLuong": float(tong_luong or 0)
        }

    finally:
        conn.close()