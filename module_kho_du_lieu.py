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


def _get_collection_or_none():
    """Tra ve collection 'tai_lieu_seo' hoac None."""
    try:
        if not os.path.exists(THU_MUC_KHO):
            return None
        client = chromadb.PersistentClient(path=THU_MUC_KHO)
        return client.get_collection(name="tai_lieu_seo")
    except Exception:
        return None


def lay_danh_sach_file_tu_kho_rag(batch: int = 2000) -> tuple[int, list[str], str]:
    """
    Quet metadatas theo lo, lay duy ten file (basename) unique, sap xep.
    Tra ve: (so_chunks, danh_sach_ten_file, loi).
    """
    loi = ""
    try:
        col = _get_collection_or_none()
        if col is None:
            return 0, [], "Chua co kho hoac collection."
        total = col.count()
        if total == 0:
            return 0, [], ""
        nguon = set()
        offset = 0
        while offset < total:
            lim = min(batch, total - offset)
            chunk = col.get(limit=lim, offset=offset, include=["metadatas"])
            metas = chunk.get("metadatas") or []
            if not metas:
                break
            for m in metas:
                src = m.get("source") or m.get("nguon_goc", "")
                if src:
                    nguon.add(os.path.basename(str(src)))
            offset += len(metas)
        return total, sorted(nguon), ""
    except Exception as e:
        return 0, [], str(e)


def chia_hai_cot_danh_sach_stt(danh_sach_file: list[str]) -> tuple[list[str], list[str]]:
    """
    Giong giao dien nguoi dung: cot trai 1,3,5... cot phai 2,4,6...
    Moi dong: "ten_file.pdf {so_thu_tu}."
    """
    trai, phai = [], []
    for i, name in enumerate(danh_sach_file):
        stt = i + 1
        line = f"{name} {stt}."
        if i % 2 == 0:
            trai.append(line)
        else:
            phai.append(line)
    return trai, phai


def lay_mau_chunk_rag(gioi_han: int = 5) -> list[tuple[str, str]]:
    """Tra ve [(ten_file, preview), ...]"""
    out = []
    try:
        col = _get_collection_or_none()
        if col is None or col.count() == 0:
            return out
        items = col.get(limit=gioi_han, include=["documents", "metadatas"])
        for doc, meta in zip(
            items.get("documents", []),
            items.get("metadatas", []),
        ):
            src = os.path.basename(str(meta.get("source", "") or meta.get("nguon_goc", "")))
            prev = (doc or "")[:400].replace("\n", " ").strip()
            out.append((src, prev))
    except Exception:
        pass
    return out


def lay_du_lieu_xem_kho_rag(so_mau: int = 5) -> dict:
    """
    Goi du lieu day du cho UI 'Xem Kho' (Streamlit/desktop).
    """
    so_chunks, files, err_scan = lay_danh_sach_file_tu_kho_rag()
    trai, phai = chia_hai_cot_danh_sach_stt(files)
    mau = [{"file": s, "preview": p} for s, p in lay_mau_chunk_rag(so_mau)]
    return {
        "so_chunks": so_chunks,
        "so_file": len(files),
        "files": files,
        "cot_trai": trai,
        "cot_phai": phai,
        "mau": mau,
        "loi": err_scan,
    }