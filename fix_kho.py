import os
import chromadb

# 1. Định nghĩa đường dẫn tuyệt đối
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
THU_MUC_KHO = os.path.join(BASE_DIR, "Kho_Du_Lieu_Vector")

print(f"📂 Đường dẫn kho sẽ tạo: {THU_MUC_KHO}")

# 2. Tự tạo thư mục bằng tay trước
if not os.path.exists(THU_MUC_KHO):
    try:
        os.makedirs(THU_MUC_KHO)
        print("✅ Đã tạo thư mục Kho_Du_Lieu_Vector thành công bằng lệnh OS.")
    except Exception as e:
        print(f"❌ Không thể tạo thư mục: {e}")

# 3. Ép ChromaDB khởi tạo file Database
try:
    print("⏳ Đang ép ChromaDB khởi tạo Database...")
    client = chromadb.PersistentClient(path=THU_MUC_KHO)
    collection = client.get_or_create_collection(name="tai_lieu_seo")
    
    # Ghi thử một đoạn dữ liệu mồi
    collection.upsert(
        ids=["test_id"],
        documents=["Day la du lieu kiem tra"],
        metadatas=[{"status": "ok"}]
    )
    print("🎉 CHÚC MỪNG! Kho dữ liệu đã được tạo và ghi thành công.")
    print("👉 Bây giờ anh hãy vào thư mục sẽ thấy file 'chroma.sqlite3'.")
except Exception as e:
    print(f"❌ Vẫn dính lỗi khởi tạo: {e}")
    if "Errno 22" in str(e):
        print("🚩 CẢNH BÁO: Windows vẫn chặn quyền ghi. Anh hãy thử chạy Terminal bằng quyền Administrator (Run as Administrator).")
        