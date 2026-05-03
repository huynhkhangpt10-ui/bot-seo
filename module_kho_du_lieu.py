# File: module_kho_du_lieu.py
import chromadb
import os
import sys

def _log(msg: str):
    """In log an toàn với UTF-8 — tránh UnicodeEncodeError trên Windows CP1252."""
    try:
        sys.stdout.buffer.write((msg + "\n").encode("utf-8", errors="replace"))
        sys.stdout.buffer.flush()
    except Exception:
        pass

# Dùng đường dẫn tuyệt đối dựa theo vị trí file này — tránh lỗi CWD
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
THU_MUC_KHO = os.path.join(_BASE_DIR, "Kho_Du_Lieu_Vector")

# Ngưỡng distance tối đa — ChromaDB L2: 0=giống hệt, 2=hoàn toàn khác
# Mặc định 1.8 để lấy được kết quả liên quan một phần
NGUONG_DISTANCE = 1.8

def tim_kiem_tai_lieu(tu_khoa, cap_nhat_ui=None, do_chinh_xac=None):
    """
    Hàm nhận từ khóa, truy cập kho Vector và báo cáo trạng thái lên UI 1 lần duy nhất.
    """
    if do_chinh_xac is None:
        do_chinh_xac = NGUONG_DISTANCE

    try:
        if not os.path.exists(THU_MUC_KHO):
            _log(f"[RAG] Kho chua ton tai: {THU_MUC_KHO}")
            return ""

        client = chromadb.PersistentClient(path=THU_MUC_KHO)

        try:
            collection = client.get_collection(name="tai_lieu_seo")
        except Exception:
            _log("[RAG] Collection 'tai_lieu_seo' chua co trong kho.")
            return ""

        so_chunks = collection.count()
        if so_chunks == 0:
            _log("[RAG] Kho rong (0 chunks).")
            return ""

        # Giới hạn n_results không vượt quá số chunk thực tế
        n = min(3, so_chunks)
        results = collection.query(
            query_texts=[tu_khoa],
            n_results=n
        )

        # Kiểm tra kết quả
        docs = results.get('documents', [[]])[0]
        dists = results.get('distances', [[]])[0]

        if not docs:
            _log(f"[RAG] No chunks found for keyword: '{tu_khoa}'")
            return ""

        # Log distance để debug (dùng stdout với utf-8 để tránh UnicodeEncodeError)
        _log(f"[RAG] keyword='{tu_khoa}' | chunks={so_chunks} | "
             f"best_distance={dists[0]:.3f} (threshold={do_chinh_xac})")

        # Lấy tất cả kết quả trong ngưỡng
        tai_lieu_list = [d for d, dist in zip(docs, dists) if dist <= do_chinh_xac]

        if not tai_lieu_list:
            _log(f"[RAG] Distance {dists[0]:.3f} > threshold {do_chinh_xac} -> skip")
            return ""

        if cap_nhat_ui:
            cap_nhat_ui("🔥 Đang sử dụng: Bí kíp nội bộ + Dữ liệu Google...")

        return "\n---\n".join(tai_lieu_list)

    except Exception as e:
        import traceback
        _log(f"[RAG] ERROR: {e}\n{traceback.format_exc()}")
        return ""