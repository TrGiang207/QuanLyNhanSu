from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database import get_connection


router = APIRouter()


class PhongBanModel(BaseModel):
    TenPhongBan: str
    MoTa: Optional[str] = None


@router.get("/")
def get_phong_ban():
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                MaPhongBan,
                TenPhongBan,
                MoTa
            FROM PhongBan
            ORDER BY MaPhongBan
        """)

        rows = cursor.fetchall()

        data = []

        for row in rows:
            data.append({
                "MaPhongBan": row.MaPhongBan,
                "TenPhongBan": row.TenPhongBan,
                "MoTa": row.MoTa
            })

        return {
            "data": data
        }

    finally:
        conn.close()


@router.get("/{id}")
def get_phong_ban_by_id(id: int):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                MaPhongBan,
                TenPhongBan,
                MoTa
            FROM PhongBan
            WHERE MaPhongBan = ?
        """, id)

        row = cursor.fetchone()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy phòng ban"
            )

        return {
            "MaPhongBan": row.MaPhongBan,
            "TenPhongBan": row.TenPhongBan,
            "MoTa": row.MoTa
        }

    finally:
        conn.close()


@router.post("/", status_code=201)
def create_phong_ban(data: PhongBanModel):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT 1 FROM PhongBan WHERE TenPhongBan = ?",
            data.TenPhongBan
        )

        if cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail="Tên phòng ban đã tồn tại"
            )

        cursor.execute("""
            INSERT INTO PhongBan
            (
                TenPhongBan,
                MoTa
            )
            VALUES (?, ?)
        """,
            data.TenPhongBan,
            data.MoTa
        )

        conn.commit()

        return {
            "message": "Thêm phòng ban thành công"
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Lỗi thêm phòng ban: {e}"
        )

    finally:
        conn.close()


@router.put("/{id}")
def update_phong_ban(id: int, data: PhongBanModel):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT 1 FROM PhongBan WHERE MaPhongBan = ?",
            id
        )

        if cursor.fetchone() is None:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy phòng ban"
            )

        cursor.execute("""
            SELECT 1
            FROM PhongBan
            WHERE TenPhongBan = ?
            AND MaPhongBan <> ?
        """,
            data.TenPhongBan,
            id
        )

        if cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail="Tên phòng ban đã tồn tại"
            )

        cursor.execute("""
            UPDATE PhongBan
            SET
                TenPhongBan = ?,
                MoTa = ?
            WHERE MaPhongBan = ?
        """,
            data.TenPhongBan,
            data.MoTa,
            id
        )

        conn.commit()

        return {
            "message": "Cập nhật phòng ban thành công"
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Lỗi cập nhật phòng ban: {e}"
        )

    finally:
        conn.close()


@router.delete("/{id}")
def delete_phong_ban(id: int):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT 1 FROM PhongBan WHERE MaPhongBan = ?",
            id
        )

        if cursor.fetchone() is None:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy phòng ban"
            )

        # Kiểm tra phòng ban có nhân viên không
        cursor.execute(
            "SELECT 1 FROM NhanVien WHERE MaPhongBan = ?",
            id
        )

        if cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail="Không thể xóa phòng ban đang có nhân viên"
            )

        cursor.execute(
            "DELETE FROM PhongBan WHERE MaPhongBan = ?",
            id
        )

        conn.commit()

        return {
            "message": "Xóa phòng ban thành công"
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Lỗi xóa phòng ban: {e}"
        )

    finally:
        conn.close()