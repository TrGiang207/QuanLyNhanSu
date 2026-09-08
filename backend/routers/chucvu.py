from decimal import Decimal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from database import get_connection


router = APIRouter()


class ChucVuModel(BaseModel):
    TenChucVu: str
    HeSoLuong: Decimal = Field(default=Decimal("1"), ge=0)


@router.get("/")
def get_chuc_vu():
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                MaChucVu,
                TenChucVu,
                HeSoLuong
            FROM ChucVu
            ORDER BY MaChucVu
        """)

        rows = cursor.fetchall()

        data = []

        for row in rows:
            data.append({
                "MaChucVu": row.MaChucVu,
                "TenChucVu": row.TenChucVu,
                "HeSoLuong": row.HeSoLuong
            })

        return {
            "data": data
        }

    finally:
        conn.close()


@router.get("/{id}")
def get_chuc_vu_by_id(id: int):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                MaChucVu,
                TenChucVu,
                HeSoLuong
            FROM ChucVu
            WHERE MaChucVu = ?
        """, id)

        row = cursor.fetchone()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy chức vụ"
            )

        return {
            "MaChucVu": row.MaChucVu,
            "TenChucVu": row.TenChucVu,
            "HeSoLuong": row.HeSoLuong
        }

    finally:
        conn.close()


@router.post("/", status_code=201)
def create_chuc_vu(data: ChucVuModel):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT 1 FROM ChucVu WHERE TenChucVu = ?",
            data.TenChucVu
        )

        if cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail="Tên chức vụ đã tồn tại"
            )

        cursor.execute("""
            INSERT INTO ChucVu
            (
                TenChucVu,
                HeSoLuong
            )
            VALUES (?, ?)
        """,
            data.TenChucVu,
            data.HeSoLuong
        )

        conn.commit()

        return {
            "message": "Thêm chức vụ thành công"
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Lỗi thêm chức vụ: {e}"
        )

    finally:
        conn.close()


@router.put("/{id}")
def update_chuc_vu(id: int, data: ChucVuModel):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT 1 FROM ChucVu WHERE MaChucVu = ?",
            id
        )

        if cursor.fetchone() is None:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy chức vụ"
            )

        cursor.execute("""
            SELECT 1
            FROM ChucVu
            WHERE TenChucVu = ?
            AND MaChucVu <> ?
        """,
            data.TenChucVu,
            id
        )

        if cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail="Tên chức vụ đã tồn tại"
            )

        cursor.execute("""
            UPDATE ChucVu
            SET
                TenChucVu = ?,
                HeSoLuong = ?
            WHERE MaChucVu = ?
        """,
            data.TenChucVu,
            data.HeSoLuong,
            id
        )

        conn.commit()

        return {
            "message": "Cập nhật chức vụ thành công"
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Lỗi cập nhật chức vụ: {e}"
        )

    finally:
        conn.close()


@router.delete("/{id}")
def delete_chuc_vu(id: int):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT 1 FROM ChucVu WHERE MaChucVu = ?",
            id
        )

        if cursor.fetchone() is None:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy chức vụ"
            )

        cursor.execute(
            "SELECT 1 FROM NhanVien WHERE MaChucVu = ?",
            id
        )

        if cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail="Không thể xóa chức vụ đang có nhân viên"
            )

        cursor.execute(
            "DELETE FROM ChucVu WHERE MaChucVu = ?",
            id
        )

        conn.commit()

        return {
            "message": "Xóa chức vụ thành công"
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Lỗi xóa chức vụ: {e}"
        )

    finally:
        conn.close()