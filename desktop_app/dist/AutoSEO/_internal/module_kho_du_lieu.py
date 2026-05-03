# File: module_kho_du_lieu.py
import chromadb
import os

THU_MUC_KHO = "./Kho_Du_Lieu_Vector"

def tim_kiem_tai_lieu(tu_khoa, cap_nhat_ui=None, do_chinh_xac=1.2):
    """
    Hàm nhận từ khóa, truy cập kho Vector và báo cáo trạng thái lên UI 1 lần duy nhất.
    """
    try:
        if not os.path.exists(THU_MUC_KHO):
            return ""

        client = chromadb.PersistentClient(path=THU_MUC_KHO)
        collection = client.get_collection(name="tai_lieu_seo")
        
        results = collection.query(
            query_texts=[tu_khoa],
            n_results=2 
        )
        
        # Kiểm tra nếu tìm thấy dữ liệu đạt độ chính xác
        if results['documents'] and len(results['documents'][0]) > 0:
            if results['distances'][0][0] <= do_chinh_xac:
                # ✅ THÔNG BÁO 1 LẦN: Chỉ hiện khi thực sự tìm thấy kiến thức trong kho
                if cap_nhat_ui:
                    cap_nhat_ui("🔥 Đang sử dụng: Bí kíp nội bộ + Dữ liệu Google...")
                
                tai_lieu_gom_duoc = "\n---\n".join(results['documents'][0])
                return tai_lieu_gom_duoc
        
        return ""
        
    except Exception as e:
        print(f"Lỗi kho dữ liệu nội bộ (Bỏ qua): {e}")
        return ""