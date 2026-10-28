from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models import HoaDon, PhieuThue, ChiTietPhieuThue, DungDichVu, KhachHang, LoaiKhachHang
from backend.app.schemas import HoaDonOut

router = APIRouter(prefix="/hoa-don", tags=["Hóa Đơn & Thanh Toán"])

@router.get("", response_model=List[HoaDonOut])
def list_invoices(db: Session = Depends(get_db)):
    invoices = db.query(HoaDon).order_by(HoaDon.NgayLap.desc()).limit(50).all()
    results = []
    for h in invoices:
        tien_phong = float(h.TienPhong or 0)
        tien_dv = float(h.TienDichVu or 0)
        tien_phu_thu = float(h.TienPhuThu or 0)
        uu_dai = float(h.UuDai or 0)
        vat_rate = float(h.TyLeVAT or 10)
        subtotal = max(0.0, tien_phong + tien_dv + tien_phu_thu - uu_dai)
        tong = round(subtotal + (subtotal * vat_rate / 100.0))

        results.append(
            HoaDonOut(
                MaHD=h.MaHD,
                MaPhieuThue=h.MaPhieuThue,
                MaNV=h.MaNV,
                NgayLap=h.NgayLap,
                TienPhong=tien_phong,
                TienDichVu=tien_dv,
                TienPhuThu=tien_phu_thu,
                UuDai=uu_dai,
                TyLeVAT=vat_rate,
                TongTien=tong,
                TrangThai=h.TrangThai
            )
        )
    return results

@router.post("/tao-hoa-don/{ma_pt}", response_model=HoaDonOut)
def generate_invoice(ma_pt: str, db: Session = Depends(get_db)):
    # 1. Kiểm tra phiếu thuê
    pt = db.query(PhieuThue).filter(PhieuThue.MaPhieuThue == ma_pt).first()
    if not pt:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiếu thuê")

    # Kiểm tra hóa đơn đã tồn tại chưa
    hd_exist = db.query(HoaDon).filter(HoaDon.MaPhieuThue == ma_pt).first()
    if hd_exist:
        return HoaDonOut(
            MaHD=hd_exist.MaHD,
            MaPhieuThue=hd_exist.MaPhieuThue,
            MaNV=hd_exist.MaNV,
            NgayLap=hd_exist.NgayLap,
            TienPhong=float(hd_exist.TienPhong or 0),
            TienDichVu=float(hd_exist.TienDichVu or 0),
            TienPhuThu=float(hd_exist.TienPhuThu or 0),
            UuDai=float(hd_exist.UuDai or 0),
            TyLeVAT=float(hd_exist.TyLeVAT or 10),
            TongTien=float(hd_exist.TienPhong + hd_exist.TienDichVu - hd_exist.UuDai) * 1.1,
            TrangThai=hd_exist.TrangThai
        )

    # 2. Tính tiền phòng
    tien_phong = 0.0
    for ct in pt.chi_tiet:
        gio_nhan = ct.GioNhan
        gio_tra = ct.GioTra or datetime.now()
        duration_days = max(1, (gio_tra.date() - gio_nhan.date()).days)
        tien_phong += float(ct.DonGiaApDung) * duration_days

    # 3. Tính tiền dịch vụ
    tien_dich_vu = 0.0
    used_services = db.query(DungDichVu).filter(DungDichVu.MaPhieuThue == ma_pt).all()
    for s in used_services:
        tien_dich_vu += float(s.DonGiaApDung) * s.SoLuong

    # 4. Tính ưu đãi khách hàng
    kh = db.query(KhachHang).filter(KhachHang.MaKH == pt.MaKH).first()
    phan_tram_uu_dai = 0.0
    if kh and kh.loai_khach_hang:
        phan_tram_uu_dai = float(kh.loai_khach_hang.PhanTramUuDai or 0)
    uu_dai = round((tien_phong + tien_dich_vu) * phan_tram_uu_dai / 100.0)

    # 5. Sinh mã hóa đơn mới
    now = datetime.now()
    count_hd = db.query(HoaDon).count()
    ma_hd = f"HD{now.strftime('%y%m%d')}{count_hd + 1:03d}"
    while db.query(HoaDon).filter(HoaDon.MaHD == ma_hd).first():
        count_hd += 1
        ma_hd = f"HD{now.strftime('%y%m%d')}{count_hd:03d}"

    new_hd = HoaDon(
        MaHD=ma_hd,
        MaPhieuThue=ma_pt,
        MaNV="NV01",
        NgayLap=now,
        TienPhong=tien_phong,
        TienDichVu=tien_dich_vu,
        TienPhuThu=0,
        UuDai=uu_dai,
        TyLeVAT=10,
        TrangThai="Chưa thanh toán"
    )
    db.add(new_hd)
    db.commit()
    db.refresh(new_hd)

    subtotal = max(0.0, tien_phong + tien_dich_vu - uu_dai)
    tong = round(subtotal + (subtotal * 10 / 100.0))

    return HoaDonOut(
        MaHD=new_hd.MaHD,
        MaPhieuThue=new_hd.MaPhieuThue,
        MaNV=new_hd.MaNV,
        NgayLap=new_hd.NgayLap,
        TienPhong=tien_phong,
        TienDichVu=tien_dich_vu,
        TienPhuThu=0.0,
        UuDai=uu_dai,
        TyLeVAT=10.0,
        TongTien=tong,
        TrangThai=new_hd.TrangThai
    )

@router.post("/{ma_hd}/thanh-toan")
def pay_invoice(ma_hd: str, db: Session = Depends(get_db)):
    hd = db.query(HoaDon).filter(HoaDon.MaHD == ma_hd).first()
    if not hd:
        raise HTTPException(status_code=404, detail="Không tìm thấy hóa đơn")

    hd.TrangThai = "Đã thanh toán"
    db.commit()
    return {"message": f"Hóa đơn {ma_hd} đã được thanh toán thành công!"}

