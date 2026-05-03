# check_model.py
from my_config import client

print("🔍 Đang kết nối vào API để soi danh sách Model...")
print("-" * 50)

try:
    # Lấy danh sách toàn bộ model từ hệ thống
    danh_sach_models = client.models.list()

    count = 0
    print("✅ DANH SÁCH CÁC MODEL GEMINI BẠN CÓ THỂ DÙNG (Copy chính xác tên này):")
    print("-" * 50)
    
    for model in danh_sach_models:
        # Tên model thường có dạng "models/gemini-1.5-pro..." hoặc "gemini-1.5-pro..."
        ten_model = model.name
        
        # Chỉ lọc ra mấy con Gemini cho sếp dễ nhìn, bỏ qua mấy con AI vẽ ảnh hay dịch thuật cũ rích
        if 'gemini' in ten_model.lower():
            # In ra kèm theo mô tả ngắn gọn nếu có (tuỳ API trả về)
            display_name = getattr(model, 'display_name', 'Không có tên hiển thị')
            print(f"👉 Mã code để chạy: {ten_model}")
            count += 1
            
    print("-" * 50)
    print(f"🎉 Quét xong! Sếp đang có {count} con Gemini sẵn sàng phục vụ.")

except Exception as e:
    print(f"❌ Lỗi truy vấn API: {e}")
    print("💡 Gợi ý: Kiểm tra lại mạng hoặc API Key trong my_config.py xem có chính xác chưa.")