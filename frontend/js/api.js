// frontend/js/api.js
// Quản lý gọi API tới FastAPI Backend

const API_BASE = '/api';

// Format tiền tệ VNĐ
function formatMoney(amount) {
    if (amount === null || amount === undefined) return '0 ₫';
    return Number(amount).toLocaleString('vi-VN') + ' ₫';
}

// Format ngày giờ
function formatDateTime(dtStr) {
    if (!dtStr) return '—';
    const d = new Date(dtStr);
    return d.toLocaleString('vi-VN', {
        hour: '2-digit', minute: '2-digit',
        day: '2-digit', month: '2-digit', year: 'numeric'
    });
}

// Hàm fetch wrapper xử lý lỗi
async function apiRequest(endpoint, options = {}) {
    try {
        const url = `${API_BASE}${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...(options.headers || {})
        };

        const res = await fetch(url, { ...options, headers });
        const data = await res.json();

        if (!res.ok) {
            throw new Error(data.detail || 'Có lỗi xảy ra khi gọi API');
        }
        return data;
    } catch (err) {
        console.error(`API Error [${endpoint}]:`, err);
        throw err;
    }
}

// 1. Quản lý Phòng
const RoomAPI = {
    getAll: (tang = null, tinhTrang = null) => {
        let q = [];
        if (tang) q.push(`tang=${tang}`);
        if (tinhTrang) q.push(`tinh_trang=${encodeURIComponent(tinhTrang)}`);
        const queryStr = q.length ? `?${q.join('&')}` : '';
        return apiRequest(`/phong${queryStr}`);
    },
    getTypes: () => apiRequest('/phong/loai-phong'),
    updateStatus: (maPhong, tinhTrang) => {
        return apiRequest(`/phong/${maPhong}/tinh-trang`, {
            method: 'PUT',
            body: JSON.stringify({ TinhTrang: tinhTrang })
        });
    }
};

// 2. Quản lý Khách hàng
const CustomerAPI = {
    getAll: (keyword = '') => {
        const q = keyword ? `?keyword=${encodeURIComponent(keyword)}` : '';
        return apiRequest(`/khach-hang${q}`);
    },
    create: (customerData) => {
        return apiRequest('/khach-hang', {
            method: 'POST',
            body: JSON.stringify(customerData)
        });
    }
};

// 3. Quản lý Phiếu thuê
const RentalAPI = {
    getAll: (trangThai = null) => {
        const q = trangThai ? `?trang_thai=${encodeURIComponent(trangThai)}` : '';
        return apiRequest(`/phieu-thue${q}`);
    },
    create: (rentalData) => {
        return apiRequest('/phieu-thue', {
            method: 'POST',
            body: JSON.stringify(rentalData)
        });
    },
    checkOut: (maPT) => {
        return apiRequest(`/phieu-thue/${maPT}/tra-phong`, {
            method: 'POST'
        });
    }
};

// 4. Quản lý Dịch vụ
const ServiceAPI = {
    getAll: () => apiRequest('/dich-vu'),
    use: (data) => {
        return apiRequest('/dich-vu/su-dung', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
};

// 5. Quản lý Hóa đơn
const InvoiceAPI = {
    getAll: () => apiRequest('/hoa-don'),
    generate: (maPT) => {
        return apiRequest(`/hoa-don/tao-hoa-don/${maPT}`, {
            method: 'POST'
        });
    },
    pay: (maHD) => {
        return apiRequest(`/hoa-don/${maHD}/thanh-toan`, {
            method: 'POST'
        });
    }
};

// 6. Thống kê
const StatsAPI = {
    getSummary: () => apiRequest('/thong-ke/tong-quan')
};

