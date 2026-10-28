
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import cast, String
from backend.app.database import get_db
from backend.app.models import Phong, KhachHang, HoaDon
from backend.app.schemas import ThongKeSummary

router = APIRouter(prefix="/thong-ke", tags=["Thống Kê Báo Cáo"])


@router.get("/tong-quan", response_model=ThongKeSummary)
def get_dashboard_summary(db: Session = Depends(get_db)):
    tong_phong = db.query(Phong).count()

    phong_trong = db.query(Phong).filter(
        Phong.TinhTrang == "Trống"
    ).count()

    phong_dang_thue = db.query(Phong).filter(
        Phong.TinhTrang == "Đang thuê"
    ).count()

    phong_dang_don = db.query(Phong).filter(
        Phong.TinhTrang == "Đang dọn"
    ).count()

    phong_bao_tri = db.query(Phong).filter(
        Phong.TinhTrang == "Bảo trì"
    ).count()

    tong_khach = db.query(KhachHang).count()

    # Chỉ lấy các cột cần dùng và chuyển sang chuỗi tại SQL Server
    invoices = db.query(
        cast(HoaDon.TienPhong, String),
        cast(HoaDon.TienDichVu, String),
        cast(HoaDon.TienPhuThu, String),
        cast(HoaDon.UuDai, String),
        cast(HoaDon.TyLeVAT, String)
    ).filter(
        HoaDon.TrangThai == "Đã thanh toán"
    ).all()

    doanh_thu = 0.0

    for tien_phong, tien_dich_vu, tien_phu_thu, uu_dai, vat in invoices:
        subtotal = (
            float(tien_phong or 0)
            + float(tien_dich_vu or 0)
            + float(tien_phu_thu or 0)
            - float(uu_dai or 0)
        )

        ty_le_vat = float(vat) if vat not in (None, "") else 10.0
        doanh_thu += subtotal * (1 + ty_le_vat / 100.0)

    return ThongKeSummary(
        tong_phong=tong_phong,
        phong_trong=phong_trong,
        phong_dang_thue=phong_dang_thue,
        phong_dang_don=phong_dang_don,
        phong_bao_tri=phong_bao_tri,
        tong_khach_hang=tong_khach,
        doanh_thu_thang=round(doanh_thu)
    )
