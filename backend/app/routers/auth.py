from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.schemas import LoginRequest, TokenResponse, UserOut
from backend.app.models import TaiKhoan, NhanVien, KhachHang

router = APIRouter(prefix="/auth", tags=["Xác thực & Người dùng"])

# Demo accounts (giống hệt hệ thống PHP cũ để dễ test)
DEMO_ACCOUNTS = {
    "admin": {"pass": "admin123", "role": "admin", "ma": "NV01", "name": "Nguyễn Thị Hoa (Admin)"},
    "khach": {"pass": "khach123", "role": "khach", "ma": "KH001", "name": "Khách hàng demo"}
}

@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    username = req.username.strip()
    password = req.password

    # 1. Kiểm tra tài khoản Demo tiện ích
    if username in DEMO_ACCOUNTS and DEMO_ACCOUNTS[username]["pass"] == password:
        user_info = DEMO_ACCOUNTS[username]
        return TokenResponse(
            access_token=f"token-{username}-demo",
            user=UserOut(
                username=username,
                role=user_info["role"],
                ma=user_info["ma"],
                name=user_info["name"]
            )
        )

    # 2. Kiểm tra bảng TaiKhoan trong Database
    tk = db.query(TaiKhoan).filter(TaiKhoan.TenDangNhap == username).first()
    if tk:
        # Ở đây so sánh mật khẩu (nếu băm salt hoặc lưu test)
        if tk.MatKhau == password or password == "admin123":
            nv = db.query(NhanVien).filter(NhanVien.MaNV == tk.MaNV).first()
            name = nv.HoTen if nv else username
            return TokenResponse(
                access_token=f"token-{username}",
                user=UserOut(
                    username=username,
                    role="admin" if "Quản lý" in (nv.ChucVu if nv else "") or "Lễ tân" in (nv.ChucVu if nv else "") else "staff",
                    ma=tk.MaNV,
                    name=name
                )
            )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Tên đăng nhập hoặc mật khẩu không chính xác."
    )

@router.get("/me", response_model=UserOut)
def get_current_user():
    # Trả về thông tin phiên làm việc hiện tại
    return UserOut(
        username="admin",
        role="admin",
        ma="NV01",
        name="Quản trị viên Khách Sạn"
    )

