from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from database import get_connection

router = APIRouter()


class BangLuongModel(BaseModel):
    MaNhanVien: int
    Thang: int = Field(..., ge=1, le=12)
    Nam: int = Field(..., ge=2000)
    LuongCoBan: float = Field(..., ge=0)
    PhuCap: float = Field(0, ge=0)
    Thuong: float = Field(0, ge=0)
    KhauTru: float = Field(0, ge=0)


def row_to_dict(row):
    return {
        "MaLuong": row.MaLuong,
        "MaNhanVien": row.MaNhanVien,
        "MaNV": row.MaNV,
        "HoTen": row.HoTen,
        "Thang": row.Thang,
        "Nam": row.Nam,
        "LuongCoBan": float(row.LuongCoBan or 0),
        "PhuCap": float(row.PhuCap or 0),
        "Thuong": float(row.Thuong or 0),
        "KhauTru": float(row.KhauTru or 0),
        "ThucLinh": float(
            (row.LuongCoBan or 0)
            + (row.PhuCap or 0)
            + (row.Thuong or 0)
            - (row.KhauTru or 0)
        )
    }


# GET danh sách bảng lương
@router.get("/")
def get_bang_luong(
    maNhanVien: int | None = None,
    thang: int | None = Query(None, ge=1, le=12),
    nam: int | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100)
):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        conditions = []
        params = []

        if maNhanVien is not None:
            conditions.append("bl.MaNhanVien = ?")
            params.append(maNhanVien)

        if thang is not None:
            conditions.append("bl.Thang = ?")
            params.append(thang)

        if nam is not None:
            conditions.append("bl.Nam = ?")
            params.append(nam)

        where_sql = ""

        if conditions:
            where_sql = "WHERE " + " AND ".join(conditions)

        # Đếm tổng số bản ghi
        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM BangLuong bl
            {where_sql}
            """,
            *params
        )

        total = cursor.fetchone()[0]

        offset = (page - 1) * limit

        cursor.execute(
            f"""
            SELECT
                bl.MaLuong,
                bl.MaNhanVien,
                nv.MaNV,
                nv.HoTen,
                bl.Thang,
                bl.Nam,
                bl.LuongCoBan,
                bl.PhuCap,
                bl.Thuong,
                bl.KhauTru
            FROM BangLuong bl
            INNER JOIN NhanVien nv
                ON bl.MaNhanVien = nv.MaNhanVien
            {where_sql}
            ORDER BY bl.Nam DESC, bl.Thang DESC, bl.MaLuong DESC
            OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
            """,
            *params,
            offset,
            limit
        )

        rows = cursor.fetchall()

        data = [row_to_dict(row) for row in rows]

        total_pages = (total + limit - 1) // limit

        return {
            "data": data,
            "page": page,
            "limit": limit,
            "total": total,
            "totalPages": total_pages
        }

    finally:
        conn.close()


# GET bảng lương theo ID
@router.get("/{id}")
def get_bang_luong_by_id(id: int):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                bl.MaLuong,
                bl.MaNhanVien,
                nv.MaNV,
                nv.HoTen,
                bl.Thang,
                bl.Nam,
                bl.LuongCoBan,
                bl.PhuCap,
                bl.Thuong,
                bl.KhauTru
            FROM BangLuong bl
            INNER JOIN NhanVien nv
                ON bl.MaNhanVien = nv.MaNhanVien
            WHERE bl.MaLuong = ?
            """,
            id
        )

        row = cursor.fetchone()

        if row is None:
            raise HTTPException(404, "Không tìm thấy bảng lương")

        return row_to_dict(row)

    finally:
        conn.close()


# POST thêm bảng lương
@router.post("/")
def them_bang_luong(data: BangLuongModel):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        # Kiểm tra nhân viên
        cursor.execute(
            "SELECT 1 FROM NhanVien WHERE MaNhanVien = ?",
            data.MaNhanVien
        )

        if cursor.fetchone() is None:
            raise HTTPException(400, "Nhân viên không tồn tại")

        # Kiểm tra trùng tháng/năm
        cursor.execute(
            """
            SELECT 1
            FROM BangLuong
            WHERE MaNhanVien = ?
              AND Thang = ?
              AND Nam = ?
            """,
            data.MaNhanVien,
            data.Thang,
            data.Nam
        )

        if cursor.fetchone():
            raise HTTPException(
                400,
                "Nhân viên đã có bảng lương trong tháng này"
            )

        cursor.execute(
            """
            INSERT INTO BangLuong
            (
                MaNhanVien,
                Thang,
                Nam,
                LuongCoBan,
                PhuCap,
                Thuong,
                KhauTru
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            data.MaNhanVien,
            data.Thang,
            data.Nam,
            data.LuongCoBan,
            data.PhuCap,
            data.Thuong,
            data.KhauTru
        )

        conn.commit()

        return {
            "message": "Thêm bảng lương thành công"
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        conn.rollback()
        raise HTTPException(
            500,
            f"Lỗi thêm bảng lương: {e}"
        )

    finally:
        conn.close()


# PUT sửa bảng lương
@router.put("/{id}")
def sua_bang_luong(id: int, data: BangLuongModel):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT 1 FROM BangLuong WHERE MaLuong = ?",
            id
        )

        if cursor.fetchone() is None:
            raise HTTPException(404, "Không tìm thấy bảng lương")

        cursor.execute(
            "SELECT 1 FROM NhanVien WHERE MaNhanVien = ?",
            data.MaNhanVien
        )

        if cursor.fetchone() is None:
            raise HTTPException(400, "Nhân viên không tồn tại")

        cursor.execute(
            """
            SELECT 1
            FROM BangLuong
            WHERE MaNhanVien = ?
              AND Thang = ?
              AND Nam = ?
              AND MaLuong <> ?
            """,
            data.MaNhanVien,
            data.Thang,
            data.Nam,
            id
        )

        if cursor.fetchone():
            raise HTTPException(
                400,
                "Nhân viên đã có bảng lương trong tháng này"
            )

        cursor.execute(
            """
            UPDATE BangLuong
            SET
                MaNhanVien = ?,
                Thang = ?,
                Nam = ?,
                LuongCoBan = ?,
                PhuCap = ?,
                Thuong = ?,
                KhauTru = ?
            WHERE MaLuong = ?
            """,
            data.MaNhanVien,
            data.Thang,
            data.Nam,
            data.LuongCoBan,
            data.PhuCap,
            data.Thuong,
            data.KhauTru,
            id
        )

        conn.commit()

        return {
            "message": "Cập nhật bảng lương thành công"
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        conn.rollback()
        raise HTTPException(
            500,
            f"Lỗi cập nhật bảng lương: {e}"
        )

    finally:
        conn.close()


# DELETE bảng lương
@router.delete("/{id}")
def xoa_bang_luong(id: int):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT 1 FROM BangLuong WHERE MaLuong = ?",
            id
        )

        if cursor.fetchone() is None:
            raise HTTPException(404, "Không tìm thấy bảng lương")

        cursor.execute(
            "DELETE FROM BangLuong WHERE MaLuong = ?",
            id
        )

        conn.commit()

        return {
            "message": "Xóa bảng lương thành công"
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        conn.rollback()
        raise HTTPException(
            500,
            f"Lỗi xóa bảng lương: {e}"
        )

    finally:
        conn.close()