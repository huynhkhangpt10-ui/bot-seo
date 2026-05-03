import os
import time
from google import genai

# 1. Trỏ đường dẫn đến file Thẻ căn cước MỚI của sếp
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "vertex-key.json"

# 2. Khởi tạo Client truy cập vào đúng dự án chuẩn xác
client = genai.Client(
    vertexai=True, 
    project="project-46198d54-c335-4c44-bf1", 
    location="us-central1"
)

print("🔍 Đã cầm thẻ căn cước (vertex-key.json), đang mở cửa vào Google Cloud (us-central1)...")
print("🔥 KÍCH HOẠT CHẾ ĐỘ THỬ LỬA: Test quyền sử dụng thực tế!")
print("-" * 70)

try:
    # Lấy danh sách toàn bộ model
    danh_sach = client.models.list()
    count_ok = 0
    
    for model in danh_sach:
        ten_model = model.name
        ten_model_nho = ten_model.lower()
        
        # Chỉ test mấy dòng Gemini
        if 'gemini' in ten_model_nho:
            
            # Phân loại 1: Mấy con chuyên vẽ Ảnh, Nhúng véc-tơ, Âm thanh
            if any(x in ten_model_nho for x in ['image', 'tts', 'embedding', 'audio']):
                print(f"⚠️ [MÓN ĐẶC BIỆT] {ten_model} -> (Chuyên vẽ ảnh/âm thanh/nhúng)")
                continue
                
            # Phân loại 2: Mấy con Chat/Viết bài thì lôi ra test thực tế
            try:
                # Ép nó nói OK
                response = client.models.generate_content(
                    model=ten_model,
                    contents="Say 'OK'"
                )
                print(f"✅ [XÀI NGON] {ten_model} -> Phản hồi: {response.text.strip()}")
                count_ok += 1
                
                # Nghỉ 1.5s chống Spam
                time.sleep(1.5) 
                
            except Exception as e:
                loi_ngan = str(e).split('\n')[0][:60] 
                print(f"❌ [BỊ CẤM/LỖI] {ten_model} -> {loi_ngan}...")
                
    print("-" * 70)
    print(f"🎉 Báo cáo sếp: Đã test xong! Sếp đang có {count_ok} con AI Text đang xài mượt mà.")

except Exception as e:
    print(f"❌ Lỗi truy vấn API tổng: {e}")