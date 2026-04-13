# 🍀 Lắc Vận May

App PWA giải trí vui nhộn — lắc điện thoại (hoặc chạm nút) để xem vận hôm nay!

## Tính năng
- 30+ câu chúc vui nhộn tiếng Việt
- Hiệu ứng mưa emoji 🎉
- Rung điện thoại mỗi lần lắc
- Nền gradient đổi màu động
- Đếm streak (lưu localStorage)
- Cài được trên Android như app thật (PWA)
- Hoạt động offline sau lần mở đầu

## Cài trên Android
1. Deploy thư mục này lên bất kỳ host HTTPS nào (Vercel, GitHub Pages, Netlify...)
2. Mở link bằng Chrome trên điện thoại Android
3. Nhấn menu ⋮ → **"Add to Home screen"** / **"Cài đặt ứng dụng"**
4. Icon 🍀 xuất hiện trên màn hình chính, mở như app native

## Chạy thử cục bộ
```bash
cd lac-van-may
python -m http.server 8000
# Mở http://localhost:8000
```

> Lưu ý: DeviceMotion chỉ hoạt động trên HTTPS (hoặc localhost). Shake sẽ không kích hoạt trên http://ip-noi-bo.
