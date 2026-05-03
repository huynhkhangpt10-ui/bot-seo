import os
import re
import chromadb
import fitz  # PyMuPDF
from datetime import datetime
import hashlib  # Thêm thư viện Hashing chống trùng

# Đường dẫn kho — tuyệt đối theo vị trí file, tránh lỗi CWD
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
THU_MUC_KHO     = os.path.join(_BASE_DIR, "Kho_Du_Lieu_Vector")
THU_MUC_TAI_LIEU = os.path.join(_BASE_DIR, "Nguon_Tai_Lieu_Tho")
FILE_LOG         = os.path.join(_BASE_DIR, "nhat_ky_nap_kho.txt")


def ghi_log(noi_dung):
    """Hàm ghi log song song: vừa in ra màn hình, vừa lưu vào file txt"""
    thoi_gian = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    dong_log = f"[{thoi_gian}] {noi_dung}"
    print(dong_log)
    with open(FILE_LOG, "a", encoding="utf-8") as f:
        f.write(dong_log + "\n")


def chia_nho_van_ban(text, max_words=300):
    words = text.split()
    chunks = []
    for i in range(0, len(words), max_words):
        chunks.append(" ".join(words[i : i + max_words]))
    return chunks


def tao_ma_bam(text_content):
    """
    Tạo mã băm SHA-256 dựa trên 500 ký tự đầu tiên của nội dung bài viết.
    Giúp nhận diện chính xác 1 bài viết dù tên file có thay đổi.
    """
    chuoi_nhan_dien = text_content[:500].strip()  # Lấy khúc đầu làm vân tay
    return hashlib.sha256(chuoi_nhan_dien.encode("utf-8")).hexdigest()


def nap_vao_kho():
    ghi_log("🚀 BẮT ĐẦU QUY TRÌNH NẠP TÀI LIỆU CÓ CHỐNG TRÙNG LẶP...")

    if not os.path.exists(THU_MUC_TAI_LIEU):
        os.makedirs(THU_MUC_TAI_LIEU)
        ghi_log(f"⚠️ Thư mục nguồn rỗng. Đã tạo mới: {THU_MUC_TAI_LIEU}")
        return

    try:
        client = chromadb.PersistentClient(path=THU_MUC_KHO)
        collection = client.get_or_create_collection(name="tai_lieu_seo")
    except Exception as e:
        ghi_log(f"❌ LỖI KẾT NỐI DATABASE: {e}")
        return

    danh_sach_file = os.listdir(THU_MUC_TAI_LIEU)
    if not danh_sach_file:
        ghi_log("📭 Không tìm thấy file mới nào để nạp.")
        return

    for filename in danh_sach_file:
        filepath = os.path.abspath(os.path.join(THU_MUC_TAI_LIEU, filename))
        if not os.path.isfile(filepath):
            continue

        ghi_log(f"🔍 Đang đọc file: {filename}")
        text_content = ""

        try:
            if filename.lower().endswith(".txt"):
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    text_content = f.read()
            elif filename.lower().endswith(".pdf"):
                doc = fitz.open(filepath)
                for page in doc:
                    text_content += page.get_text()
                doc.close()
            else:
                ghi_log(f"⏩ Bỏ qua file không hỗ trợ: {filename}")
                continue
        except Exception as e:
            ghi_log(f"❌ LỖI ĐỌC FILE {filename}: {e}")
            continue

        if len(text_content.strip()) < 50:
            ghi_log(f"⚠️ Nội dung quá ngắn hoặc rỗng, loại bỏ: {filename}")
            try:
                os.remove(filepath)
            except:
                pass
            continue

        # ==========================================
        # 💥 BỘ LỌC CHỐNG TRÙNG LẶP THẦN THÁNH
        # ==========================================
        ma_hash_bai_viet = tao_ma_bam(text_content)

        # Hỏi xem mã Hash này đã tồn tại trong DB chưa
        kiem_tra = collection.get(
            where={"hash_id": ma_hash_bai_viet},  # Truy vấn theo thuộc tính metadata
            limit=1,
        )

        if kiem_tra and kiem_tra["ids"] and len(kiem_tra["ids"]) > 0:
            ghi_log(
                f"🛑 ĐÃ TRÙNG LẶP NỘI DUNG! Bài viết này đã có trong kho RAG. Bỏ qua: {filename}"
            )
            # Xóa luôn cái file trùng lặp cho đỡ chật ổ cứng
            try:
                os.remove(filepath)
            except:
                pass
            continue

        # Nếu chưa trùng -> Tiến hành băm nhỏ và nạp
        chunks = chia_nho_van_ban(text_content)
        ghi_log(f"⏳ Băm nhỏ thành {len(chunks)} đoạn kiến thức...")

        try:
            for i, chunk in enumerate(chunks):
                # ID đoạn văn bây giờ là mã Hash + Index (Bảo đảm độc nhất toàn cầu)
                doc_id = f"{ma_hash_bai_viet}_{i}"

                collection.upsert(
                    documents=[chunk],
                    metadatas=[
                        {"nguon_goc": filename, "hash_id": ma_hash_bai_viet}
                    ],  # Gắn mã hash vào metadata để sau này check
                    ids=[doc_id],
                )
            ghi_log(f"✅ ĐÃ NẠP XONG VÀ ĐÓNG DẤU CHỐNG TRÙNG: {filename}")

            # Dọn rác sau khi nạp thành công
            os.remove(filepath)
            ghi_log(f"🗑️ Đã xóa file thô: {filename}")
        except Exception as e:
            ghi_log(f"❌ LỖI KHI LƯU VÀO KHO (UPSERT): {e}")

    ghi_log("🎉 KẾT THÚC QUY TRÌNH.")


if __name__ == "__main__":
    nap_vao_kho()
