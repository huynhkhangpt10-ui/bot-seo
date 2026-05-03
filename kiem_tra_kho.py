import chromadb
import os

# 1. Định nghĩa đường dẫn tuyệt đối để tránh nhầm lẫn
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
THU_MUC_KHO = os.path.join(BASE_DIR, "Kho_Du_Lieu_Vector")

client = chromadb.PersistentClient(path=THU_MUC_KHO)

try:
    # 2. Lấy tủ tài liệu
    collection = client.get_collection(name="tai_lieu_seo")

    # 3. Lấy thử 10 đoạn kiến thức trong kho
    data = collection.peek(limit=10)

    print("\n--- 🔎 KIỂM TRA DỮ LIỆU TRONG KHO ---")
    
    if data['documents']:
        for i in range(len(data['documents'])):
            print(f"\n📍 Đoạn số {i+1}:")
            
            # Dùng .get() để nếu không có 'nguon_goc' thì hiện 'Dữ liệu test' thay vì báo lỗi
            nguon = data['metadatas'][i].get('nguon_goc', 'Dữ liệu hệ thống/Test')
            print(f"📄 Nguồn: {nguon}")
            
            nội_dung = data['documents'][i]
            print(f"📝 Nội dung: {nội_dung[:300]}...") # In 300 chữ đầu cho dễ nhìn
            print("-" * 30)
            
        print(f"\n✅ Tổng cộng đang có {collection.count()} đoạn kiến thức trong não AI.")
    else:
        print("❌ Kho hiện tại vẫn đang trống.")

except Exception as e:
    print(f"❌ Không thể kết nối hoặc kho chưa có dữ liệu: {e}")