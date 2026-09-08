from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from database import get_connection

router = APIRouter()


class NhanVienModel(BaseModel):
    # Khớp chính xác tên cột trong SQL Server
    MaNV: str = Field(..., min_length=1, max_length=20)
    HoTen: str = Field(..., min_length=1, max_length=100)
    NgaySinh: Optional[date] = None
    GioiTinh: Optional[str] = Field(default=None, max_length=10)
    SoDienThoai: Optional[str] = Field(default=None, max_length=20)
    Email: Optional[str] = Field(default=None, max_length=120)
    DiaChi: Optional[str] = Field(default=None, max_length=255)
    NgayVaoLam: Optional[date] = None
    MaPhongBan: Optional[int] = None
    MaChucVu: Optional[int] = None
    LuongCoBan: Decimal = Field(default=Decimal("0"), ge=0)
    TrangThai: bool = True


class NhanVienResponse(NhanVienModel):
    MaNhanVien: int
    TenPhongBan: Optional[str] = None
    TenChucVu: Optional[str] = None


def row_to_dict(row):
    return {
        "MaNhanVien": row[0],
        "MaNV": row[1],
        "HoTen": row[2],
        "NgaySinh": row[3],
        "GioiTinh": row[4],
        "SoDienThoai": row[5],
        "Email": row[6],
        "DiaChi": row[7],
        "NgayVaoLam": row[8],
        "MaPhongBan": row[9],
        "TenPhongBan": row[10],
        "MaChucVu": row[11],
        "TenChucVu": row[12],
        "LuongCoBan": row[13] or Decimal("0"),
        "TrangThai": bool(row[14]) if row[14] is not None else True,
    }


SELECT_SQL = """
    SELECT
        nv.MaNhanVien,
        nv.MaNV,
        nv.HoTen,
        nv.NgaySinh,
        nv.GioiTinh,
        nv.SoDienThoai,
        nv.Email,
        nv.DiaChi,
        nv.NgayVaoLam,
        nv.MaPhongBan,
        pb.TenPhongBan,
        nv.MaChucVu,
        cv.TenChucVu,
        nv.LuongCoBan,
        nv.TrangThai
    FROM NhanVien nv
    LEFT JOIN PhongBan pb ON nv.MaPhongBan = pb.MaPhongBan
    LEFT JOIN ChucVu cv ON nv.MaChucVu = cv.MaChucVu
"""


def check_foreign_keys(cursor, data):
    if data.MaPhongBan is not None:
        cursor.execute("SELECT 1 FROM PhongBan WHERE MaPhongBan = ?", data.MaPhongBan)
        if cursor.fetchone() is None:
            raise HTTPException(status_code=400, detail="Mã phòng ban không tồn tại")

    if data.MaChucVu is not None:
        cursor.execute("SELECT 1 FROM ChucVu WHERE MaChucVu = ?", data.MaChucVu)
        if cursor.fetchone() is None:
            raise HTTPException(status_code=400, detail="Mã chức vụ không tồn tại")


@router.get("/")
def get_nhan_vien(
    keyword: str = Query("", description="Tìm theo mã, họ tên, điện thoại, email, phòng ban, chức vụ"),
    trang_thai: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        where = " WHERE 1=1 "
        params = []

        if keyword.strip():
            where += " AND (nv.MaNV LIKE ? OR nv.HoTen LIKE ? OR nv.SoDienThoai LIKE ? OR nv.Email LIKE ? OR pb.TenPhongBan LIKE ? OR cv.TenChucVu LIKE ?) "
            value = f"%{keyword.strip()}%"
            params.extend([value] * 6)

        if trang_thai is not None:
            where += " AND nv.TrangThai = ? "
            params.append(trang_thai)

        cursor.execute("""
            SELECT COUNT(*)
            FROM NhanVien nv
            LEFT JOIN PhongBan pb ON nv.MaPhongBan = pb.MaPhongBan
            LEFT JOIN ChucVu cv ON nv.MaChucVu = cv.MaChucVu
        """ + where, *params)
        total = cursor.fetchone()[0]
        offset = (page - 1) * limit

        cursor.execute("""
            SELECT
                nv.MaNhanVien, nv.MaNV, nv.HoTen, nv.NgaySinh, nv.GioiTinh,
                nv.SoDienThoai, nv.Email, nv.DiaChi, nv.NgayVaoLam,
                nv.MaPhongBan, pb.TenPhongBan, nv.MaChucVu, cv.TenChucVu,
                nv.LuongCoBan, nv.TrangThai
            FROM NhanVien nv
            LEFT JOIN PhongBan pb ON nv.MaPhongBan = pb.MaPhongBan
            LEFT JOIN ChucVu cv ON nv.MaChucVu = cv.MaChucVu
        """ + where + " ORDER BY nv.MaNhanVien DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY", *(params + [offset, limit]))

        data = [row_to_dict(row) for row in cursor.fetchall()]
        total_pages = (total + limit - 1) // limit if total else 0
        return {"data": data, "page": page, "limit": limit, "total": total, "totalPages": total_pages}
    finally:
        cursor.close()
        conn.close()


@router.get("/{id}", response_model=dict)
def get_nhan_vien_by_id(id: int):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(SELECT_SQL + " WHERE nv.MaNhanVien = ?", id)
        row = cursor.fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên")
        return row_to_dict(row)
    finally:
        conn.close()


@router.post("/", status_code=201)
def create_nhan_vien(data: NhanVienModel):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM NhanVien WHERE MaNV = ?", data.MaNV)
        if cursor.fetchone() is not None:
            raise HTTPException(status_code=400, detail="Mã nhân viên đã tồn tại")

        check_foreign_keys(cursor, data)

        cursor.execute(
            """
            INSERT INTO NhanVien
            (MaNV, HoTen, NgaySinh, GioiTinh, SoDienThoai, Email, DiaChi,
             NgayVaoLam, MaPhongBan, MaChucVu, LuongCoBan, TrangThai)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            data.MaNV,
            data.HoTen,
            data.NgaySinh,
            data.GioiTinh,
            data.SoDienThoai,
            data.Email,
            data.DiaChi,
            data.NgayVaoLam,
            data.MaPhongBan,
            data.MaChucVu,
            data.LuongCoBan,
            data.TrangThai,
        )
        conn.commit()
        return {"message": "Thêm nhân viên thành công"}
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi thêm nhân viên: {e}")
    finally:
        conn.close()


@router.put("/{id}")
def update_nhan_vien(id: int, data: NhanVienModel):
    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT 1 FROM NhanVien WHERE MaNhanVien = ?", id)
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên")

        cursor.execute(
            "SELECT 1 FROM NhanVien WHERE MaNV = ? AND MaNhanVien <> ?",
            data.MaNV,
            id,
        )
        if cursor.fetchone() is not None:
            raise HTTPException(status_code=400, detail="Mã nhân viên đã tồn tại")

        check_foreign_keys(cursor, data)

        cursor.execute(
            """
            UPDATE NhanVien SET
                MaNV = ?, HoTen = ?, NgaySinh = ?, GioiTinh = ?,
                SoDienThoai = ?, Email = ?, DiaChi = ?, NgayVaoLam = ?,
                MaPhongBan = ?, MaChucVu = ?, LuongCoBan = ?, TrangThai = ?
            WHERE MaNhanVien = ?
            """,
            data.MaNV,
            data.HoTen,
            data.NgaySinh,
            data.GioiTinh,
            data.SoDienThoai,
            data.Email,
            data.DiaChi,
            data.NgayVaoLam,
            data.MaPhongBan,
            data.MaChucVu,
            data.LuongCoBan,
            data.TrangThai,
            id,
        )
        conn.commit()
        return {"message": "Cập nhật nhân viên thành công"}
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi cập nhật nhân viên: {e}")
    finally:
        conn.close()


@router.delete("/{id}")
def delete_nhan_vien(id: int):
    """Xóa theo MaNhanVien và xóa các bản ghi con trước để không vi phạm FK."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM NhanVien WHERE MaNhanVien = ?", id)
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy nhân viên")

        # Các bảng này đều tham chiếu NhanVien.MaNhanVien trong thuctap.sql.
        cursor.execute("DELETE FROM BangLuong WHERE MaNhanVien = ?", id)
        cursor.execute("DELETE FROM HopDong WHERE MaNhanVien = ?", id)
        cursor.execute("DELETE FROM TaiKhoan WHERE MaNhanVien = ?", id)
        cursor.execute("DELETE FROM NhanVien WHERE MaNhanVien = ?", id)

        conn.commit()
        return {"message": "Xóa nhân viên thành công"}
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi xóa nhân viên: {e}")
    finally:
        conn.close()
