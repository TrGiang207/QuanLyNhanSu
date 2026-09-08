from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from database import get_connection


router = APIRouter()


class HopDongModel(BaseModel):
    SoHopDong: str
    MaNhanVien: int
    LoaiHopDong: str
    NgayBatDau: date
    NgayKetThuc: Optional[date] = None
    TrangThai: bool = True


@router.get("/")
def get_hop_dong():
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                hd.MaHopDong,
                hd.SoHopDong,
                hd.MaNhanVien,
                nv.MaNV,
                nv.HoTen,
                hd.LoaiHopDong,
                hd.NgayBatDau,
                hd.NgayKetThuc,
                hd.TrangThai
            FROM HopDong hd
            INNER JOIN NhanVien nv
                ON hd.MaNhanVien = nv.MaNhanVien
            ORDER BY hd.MaHopDong DESC
        """)

        rows = cursor.fetchall()

        data = []

        for row in rows:
            data.append({
                "MaHopDong": row.MaHopDong,
                "SoHopDong": row.SoHopDong,
                "MaNhanVien": row.MaNhanVien,
                "MaNV": row.MaNV,
                "HoTen": row.HoTen,
                "LoaiHopDong": row.LoaiHopDong,
                "NgayBatDau": row.NgayBatDau,
                "NgayKetThuc": row.NgayKetThuc,
                "TrangThai": bool(row.TrangThai)
            })

        return {
            "data": data
        }

    finally:
        conn.close()


@router.get("/sap-het-han/")
def hop_dong_sap_het_han():
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                hd.MaHopDong,
                hd.SoHopDong,
                nv.MaNV,
                nv.HoTen,
                hd.LoaiHopDong,
                hd.NgayBatDau,
                hd.NgayKetThuc,
                hd.TrangThai
            FROM HopDong hd
            INNER JOIN NhanVien nv
                ON hd.MaNhanVien = nv.MaNhanVien
            WHERE hd.NgayKetThuc IS NOT NULL
            AND hd.NgayKetThuc >= CAST(GETDATE() AS DATE)
            AND hd.NgayKetThuc <= DATEADD(DAY, 30, CAST(GETDATE() AS DATE))
            AND hd.TrangThai = 1
            ORDER BY hd.NgayKetThuc
        """)

        rows = cursor.fetchall()

        data = []

        for row in rows:
            data.append({
                "MaHopDong": row.MaHopDong,
                "SoHopDong": row.SoHopDong,
                "MaNV": row.MaNV,
                "HoTen": row.HoTen,
                "LoaiHopDong": row.LoaiHopDong,
                "NgayBatDau": row.NgayBatDau,
                "NgayKetThuc": row.NgayKetThuc,
                "TrangThai": bool(row.TrangThai)
            })

        return {
            "data": data
        }

    finally:
        conn.close()


@router.get("/{id}")
def get_hop_dong_by_id(id: int):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                MaHopDong,
                SoHopDong,
                MaNhanVien,
                LoaiHopDong,
                NgayBatDau,
                NgayKetThuc,
                TrangThai
            FROM HopDong
            WHERE MaHopDong = ?
        """, id)

        row = cursor.fetchone()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy hợp đồng"
            )

        return {
            "MaHopDong": row.MaHopDong,
            "SoHopDong": row.SoHopDong,
            "MaNhanVien": row.MaNhanVien,
            "LoaiHopDong": row.LoaiHopDong,
            "NgayBatDau": row.NgayBatDau,
            "NgayKetThuc": row.NgayKetThuc,
            "TrangThai": bool(row.TrangThai)
        }

    finally:
        conn.close()


@router.post("/", status_code=201)
def create_hop_dong(data: HopDongModel):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 1
            FROM HopDong
            WHERE SoHopDong = ?
        """, data.SoHopDong)

        if cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail="Số hợp đồng đã tồn tại"
            )

        cursor.execute("""
            SELECT 1
            FROM NhanVien
            WHERE MaNhanVien = ?
        """, data.MaNhanVien)

        if cursor.fetchone() is None:
            raise HTTPException(
                status_code=400,
                detail="Nhân viên không tồn tại"
            )

        cursor.execute("""
            INSERT INTO HopDong
            (
                SoHopDong,
                MaNhanVien,
                LoaiHopDong,
                NgayBatDau,
                NgayKetThuc,
                TrangThai
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            data.SoHopDong,
            data.MaNhanVien,
            data.LoaiHopDong,
            data.NgayBatDau,
            data.NgayKetThuc,
            data.TrangThai
        )

        conn.commit()

        return {
            "message": "Thêm hợp đồng thành công"
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Lỗi thêm hợp đồng: {e}"
        )

    finally:
        conn.close()


@router.put("/{id}")
def update_hop_dong(id: int, data: HopDongModel):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT 1 FROM HopDong WHERE MaHopDong = ?",
            id
        )

        if cursor.fetchone() is None:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy hợp đồng"
            )

        cursor.execute("""
            SELECT 1
            FROM HopDong
            WHERE SoHopDong = ?
            AND MaHopDong <> ?
        """,
            data.SoHopDong,
            id
        )

        if cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail="Số hợp đồng đã tồn tại"
            )

        cursor.execute("""
            UPDATE HopDong
            SET
                SoHopDong = ?,
                MaNhanVien = ?,
                LoaiHopDong = ?,
                NgayBatDau = ?,
                NgayKetThuc = ?,
                TrangThai = ?
            WHERE MaHopDong = ?
        """,
            data.SoHopDong,
            data.MaNhanVien,
            data.LoaiHopDong,
            data.NgayBatDau,
            data.NgayKetThuc,
            data.TrangThai,
            id
        )

        conn.commit()

        return {
            "message": "Cập nhật hợp đồng thành công"
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Lỗi cập nhật hợp đồng: {e}"
        )

    finally:
        conn.close()


@router.delete("/{id}")
def delete_hop_dong(id: int):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT 1 FROM HopDong WHERE MaHopDong = ?",
            id
        )

        if cursor.fetchone() is None:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy hợp đồng"
            )

        cursor.execute(
            "DELETE FROM HopDong WHERE MaHopDong = ?",
            id
        )

        conn.commit()

        return {
            "message": "Xóa hợp đồng thành công"
        }

    except HTTPException:
        conn.rollback()
        raise

    except Exception as e:
        conn.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Lỗi xóa hợp đồng: {e}"
        )

    finally:
        conn.close()