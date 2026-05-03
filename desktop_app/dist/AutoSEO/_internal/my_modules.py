import re
import unicodedata
import os
import sys
import requests
import time
import random
from urllib.parse import urlparse
from datetime import datetime, timedelta
import streamlit as st
import markdown

# Fix encoding cho Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except:
        pass

from my_config import *
from module_images import ve_va_upload_anh, tao_prompt_anh_software_interface
from module_content import sinh_dan_y, sinh_bai_viet

# =========================================================
# 🕒 HÀM MỚI: TÍNH TOÁN THỜI GIAN LÊN LỊCH "NHỎ GIỌT"
# =========================================================
_dem_so_bai = 0  # Biến đếm toàn cục


def reset_dem_so_bai():
    global _dem_so_bai
    _dem_so_bai = 0


def tinh_gio_dang_nho_giot(stt_bai):
    khung_gio = [9, 14, 20]
    so_bai_trong_ngay = len(khung_gio)

    so_ngay_them = (stt_bai - 1) // so_bai_trong_ngay
    idx_gio = (stt_bai - 1) % so_bai_trong_ngay

    now = datetime.now()
    ngay_dang = now + timedelta(days=so_ngay_them)

    gio_chuan = khung_gio[idx_gio]
    phut_rd = random.randint(5, 55)
    giay_rd = random.randint(0, 59)

    thoi_diem_dang = ngay_dang.replace(hour=gio_chuan, minute=phut_rd, second=giay_rd)

    if thoi_diem_dang < now:
        thoi_diem_dang += timedelta(days=1)

    return thoi_diem_dang.isoformat()


def tao_slug(s):
    if not isinstance(s, str):
        return ""
    s = s.replace("đ", "d").replace("Đ", "d")
    s = unicodedata.normalize("NFKD", s).encode("ASCII", "ignore").decode("utf-8")
    s = re.sub(r"[^\w\s-]", "", s).strip().lower()
    s = re.sub(r"[-\s]+", "-", s)
    return s


TRUSTED_EXTERNAL_DOMAINS = {
    "adobe.com",
    "autodesk.com",
    "coreldraw.com",
    "microsoft.com",
    "wikipedia.org",
    "wikimedia.org",
}


def la_domain_hang_lon(url):
    try:
        hostname = urlparse(url).hostname or ""
    except Exception:
        return False

    hostname = hostname.lower()
    if hostname.startswith("www."):
        hostname = hostname[4:]

    return any(
        hostname == domain or hostname.endswith(f".{domain}")
        for domain in TRUSTED_EXTERNAL_DOMAINS
    )


def rut_gon_tu_khoa(tk):
    if not tk:
        return ""
    words = str(tk).strip().split()
    return " ".join(words[:15])


# =========================================================
# BỘ LỌC DIỆT LINK ẢO GIÁC DO AI BỊA RA
# =========================================================
def diet_link_chet_ai(html_content):
    import re

    # 1. Gỡ bỏ các thẻ link rỗng, link chỉ có dấu #
    html_clean = re.sub(
        r'<a\s+[^>]*href=["\'](?:#|\s*)["\'][^>]*>(.*?)</a>',
        r"\1",
        html_content,
        flags=re.IGNORECASE,
    )
    # 2. Gỡ bỏ các link AI bịa dạng ngoặc vuông href="[URL_chèn_ở_đây]"
    html_clean = re.sub(
        r'<a\s+[^>]*href=["\']\[.*?\]["\'][^>]*>(.*?)</a>',
        r"\1",
        html_clean,
        flags=re.IGNORECASE,
    )
    # 3. Gỡ các link rác trỏ về example.com
    html_clean = re.sub(
        r'<a\s+[^>]*href=["\'][^"\']*example\.com[^"\']*["\'][^>]*>(.*?)</a>',
        r"\1",
        html_clean,
        flags=re.IGNORECASE,
    )
    return html_clean


@st.cache_data(ttl=3600)
def lay_tat_ca_the():
    try:
        response = requests.get(f"{WP_TAGS_URL}?per_page=100")
        return response.json() if response.status_code == 200 else []
    except:
        return []


@st.cache_data(ttl=3600)
def lay_tat_ca_danh_muc():
    try:
        response = requests.get(f"{WP_CAT_URL}?per_page=100")
        return response.json() if response.status_code == 200 else []
    except:
        return []


def check_link_ton_tai(url):
    try:
        r = requests.head(url, timeout=5)
        return r.status_code < 400
    except:
        return False


def get_random_alive_link(k_list, ws_k, excludes=[]):
    temp_list = k_list.copy()
    random.shuffle(temp_list)
    for item in temp_list:
        if item["url"] in excludes:
            continue
        if check_link_ton_tai(item["url"]):
            return item["anchor"], item["url"]
    return "", ""


def dang_bai_zalo_oa(tieu_de, mo_ta, anh_cover_url, html_content, link_web):
    import json

    if not anh_cover_url:
        anh_cover_url = (
            "https://huynhkhang.com/wp-content/uploads/2023/10/logo-huynh-khang.png"
        )
    try:
        with open(ZALO_TOKEN_PATH, "r", encoding="utf-8") as f:
            token = json.load(f).get("access_token")
    except Exception as e:
        return False, f"Lỗi đọc token ({e})"
    if not token:
        return False, "Token rỗng"

    html_zalo = html_content
    html_zalo = re.sub(r"\[.*?\]", "", html_zalo)
    html_zalo = html_zalo.replace(
        '<h3 style="text-align: left;">Tham khảo thêm phần mềm hữu ích:</h3>', ""
    )
    html_zalo = re.sub(
        r"<a\s+[^>]*>(.*?)</a>", r"\1", html_zalo, flags=re.IGNORECASE | re.DOTALL
    )
    html_zalo = re.sub(r"<img\s+[^>]*>", "", html_zalo, flags=re.IGNORECASE)
    html_zalo = re.sub(r"<([a-zA-Z0-9]+)\s+[^>]*>", r"<\1>", html_zalo)

    noi_dung_zalo = f"{html_zalo}<br><br><hr><br>👉 <strong>Xem bài viết gốc tại:</strong> {link_web}"
    url = "https://openapi.zalo.me/v2.0/article/create"
    headers = {"access_token": token, "Content-Type": "application/json"}
    payload = {
        "type": "normal",
        "title": str(tieu_de)[:150],
        "author": "Huỳnh Khang",
        "cover": {
            "cover_type": "photo",
            "photo_url": str(anh_cover_url),
            "status": "show",
        },
        "description": str(mo_ta)[:300],
        "body": [{"type": "text", "content": noi_dung_zalo}],
        "status": "show",
        "comment": "show",
    }
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=15).json()
        return (True, "OK") if res.get("error") == 0 else (False, res.get("message"))
    except Exception as e:
        return False, str(e)


def dang_bai_facebook(tieu_de, html_content, link_web, anh_cover_url=None):
    import json
    import os
    import time
    import requests
    import re
    from datetime import datetime

    fb_file = "fb_pages.json"
    if not os.path.exists(fb_file):
        return False, "Chưa cấu hình FB (Thiếu file)."
    try:
        with open(fb_file, "r", encoding="utf-8") as f:
            pages = json.load(f)
    except:
        return False, "Lỗi đọc file cấu hình FB."
    if not pages:
        return False, "Danh sách Page FB trống."

    text_sach = re.sub(r"<[^>]+>", "", html_content)
    text_sach = re.sub(r"\[.*?\]", "", text_sach)
    text_sach = " ".join(text_sach.split())
    doan_trich = text_sach[:450].rsplit(" ", 1)[0] + "..."

    noi_dung_fb = f"🔥 {tieu_de}\n\n{doan_trich}\n\n👉 Xem chi tiết và tải về tại đây: {link_web}\n\n#DichVuHuynhKhang #HuynhKhangIT"

    ket_qua = []
    ok_any = False

    img_url = (
        anh_cover_url
        if anh_cover_url
        else "https://huynhkhang.com/wp-content/uploads/2023/10/logo-huynh-khang.png"
    )
    img_bytes = None
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        img_res = requests.get(img_url, headers=headers, timeout=15)
        if img_res.status_code == 200:
            img_bytes = img_res.content
    except Exception as e:
        print(f"Lỗi không thể tải ảnh xuyên tường lửa: {e}")

    for idx, page in enumerate(pages):
        page_id = page.get("page_id")
        token = page.get("access_token")
        page_name = page.get("name", "Unknown Page")

        url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
        payload = {"message": noi_dung_fb, "access_token": token}

        try:
            if img_bytes:
                files = {"source": ("image.jpg", img_bytes, "image/jpeg")}
                res = requests.post(url, data=payload, files=files, timeout=30).json()
            else:
                url_feed = f"https://graph.facebook.com/v19.0/{page_id}/feed"
                payload_feed = {
                    "message": noi_dung_fb,
                    "link": link_web,
                    "access_token": token,
                }
                res = requests.post(url_feed, data=payload_feed, timeout=30).json()

            if "id" in res or "post_id" in res:
                ket_qua.append(f"✅ {page_name}")
                ok_any = True
                if idx < len(pages) - 1:
                    time.sleep(60)
            else:
                err_msg = res.get("error", {}).get("message", "Bị FB chặn ẩn")
                ket_qua.append(f"❌ {page_name} (Lỗi Meta: {err_msg})")

                with open("log_loi_facebook.txt", "a", encoding="utf-8") as f:
                    f.write(
                        f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] LỖI TẠI PAGE '{page_name}': {err_msg}\n"
                    )

        except Exception as e:
            ket_qua.append(f"❌ {page_name} (Lỗi hệ thống)")
            with open("log_loi_facebook.txt", "a", encoding="utf-8") as f:
                f.write(
                    f"[{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}] LỖI HỆ THỐNG TẠI PAGE '{page_name}': {str(e)}\n"
                )

    return ok_any, " | ".join(ket_qua)


def tim_link_trang_chu_ai(ten_phan_mem, client_ai):
    prompt = f"""
    Bạn là một chuyên gia IT. Hãy tìm đường link TẢI XUỐNG TỪ TRANG CHỦ CHÍNH THỨC (Official Homepage/GitHub) cho phần mềm: "{ten_phan_mem}".
    
    CRITICAL RULES:
    1. TUYỆT ĐỐI KHÔNG dùng link từ các trang chia sẻ bên thứ 3 (như Softonic, Cnet, Filehippo, Taimienphi, v.v.).
    2. Chỉ chấp nhận link trực tiếp từ tên miền của nhà phát triển, hoặc trang mã nguồn mở như GitHub, SourceForge, Microsoft Store.
    3. Trả về kết quả CHỈ LÀ MỘT CHUỖI JSON ĐƠN GIẢN, KHÔNG GIẢI THÍCH GÌ THÊM.
    
    Định dạng JSON bắt buộc:
    {{"url": "https://link-trang-chu.com", "nguon": "Tên Nhà Phát Triển (VD: GitHub, Microsoft)"}}
    
    Nếu phần mềm này không có thật hoặc không tìm thấy trang chủ an toàn, trả về chuỗi: {{"url": "", "nguon": ""}}
    """
    try:
        res = client_ai.models.generate_content(
            model="gemini-2.5-flash", contents=prompt
        )
        text_res = res.text.strip()
        import json
        import re

        match = re.search(r"\{.*?\}", text_res, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            return data.get("url", ""), data.get("nguon", "")
    except Exception as e:
        print(f"Lỗi tìm link gốc: {e}")
    return "", ""


# =========================================================
# 🚀 HÀM TỔNG TƯ LỆNH: KẾT NỐI TẤT CẢ CÁC MODULE
# =========================================================
# =========================================================
# 🚀 HÀM TỔNG TƯ LỆNH: KẾT NỐI TẤT CẢ CÁC MODULE
# =========================================================
# Sửa dòng này:
def quy_trinh_dang_bai_full(
    tk_auto,
    tieu_de_excel,
    danh_sach_api_keys,
    kho_link_list,
    ws_kho,
    author_block_code,
    flatsome_shortcode,
    danh_sach_dm_id_auto,
    danh_sach_the_id_auto,
    trang_thai_wp,
    cap_nhat_trang_thai_func,
    cho_phep_zalo=False,
    cho_phep_facebook=False,
    cho_phep_web=True,
    row_index=None,
    sh=None,
    link_bai_goc="",
    link_tai_thu_cong="",
):
    if type(cap_nhat_trang_thai_func) == bool:
        return (
            False,
            "🚨 LỖI: Sếp truyền sai thứ tự biến ở vòng lặp for. Hãy sửa lại đúng 16 biến nhé!",
            "",
        )

    cap_nhat_trang_thai_func(f"📝 Đang xử lý: '{tk_auto}'...")

    (
        anchor_1,
        url_1,
        anchor_2,
        url_2,
        anchor_promo,
        url_promo,
        url_tailieu,
        anchor_tailieu,
    ) = ("", "", "", "", "", "", "", "")
    phan_mem_loi = ""
    danh_sach_phan_mem = [
        "adobe after effects",
        "adobe premiere pro",
        "adobe media encoder",
        "media encoder",
        "after effects",
        "adobe photoshop",
        "adobe illustrator",
        "adobe lightroom",
        "adobe indesign",
        "adobe audition",
        "fusion 360",
        "solidworks",
        "coreldraw",
        "camtasia",
        "photoshop",
        "illustrator",
        "premiere",
        "audition",
        "lightroom",
        "indesign",
        "dreamweaver",
        "encoder",
        "bridge",
        "incopy",
        "animate",
        "autocad",
        "3ds max",
        "3d max",
        "revit",
        "sketchup",
        "inventor",
        "office",
        "windows",
        "capcut",
        "maya",
        "vray",
        "corona",
        "lumion",
        "enscape",
        "word",
        "excel",
        "project",
        "microsoft project",
        "visio",
        "microsoft visio",
        "powerpoint",
        "access",
        "outlook",
        "onenote",
        "publisher",
    ]

    DANH_BA_TRANG_CHU = {
        "autocad": "site:autodesk.com",
        "3ds max": "site:autodesk.com",
        "3d max": "site:autodesk.com",
        "revit": "site:autodesk.com",
        "maya": "site:autodesk.com",
        "inventor": "site:autodesk.com",
        "fusion 360": "site:autodesk.com",
        "civil 3d": "site:autodesk.com",
        "navisworks": "site:autodesk.com",
        "photoshop": "site:adobe.com",
        "premiere": "site:adobe.com",
        "illustrator": "site:adobe.com",
        "after effects": "site:adobe.com",
        "lightroom": "site:adobe.com",
        "indesign": "site:adobe.com",
        "coreldraw": "site:coreldraw.com",
        "camtasia": "site:techsmith.com",
        "office": "site:microsoft.com",
        "windows": "site:microsoft.com",
        "intel": "site:intel.com",
        "core i3": "site:intel.com",
        "core i5": "site:intel.com",
        "core i7": "site:intel.com",
        "core i9": "site:intel.com",
        "amd": "site:amd.com",
        "ryzen": "site:amd.com",
        "radeon": "site:amd.com",
        "nvidia": "site:nvidia.com",
        "geforce": "site:nvidia.com",
        "rtx": "site:nvidia.com",
        "gtx": "site:nvidia.com",
        "asus": "site:asus.com",
        "rog": "site:rog.asus.com",
        "tuf": "site:asus.com",
        "gigabyte": "site:gigabyte.com",
        "aorus": "site:gigabyte.com",
        "msi": "site:msi.com",
        "asrock": "site:asrock.com",
        "dell": "site:dell.com",
        "alienware": "site:dell.com",
        "latitude": "site:dell.com",
        "inspiron": "site:dell.com",
        "hp": "site:hp.com",
        "hp pavilion": "site:hp.com",
        "hp elitebook": "site:hp.com",
        "lenovo": "site:lenovo.com",
        "thinkpad": "site:lenovo.com",
        "legion": "site:lenovo.com",
        "acer": "site:acer.com",
        "predator": "site:acer.com",
        "nitro": "site:acer.com",
        "apple": "site:apple.com",
        "macbook": "site:apple.com",
        "imac": "site:apple.com",
        "corsair": "site:corsair.com",
        "kingston": "site:kingston.com",
        "crucial": "site:crucial.com",
        "wd": "site:westerndigital.com",
        "western digital": "site:westerndigital.com",
        "seagate": "site:seagate.com",
        "samsung": "site:samsung.com",
        "logitech": "site:logitech.com",
        "razer": "site:razer.com",
    }

    tk_lower = tk_auto.lower()
    for pm in danh_sach_phan_mem:
        if pm in tk_lower:
            phan_mem_loi = pm
            break

        # ==========================================
        # BỘ NÃO ĐỌC TÀI LIỆU GỐC & TÌM KIẾM AI
        # ==========================================
        lenh_tim_kiem_ai = ""
        tk_lower = str(tk_auto).lower()

        # 1. NẾU SẾP NHẬP LINK TAY TỪ EXCEL (Ưu tiên số 1, ghi đè tất cả)
        if link_bai_goc and link_bai_goc.startswith("http"):
            lenh_tim_kiem_ai = f"""
            [TÀI LIỆU GỐC TỪ KỸ THUẬT VIÊN (ƯU TIÊN 1)]:
            ĐỌC KỸ nội dung tại link này: {link_bai_goc}
            """
            cap_nhat_trang_thai_func(
                f"🔗 Đang đọc tài liệu gốc (Link tay): {link_bai_goc}"
            )

        else:
            # 2. CHUẨN BỊ LỆNH SEARCH GOOGLE (Luôn luôn cần để check giá, check update mới)
            domain_hang = ""
            # DANH_BA_TRANG_CHU phải được định nghĩa ở đầu file hoặc trên đoạn này
            # (Giả sử anh đã có sẵn dictionary DANH_BA_TRANG_CHU trong code)
            try:
                for pm, domain in DANH_BA_TRANG_CHU.items():
                    if pm in tk_lower:
                        domain_hang = domain
                        break
            except:
                pass  # Đề phòng biến DANH_BA_TRANG_CHU chưa khai báo

            chu_de_tieng_anh = ""
            if "lỗi" in tk_lower or "không" in tk_lower:
                chu_de_tieng_anh = "troubleshooting fix error"
            elif "tải" in tk_lower or "download" in tk_lower or "cài đặt" in tk_lower:
                chu_de_tieng_anh = "download install requirements"
            elif "đánh giá" in tk_lower or "có nên" in tk_lower or "review" in tk_lower:
                chu_de_tieng_anh = "review pros cons"
            else:
                chu_de_tieng_anh = "new features updates official"

            # 3. CHUI VÀO KHO VECTOR LỤC LỌI
            try:
                import module_kho_du_lieu

                tai_lieu_kho = module_kho_du_lieu.tim_kiem_tai_lieu(
                    tk_auto, cap_nhat_trang_thai_func
                )
            except Exception as e:
                tai_lieu_kho = ""

            # 4. GỘP CHUNG KHO VÀ MẠNG VÀO 1 PROMPT (HYBRID RAG)
            if tai_lieu_kho:
                lenh_tim_kiem_ai = f"""
                [NGUỒN 1: KINH NGHIỆM KỸ THUẬT NỘI BỘ - BẮT BUỘC BÁM SÁT]:
                Đây là tài liệu chuyên môn chính xác tuyệt đối. Khi viết về nguyên nhân hoặc cách xử lý, phải ưu tiên dùng dữ liệu này:
                {tai_lieu_kho}
                
                [NGUỒN 2: TÌM KIẾM GOOGLE ĐỂ LẤY THÔNG TIN THỜI SỰ]:
                Sau khi nắm vững tài liệu nội bộ ở trên, BẮT BUỘC dùng công cụ Google Search với cú pháp: "{domain_hang} {tk_auto} {chu_de_tieng_anh}"
                Mục đích: Lấy thêm thông tin về giá bán hiện tại, bản cập nhật mới nhất để bổ sung cho bài viết thêm toàn diện.
                """
                cap_nhat_trang_thai_func(
                    "🔥 Đang sử dụng: Bí kíp nội bộ + Dữ liệu Google..."
                )

            else:
                lenh_tim_kiem_ai = f"""
                [LỆNH TÌM KIẾM DỮ LIỆU GỐC (BẮT BUỘC ĐỌC KỸ)]:
                Trước khi viết bài, BẮT BUỘC phải dùng Google Search với cú pháp: "{domain_hang} {tk_auto} {chu_de_tieng_anh}"
                Việc này nhằm lấy dữ liệu thực tế MỚI NHẤT. Bám sát tài liệu chính thức hoặc trang review uy tín.
                """
                cap_nhat_trang_thai_func(
                    f"🔍 Kho rỗng, đang nhả Bot Search Google 100%..."
                )

        # =====================================================================
        # 👇👇 ĐOẠN CODE CŨ CỦA ANH GỌI HÀM SINH DÀN Ý SẼ NẰM NGAY BÊN DƯỚI 👇👇
        # ok_outline, outline_auto, tieu_de_seo_auto, meta_seo_auto, tu_khoa_phu_auto = sinh_dan_y(...)

    # ==========================================================
    # 🟢 BẮT BUỘC CHÈN ĐOẠN NÀY ĐỂ BOT BÁO CÁO LÊN MÀN HÌNH UI
    # ==========================================================
    if link_bai_goc and link_bai_goc.startswith("http"):
        cap_nhat_trang_thai_func(
            f"🔗 Đang tập trung đọc tài liệu gốc (Link tay): {link_bai_goc}"
        )
    elif domain_hang:
        cap_nhat_trang_thai_func(
            f"🔍 Đang nhả Bot Search Google với lệnh: {domain_hang} {tk_auto} {chu_de_tieng_anh}"
        )
    else:
        cap_nhat_trang_thai_func(
            f"🧠 Đang cào dữ liệu tổng hợp trên Google với lệnh: {tk_auto} {chu_de_tieng_anh}"
        )

    time.sleep(
        2.5
    )  # Bắt bot đứng im 2.5 giây để màn hình Streamlit kịp load dòng chữ này lên cho sếp thấy
    # ==========================================================

    if ws_kho:
        hang_chung_chung = ""
        if any(
            x in tk_lower
            for x in [
                "cách",
                "mẹo",
                "thủ thuật",
                "hướng dẫn",
                "ẩn",
                "hiện",
                "tắt",
                "bật",
                "phím tắt",
                "chia ổ",
                "chỉnh",
                "lỗi",
                "cài win",
                "máy tính",
                "laptop",
                "văn phòng",
                "excel",
                "word",
                "office",
                "windows",
            ]
        ):
            hang_chung_chung = "office"
        elif any(
            x in tk_lower
            for x in [
                "adobe",
                "photoshop",
                "illustrator",
                "premiere",
                "after effects",
                "audition",
                "lightroom",
                "dreamweaver",
                "indesign",
                "bridge",
                "incopy",
                "encoder",
                "camtasia",
                "capcut",
                "video",
            ]
        ):
            hang_chung_chung = "adobe"
        elif any(
            x in tk_lower
            for x in [
                "autocad",
                "3ds max",
                "revit",
                "inventor",
                "autodesk",
                "maya",
                "sketchup",
                "solidworks",
                "vray",
                "corona",
            ]
        ):
            hang_chung_chung = "autodesk"
        elif any(x in tk_lower for x in ["coreldraw", "corel"]):
            hang_chung_chung = "corel"
        else:
            import random

            hang_chung_chung = random.choice(["office", "adobe", "autodesk"])

        for item in kho_link_list:
            anch = str(item.get("Từ khóa", item.get("anchor", ""))).strip().lower()
            ur = str(item.get("Link bài viết", item.get("url", ""))).strip().lower()
            if (phan_mem_loi and phan_mem_loi in anch) or (
                hang_chung_chung and hang_chung_chung in anch
            ):
                if "/san-pham/" in ur or "bản quyền" in anch or "giá rẻ" in anch:
                    anchor_promo = str(
                        item.get("Từ khóa", item.get("anchor", ""))
                    ).strip()
                    url_promo = str(
                        item.get("Link bài viết", item.get("url", ""))
                    ).strip()
                    break

        # ==========================================
        # 🎯 ĐỌC DỮ LIỆU TỪ TAB TUKHOA
        # ==========================================
        danh_sach_tu_khoa = []

        # Tạo file log để debug
        log_file = "debug_tukhoa.log"
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"=== DEBUG LOG - {tk_auto} ===\n\n")

            try:
                if sh:
                    f.write(f"✓ Biến sh tồn tại: {type(sh)}\n")
                    # Lấy worksheet "tukhoa" từ spreadsheet object
                    try:
                        ws_tukhoa = sh.worksheet("tukhoa")
                        f.write(f"✓ Đã lấy được worksheet 'tukhoa'\n")
                    except Exception as e_ws:
                        f.write(f"✗ Lỗi lấy worksheet 'tukhoa': {e_ws}\n")
                        # Thử với tên khác
                        try:
                            ws_tukhoa = sh.worksheet("Tukhoa")
                            f.write(f"✓ Đã lấy được worksheet 'Tukhoa' (chữ T hoa)\n")
                        except Exception as e_ws2:
                            f.write(
                                f"✗ Không tìm thấy tab 'tukhoa' hoặc 'Tukhoa': {e_ws2}\n"
                            )
                            ws_tukhoa = None

                    if ws_tukhoa:
                        rows = ws_tukhoa.get_all_values()
                        f.write(f"✓ Đọc được {len(rows)} dòng từ tab tukhoa\n\n")

                        if len(rows) > 1:
                            f.write(f"Header: {rows[0]}\n\n")
                            f.write(f"Đang lọc các bài 'Hoàn thành'...\n")

                            for idx, row in enumerate(rows[1:], start=2):
                                if len(row) >= 4:
                                    anch_tk = str(row[0]).strip()
                                    tt_tk = str(row[2]).strip().lower()
                                    ur_tk = str(row[3]).strip()
                                    link_tai = (
                                        str(row[7]).strip() if len(row) >= 8 else ""
                                    )  # Cột H: Link tải

                                    if idx <= 5:  # Log 5 dòng đầu để kiểm tra
                                        f.write(
                                            f"  Dòng {idx}: anchor='{anch_tk[:50]}', status='{tt_tk}', url='{ur_tk[:50]}', link_tai='{link_tai[:50]}'\n"
                                        )

                                    if (
                                        anch_tk
                                        and ur_tk
                                        and "http" in ur_tk
                                        and "hoàn thành" in tt_tk
                                    ):
                                        danh_sach_tu_khoa.append(
                                            {
                                                "anchor": anch_tk,
                                                "url": ur_tk,
                                                "link_tai": link_tai,
                                            }
                                        )

                            f.write(
                                f"\n✓ Lọc được {len(danh_sach_tu_khoa)} bài 'Hoàn thành'\n"
                            )
                    else:
                        f.write(f"✗ ws_tukhoa là None\n")
                else:
                    f.write(f"✗ Biến sh là None\n")
            except Exception as e:
                f.write(f"✗ Lỗi tổng thể: {e}\n")
                import traceback

                f.write(f"\nTraceback:\n{traceback.format_exc()}\n")

        print(f"📝 Debug log đã được lưu vào: {log_file}")

        # Lọc link hợp lệ (loại bỏ tailieu.huynhkhang và link ngoài domain)
        danh_sach_link_hop_le = []
        for item in danh_sach_tu_khoa:
            ur_check = item["url"].lower()
            # Chỉ giữ link huynhkhang.com, loại bỏ tailieu.huynhkhang
            if "huynhkhang.com" in ur_check and "tailieu.huynhkhang" not in ur_check:
                danh_sach_link_hop_le.append(item)

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"\n✓ Có {len(danh_sach_link_hop_le)} link hợp lệ để random\n")

        # Lọc theo độ liên quan với từ khóa chính
        import random

        anchor_1, url_1, anchor_2, url_2 = "", "", "", ""
        anchor_dich_vu, url_dich_vu = "", ""

        if len(danh_sach_link_hop_le) >= 2:
            # Tách từ khóa chính thành các từ riêng lẻ
            tk_words = set(tk_auto.lower().split())

            # Tính điểm liên quan cho mỗi link
            scored_links = []
            for item in danh_sach_link_hop_le:
                anchor_words = set(item["anchor"].lower().split())
                # Đếm số từ chung
                common_words = tk_words.intersection(anchor_words)
                score = len(common_words)
                scored_links.append((score, item))

            # Sắp xếp theo điểm giảm dần
            scored_links.sort(reverse=True, key=lambda x: x[0])

            # Lấy top 10 bài liên quan nhất (hoặc tất cả nếu ít hơn 10)
            top_links = [item for score, item in scored_links[:10] if score > 0]

            # Nếu không có bài nào liên quan, lấy random từ tất cả
            if len(top_links) < 2:
                top_links = danh_sach_link_hop_le

            # Random 2 link từ danh sách đã lọc
            if len(top_links) >= 2:
                link_random = random.sample(top_links, 2)
                anchor_1, url_1 = link_random[0]["anchor"], link_random[0]["url"]
                anchor_2, url_2 = link_random[1]["anchor"], link_random[1]["url"]

                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"\n✓ Đã chọn 2 link liên quan:\n")
                    f.write(f"  1. {anchor_1}\n")
                    f.write(f"  2. {anchor_2}\n")
            elif len(top_links) == 1:
                anchor_1, url_1 = top_links[0]["anchor"], top_links[0]["url"]
        elif len(danh_sach_link_hop_le) == 1:
            anchor_1, url_1 = (
                danh_sach_link_hop_le[0]["anchor"],
                danh_sach_link_hop_le[0]["url"],
            )

        # ==========================================
        # 🎯 DÙNG LINK TẢI TỪ CỘT H (ĐÃ TRUYỀN VÀO)
        # ==========================================
        link_tai_phan_mem = link_tai_thu_cong.strip() if link_tai_thu_cong else ""

        with open(log_file, "a", encoding="utf-8") as f:
            if link_tai_phan_mem:
                f.write(f"\n✓ Có link tải từ cột H: {link_tai_phan_mem}\n")
            else:
                f.write(f"\n✗ Cột H trống, AI sẽ tự tìm link chính thức\n")

        # Kiểm tra xem có phải phần mềm không
        is_phan_mem = any(pm in tk_lower for pm in danh_sach_phan_mem)

        # Danh sách hãng phần mềm "vip" KHÔNG tạo hộp download
        hang_phan_mem_vip = [
            "autodesk",
            "adobe",
            "camtasia",
            "sketchup",
            "corel",
            "autocad",
            "3ds max",
            "revit",
            "maya",
            "inventor",
            "photoshop",
            "illustrator",
            "premiere",
            "after effects",
            "lightroom",
            "indesign",
        ]
        is_phan_mem_vip = any(hang_vip in tk_lower for hang_vip in hang_phan_mem_vip)

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(
                f"\n✓ Là phần mềm: {is_phan_mem}, Là phần mềm VIP (không tạo hộp download): {is_phan_mem_vip}\n"
            )

        # ==========================================
        # 💥 TÌM LINK TÀI LIỆU CHUẨN XÁC TỪ KHOLINK (Giữ nguyên cho Hộp Tài Liệu Xanh Lá)
        # ==========================================
        import re

        nam_pb_match = re.search(r"\d{4}", tk_auto)
        nam_pb = nam_pb_match.group(0) if nam_pb_match else ""

        danh_sach_tai_lieu_hop_le = []
        tk_kiem_tra = tk_auto.lower().strip()

        for item in kho_link_list:
            anch_goc = str(item.get("Từ khóa", item.get("anchor", ""))).strip()
            ur_goc = str(item.get("Link bài viết", item.get("url", ""))).strip()
            anch = anch_goc.lower()
            ur = ur_goc.lower()

            if "tailieu.huynhkhang" in ur and phan_mem_loi and phan_mem_loi in anch:
                danh_sach_tai_lieu_hop_le.append({"anchor": anch_goc, "url": ur_goc})
                if tk_kiem_tra == anch:  # Khớp 100%
                    anchor_tailieu, url_tailieu = anch_goc, ur_goc
                    break
                elif tk_kiem_tra in anch or anch in tk_kiem_tra:
                    anchor_tailieu, url_tailieu = anch_goc, ur_goc
                    break
                elif nam_pb and (nam_pb in anch or nam_pb in ur):
                    anchor_tailieu, url_tailieu = anch_goc, ur_goc
                    break

        if not url_tailieu and danh_sach_tai_lieu_hop_le:

            def lay_nam(item_k):
                match = re.search(r"\d{4}", item_k["anchor"])
                return int(match.group(0)) if match else 0

            danh_sach_tai_lieu_hop_le.sort(key=lay_nam, reverse=True)

            best_match = danh_sach_tai_lieu_hop_le[0]
            best_match_year = lay_nam(best_match)

            # 🔴 ĐÃ KHÓA MÕM: Nếu từ khóa có năm (vd 2026), mà link vớt được lại là năm khác (vd 2025) -> BỎ NGAY, KHÔNG LẤY BẬY
            if nam_pb and best_match_year > 0 and str(best_match_year) != nam_pb:
                anchor_tailieu, url_tailieu = "", ""
            else:
                anchor_tailieu, url_tailieu = best_match["anchor"], best_match["url"]
        # ==========================================================
    # 🤖 TỰ ĐỘNG KHAI THÁC LSI & MÃ LỖI (VỊ TRÍ CHUẨN)
    # ==========================================================
    cap_nhat_trang_thai_func(f"🧠 Đang đào mã lỗi & từ khóa LSI cho: {tk_auto}...")

    # AI tự chui vào kho tìm mã lỗi và gợi ý từ khóa phụ
    lsi_suggestions = tu_dong_goi_y_lsi(tk_auto, client)

    # Gộp từ khóa từ Excel và từ khóa AI vừa đào được
    tk_phu_tong_hop = f"{tieu_de_excel}, {lsi_suggestions}"

    # Gửi thông báo thành quả
    cap_nhat_trang_thai_func(f"✅ Đã bốc được các mã lỗi: {lsi_suggestions[:100]}...")

    # ✅ SỬA DÒNG NÀY: Phải truyền tk_phu_tong_hop vào đây
    ok, outline_auto, tieu_de_seo_auto, meta_seo_auto, tu_khoa_phu_auto = sinh_dan_y(
        tk_auto,
        tk_phu_tong_hop,  # 👈 Anh phải sửa từ tieu_de_excel thành biến này
        lenh_tim_kiem_ai,
        cap_nhat_trang_thai_func,
    )
    if not ok:
        return False, outline_auto, ""

    chuoi_tu_khoa_ilj = tk_auto
    short_slug_auto = tao_slug(tk_auto)

    # 💥 GÓI GỌN LINK VÀO PROMPT (CHẶN TỰ BỊA)
    link_ins_auto = ""
    if anchor_1 and url_1:
        link_ins_auto += "[LINK DÀNH CHO HỘP BÀI LIÊN QUAN]:\n"
        link_ins_auto += f"- [{anchor_1}]({url_1})\n"
        if anchor_2 and url_2:
            link_ins_auto += f"- [{anchor_2}]({url_2})\n"
    else:
        link_ins_auto += (
            "[LINK DÀNH CHO HỘP BÀI LIÊN QUAN]: TRỐNG! TUYỆT ĐỐI KHÔNG TẠO HỘP NÀY.\n"
        )

    if anchor_dich_vu and url_dich_vu:
        link_ins_auto += f"\n[LINK DỊCH VỤ - BẮT BUỘC CHÈN NGỮ CẢNH]:\n"
        link_ins_auto += f"- [{anchor_dich_vu}]({url_dich_vu})\n"

    import random

    danh_sach_dia_diem = [
        "Quận 1",
        "Quận 3",
        "Quận 4",
        "Quận 5",
        "Quận 6",
        "Quận 7",
        "Quận 8",
        "Quận 10",
        "Quận 11",
        "Quận 12",
        "Bình Thạnh",
        "Gò Vấp",
        "Phú Nhuận",
        "Tân Bình",
        "Tân Phú",
        "Bình Tân",
        "TP Thủ Đức",
        "Bình Chánh",
        "Hóc Môn",
        "Củ Chi",
        "Nhà Bè",
        "Cần Giờ",
    ]
    dia_diem_rd = random.choice(danh_sach_dia_diem)

    tk_check_khach = str(tk_auto).lower()
    if any(
        x in tk_check_khach
        for x in [
            "autocad",
            "3ds max",
            "revit",
            "inventor",
            "maya",
            "autodesk",
            "sketchup",
            "solidworks",
            "corona",
            "vray",
        ]
    ):
        tap_khach_hang = [
            "một văn phòng kiến trúc",
            "một xưởng nội thất",
            "một công ty xây dựng",
            "một anh kỹ sư cầu đường",
            "một bạn sinh viên kiến trúc",
            "một xưởng cơ khí chế tạo",
        ]
    elif any(
        x in tk_check_khach
        for x in [
            "photoshop",
            "illustrator",
            "premiere",
            "after effects",
            "adobe",
            "audition",
            "camtasia",
            "capcut",
            "corel",
            "indesign",
        ]
    ):
        tap_khach_hang = [
            "một studio áo cưới",
            "một tiệm in ấn quảng cáo",
            "một bạn Youtuber/Tiktoker",
            "một công ty truyền thông",
            "một bạn sinh viên thiết kế đồ họa",
            "một shop thời trang (cần chỉnh ảnh sản phẩm)",
        ]
    elif any(
        x in tk_check_khach
        for x in [
            "sửa",
            "lỗi",
            "không lên",
            "hư",
            "bảo trì",
            "cài win",
            "máy tính",
            "laptop",
            "nguồn",
            "màn hình",
            "vệ sinh",
        ]
    ):
        tap_khach_hang = [
            "anh em game thủ",
            "một bạn sinh viên",
            "một phòng khám nha khoa",
            "một shop quần áo",
            "một chị kế toán",
            "một công ty bất động sản",
            "dân văn phòng",
        ]
    else:
        tap_khach_hang = [
            "một chị kế toán",
            "một văn phòng luật sư",
            "một trung tâm ngoại ngữ",
            "một bạn sinh viên",
            "một khách hàng cá nhân",
            "dân văn phòng",
        ]

    khach_hang_rd = random.choice(tap_khach_hang)

    from datetime import datetime

    ok, bai_viet_auto = sinh_bai_viet(
        tk_auto,
        tieu_de_seo_auto,
        short_slug_auto,
        link_ins_auto,
        outline_auto,
        datetime.now().year,
        khach_hang_rd,
        dia_diem_rd,
        lenh_tim_kiem_ai,
        cap_nhat_trang_thai_func,
        link_tai_phan_mem,
        is_phan_mem,
        is_phan_mem_vip,
    )
    if not ok:
        return False, bai_viet_auto, ""

    bai_viet_text_auto = re.sub(r"^#\s+", "## ", bai_viet_auto, flags=re.MULTILINE)
    cac_khoi = re.split(r"^##\s+", bai_viet_text_auto, flags=re.MULTILINE)

    phan_sapo = cac_khoi[0].strip()[:500] if len(cac_khoi) > 0 else tk_auto
    prompt_dai_dien = tao_prompt_anh_software_interface(tk_auto, phan_sapo)

    feat_id_auto, feat_url_auto = None, None
    kq_dai_dien = ve_va_upload_anh(
        prompt_dai_dien, tk_auto, tieu_de_seo_auto[:50], short_slug_auto
    )
    if kq_dai_dien and isinstance(kq_dai_dien, tuple) and len(kq_dai_dien) == 2:
        feat_id_auto, feat_url_auto = kq_dai_dien

    if not feat_id_auto:
        return (
            False,
            "❌ Lỗi vẽ ảnh Đại diện (Google từ chối hoặc đứt mạng). Hủy bài viết!",
            "",
        )

    new_lines_auto = []
    if cac_khoi[0].strip():
        new_lines_auto.append(cac_khoi[0].strip())

    for khoi in cac_khoi[1:]:
        dong_list = khoi.strip().split("\n")
        if not dong_list:
            continue

        heading_text_auto = (
            dong_list[0]
            .strip()
            .replace("**", "")
            .replace("*", "")
            .replace('"', "")
            .replace("'", "")
        )
        noi_dung_h2 = "\n".join(dong_list[1:]).strip()

        new_lines_auto.append(f"\n## {heading_text_auto}")

        tu_khoa_ne_anh = ["faq", "câu hỏi", "kết luận", "tổng kết", "lời kết"]
        if not any(tu_khoa in heading_text_auto.lower() for tu_khoa in tu_khoa_ne_anh):
            prompt_heading = tao_prompt_anh_software_interface(
                heading_text_auto, noi_dung_h2[:500]
            )
            cap_nhat_trang_thai_func(
                f"🎨 Đang vẽ ảnh cho H2: '{heading_text_auto[:30]}'..."
            )

            try:
                kq_ve = ve_va_upload_anh(
                    prompt_heading, tk_auto, heading_text_auto[:50], short_slug_auto
                )
                if kq_ve and isinstance(kq_ve, tuple) and len(kq_ve) == 2:
                    _, h_url = kq_ve
                    if h_url:
                        new_lines_auto.append(
                            f'\n<br><div style="text-align: center;"><img src="{h_url}" alt="{heading_text_auto}"></div><br>\n'
                        )
            except Exception as e:
                print(f"⚠️ Bỏ qua ảnh H2 do lỗi: {e}")

        new_lines_auto.append(noi_dung_h2)

    import markdown

    html_content_auto = markdown.markdown(
        "\n".join(new_lines_auto), extensions=["tables"]
    )

    html_content_auto = diet_link_chet_ai(html_content_auto)

    # TỰ ĐỘNG CHÈN NÚT TẢI PHẦN MỀM CHÍNH CHỦ
    phan_mem_vip_nha_lam = [
        "adobe",
        "autodesk",
        "corel",
        "sketchup",
        "camtasia",
        "office",
        "windows",
        "3ds max",
        "autocad",
        "photoshop",
        "illustrator",
        "premiere",
        "after effects",
        "vray",
        "corona",
        "revit",
    ]
    la_phan_mem_vip = any(vip in tk_lower for vip in phan_mem_vip_nha_lam)

    # 💥 DANH SÁCH 50+ PHẦN MỀM TIỆN ÍCH PHỔ BIẾN (ĐÃ LỌC TỪ DỄ NHẦM LẪN)
    phan_mem_tien_ich = [
        "ultraviewer",
        "teamviewer",
        "anydesk",
        "unikey",
        "evkey",
        "vietkey",
        "zalo",
        "chrome",
        "cốc cốc",
        "coccoc",
        "firefox",
        "microsoft edge",
        "brave",
        "obs studio",
        "idm",
        "winrar",
        "7-zip",
        "7zip",
        "telegram",
        "viber",
        "skype",
        "capcut",
        "camtasia",
        "bandicam",
        "format factory",
        "kmplayer",
        "vlc media",
        "foxit reader",
        "nitro pdf",
        "pdf24",
        "adobe acrobat reader",
        "ccleaner",
        "rufus",
        "crystaldiskinfo",
        "cpuz",
        "cpu-z",
        "gpuz",
        "hwmonitor",
        "kaspersky",
        "bkav",
        "eset",
        "avast",
        "malwarebytes",
        "xampp",
        "vmware",
        "virtualbox",
        "project",
    ]
    la_bai_tai_phan_mem = any(
        x in tk_lower
        for x in ["tải", "download", "phần mềm", "cài đặt", "tool", "app", "ứng dụng"]
    ) or any(x in tk_lower for x in phan_mem_tien_ich)

    if not la_phan_mem_vip and la_bai_tai_phan_mem:

        # 🟢 ƯU TIÊN 1: LẤY LINK TẢI THỦ CÔNG TỪ EXCEL (CỘT H)
        if link_tai_thu_cong and link_tai_thu_cong.startswith("http"):
            cap_nhat_trang_thai_func(
                f"🎯 Đã nhận link tải chuẩn từ file đầu vào. Bỏ qua Bot Search!"
            )
            link_official = link_tai_thu_cong
            if "drive.google.com" in link_tai_thu_cong:
                nguon_official = "Google Drive (Tốc độ cao)"
            elif "microsoft.com" in link_tai_thu_cong:
                nguon_official = "Trang chủ Microsoft"
            else:
                nguon_official = "Trang chủ Official"
        else:
            # 🔴 ƯU TIÊN 2: NẾU EXCEL TRỐNG, NHẢ BOT ĐI TÌM TRÊN MẠNG
            cap_nhat_trang_thai_func(
                f"🔍 Đang huy động AI săn link trang chủ gốc cho: {tk_auto}..."
            )
            link_official, nguon_official = tim_link_trang_chu_ai(tk_auto, client)

        if link_official and link_official.startswith("http"):
            bang_tai_chinh_chu_html = f"""
<div style="background-color: #f0f9ff; border: 1px solid #bae6fd; border-radius: 8px; padding: 20px; text-align: center; margin: 30px 0; font-family: inherit;">
    <h3 style="color: #0369a1; font-size: 20px; margin: 0 0 10px 0;">Tải {tk_auto} Mới Nhất</h3>
    <p style="color: #334155; font-size: 15px; margin: 0 0 15px 0;">Phiên bản ổn định, tương thích tốt với Windows 10 và Windows 11.</p>
    <a href="{link_official}" target="_blank" rel="nofollow noopener" style="display: inline-block; background-color: #0056b3; color: #ffffff !important; padding: 12px 25px; border-radius: 6px; font-weight: 700; font-size: 16px; text-decoration: none; box-shadow: 0 4px 6px rgba(0, 86, 179, 0.3); transition: background 0.3s;">
        Tải Ngay Tại {nguon_official}
    </a>
    <p style="color: #64748b; font-size: 12px; margin: 12px 0 0 0; font-style: italic;">* Lưu ý: Link tải đã được đội ngũ kỹ thuật kiểm duyệt an toàn.</p>
</div>
"""
            html_content_auto = re.sub(
                r"(<h2\b[^>]*>)",
                f"{bang_tai_chinh_chu_html}\n\\1",
                html_content_auto,
                count=1,
                flags=re.IGNORECASE,
            )
            cap_nhat_trang_thai_func(f"✅ Đã đóng đinh link tải từ {nguon_official}!")

    if url_tailieu:
        cum_tu_action = random.choice(
            ["Tải", "Download", "Hướng dẫn cài đặt", "Xem tài liệu", "Tải & Cài đặt"]
        )
        anchor_da_dang = f"{cum_tu_action} {anchor_tailieu}"
        cta_html = f"""\n<div style="background-color: #e8f5e9; padding: 15px; border-left: 5px solid #2e7d32; margin: 25px 0; border-radius: 4px;">\n📚 <strong>XEM THÊM TÀI LIỆU CHI TIẾT:</strong> Đang tìm kiếm hướng dẫn tải, cài đặt và các tài liệu chuyên sâu cho phần mềm này? Tham khảo ngay bài viết tại Kho Tài Liệu của chúng tôi: 👉 <strong><a href="{url_tailieu}" target="_blank" rel="nofollow">{anchor_da_dang}</a></strong>\n</div>\n"""
        html_content_auto = html_content_auto.replace("<h2>", f"{cta_html}\n<h2>", 1)

    if anchor_promo and url_promo:
        promo_box = f"""\n<div style="background-color: #f0f7ff; padding: 15px; border-left: 5px solid #0056b3; margin: 25px 0; border-radius: 4px;">\n🔥 <strong>GÓC TÀI TRỢ:</strong> Đang tìm kiếm phần mềm? Tham khảo ngay dịch vụ <strong><a href="{url_promo}" target="_blank">{anchor_promo}</a></strong> chính hãng, giá cực sốc tại HuynhKhang.com!\n</div>\n"""
        html_content_auto = html_content_auto.replace("<h2>", f"{promo_box}\n<h2>", 1)

    html_content_auto = (
        html_content_auto.replace("<p>", '<p style="text-align: justify;">')
        .replace("<h2>", '<h2 style="text-align: left;">')
        .replace("<h3>", '<h3 style="text-align: left;">')
    )

    def xu_ly_link_seo(match):
        href, tag = match.group(1), match.group(0)
        tag_sach = re.sub(r'\s*(target|rel)="[^"]*"', "", tag)
        href_lower = href.lower()

        if (
            "huynhkhang.com" in href_lower
            and "tailieu.huynhkhang.com" not in href_lower
        ):
            return tag_sach
        if "tailieu.huynhkhang.com" in href_lower:
            return tag_sach.replace(">", ' target="_blank" rel="nofollow noopener">')
        if href.startswith("http"):
            if la_domain_hang_lon(href):
                return tag_sach.replace(">", ' target="_blank" rel="noopener">')
            return tag_sach.replace(">", ' target="_blank" rel="nofollow noopener">')
        return tag

    html_content_auto = re.sub(
        r'<a\s+[^>]*href=["\']([^"\']+)["\'][^>]*>',
        xu_ly_link_seo,
        html_content_auto,
        flags=re.IGNORECASE,
    )

    block_quang_cao_hang = ""
    if any(
        x in tk_lower
        for x in [
            "cách",
            "mẹo",
            "thủ thuật",
            "hướng dẫn",
            "ẩn",
            "hiện",
            "tắt",
            "bật",
            "phím tắt",
            "chia ổ",
            "chỉnh",
            "lỗi",
            "office",
            "windows",
            "win 10",
            "win 11",
            "excel",
            "word",
            "cài win",
            "visio",
            "project",
            "microsoft visio",
            "microsoft project",
        ]
    ):
        block_quang_cao_hang = '[block id="key-win-office"]'
    elif any(
        x in tk_lower
        for x in [
            "photoshop",
            "illustrator",
            "premiere",
            "after effects",
            "adobe",
            "audition",
            "camtasia",
            "capcut",
            "video",
        ]
    ):
        block_quang_cao_hang = '[block id="adobe"]'
    elif any(
        x in tk_lower
        for x in [
            "autocad",
            "3ds max",
            "revit",
            "inventor",
            "maya",
            "autodesk",
            "sketchup",
            "solidworks",
        ]
    ):
        block_quang_cao_hang = '[block id="autodesk"]'
    elif any(x in tk_lower for x in ["coreldraw", "corel"]):
        block_quang_cao_hang = '[block id="coreldraw"]'
    elif any(
        x in tk_lower
        for x in ["dịch vụ", "sửa chữa", "máy tính", "laptop", "không lên", "hư"]
    ):
        danh_sach_chen_com = [
            '[block id="adobe"]',
            '[block id="autodesk"]',
            '[block id="coreldraw"]',
            '[block id="key-win-office"]',
        ]
        block_quang_cao_hang = random.choice(danh_sach_chen_com)

    if block_quang_cao_hang:
        html_quang_cao = f'\n<div style="margin: 35px 0; text-align: center;">{block_quang_cao_hang}</div>\n'
        h2_tags = list(re.finditer(r"<h2.*?>", html_content_auto, flags=re.IGNORECASE))

        if len(h2_tags) >= 2:
            vi_tri_cat = h2_tags[1].start()
            html_content_auto = (
                html_content_auto[:vi_tri_cat]
                + html_quang_cao
                + html_content_auto[vi_tri_cat:]
            )
        elif len(h2_tags) == 1:
            vi_tri_cat = h2_tags[0].end()
            html_content_auto = (
                html_content_auto[:vi_tri_cat]
                + html_quang_cao
                + html_content_auto[vi_tri_cat:]
            )
        else:
            html_content_auto += html_quang_cao

    # Khối minh bạch nội dung AI
    khoi_tac_gia_html = """
    <div style="border-left: 4px solid #0068ff; padding: 12px 15px; background-color: #eff6ff; margin: 20px 0; font-size: 14.5px; color: #334155; border-radius: 0 8px 8px 0;">
    🤖 <strong>Minh bạch nội dung:</strong> Bài viết được hỗ trợ biên soạn bởi AI và đã qua kiểm duyệt chuyên môn thực tế bởi đội ngũ kỹ thuật <strong>HuynhKhang.com</strong>.
    </div>
    """

    # 💥 KHÔI PHỤC BLOCK TÁC GIẢ: Bắt đúng mã Shortcode sếp chọn trên giao diện UI
    ux_block_shortcode = '[block id="tac-gia-bai-viet"]'

    # Gộp tất cả vào cuối bài viết theo đúng thứ tự
    html_content_auto += f'\n{khoi_tac_gia_html}\n{ux_block_shortcode}\n<h3 style="text-align: left;">Tham khảo thêm bài viết:</h3>\n{flatsome_shortcode}'

    # ==========================================
    # 5. UP LÊN WEB VÀ ZALO/FACEBOOK
    # ==========================================
    l_bai = ""
    if cho_phep_web:
        cap_nhat_trang_thai_func("🚀 Đang bắn bài lên Web và ILJ...")
        thoi_gian_dang_bai = None
        if trang_thai_wp == "scheduled":
            global _dem_so_bai
            _dem_so_bai += 1
            thoi_gian_dang_bai = tinh_gio_dang_nho_giot(_dem_so_bai)
            post_status_api = "future"
            cap_nhat_trang_thai_func(
                f"⏳ Lên lịch đăng tự động lúc: {thoi_gian_dang_bai.replace('T', ' ')}"
            )
        elif trang_thai_wp == "publish_now":
            post_status_api = "publish"
            cap_nhat_trang_thai_func("🔥 Đang xuất bản bài viết lên Web ngay lập tức!")
        else:
            post_status_api = "draft"
            cap_nhat_trang_thai_func("📝 Đang lưu bài viết vào mục Nháp.")

        post_data = {
            "title": tieu_de_seo_auto,
            "content": html_content_auto,
            "status": post_status_api,
            "slug": short_slug_auto,
            "categories": danh_sach_dm_id_auto,
            "tags": danh_sach_the_id_auto,
            "ilj_link_keywords": chuoi_tu_khoa_ilj,
            "meta": {
                "rank_math_focus_keyword": tk_auto,
                "rank_math_title": tieu_de_seo_auto,
                "rank_math_description": meta_seo_auto,
                "rank_math_rich_snippet": "article",
            },
            "featured_media": feat_id_auto,
        }
        if thoi_gian_dang_bai:
            post_data["date"] = thoi_gian_dang_bai

        import requests

        try:
            wp_res = requests.post(
                WP_POSTS_URL, auth=(WP_USER, WP_APP_PASS), json=post_data, timeout=60
            )
            if wp_res.status_code == 201:
                l_bai = wp_res.json().get("link")
            else:
                return False, f"Lỗi đăng WP: {wp_res.text}", ""
        except Exception as e:
            return False, f"Lỗi mạng khi đăng WP: {e}", ""
    else:
        l_bai = "Nháp / Chưa đăng lên Web"

    if cho_phep_zalo:
        cap_nhat_trang_thai_func("📱 Đang bắn bài sang Zalo OA...")
        ok_zl, msg_zl = dang_bai_zalo_oa(
            tieu_de_seo_auto, meta_seo_auto, feat_url_auto, html_content_auto, l_bai
        )
        if ok_zl:
            cap_nhat_trang_thai_func("🎉 Đã lên bài Zalo OA thành công!")
        else:
            cap_nhat_trang_thai_func(f"⚠️ Lỗi đăng Zalo OA: {msg_zl}")

    if cho_phep_facebook:
        cap_nhat_trang_thai_func("🌐 Đang đẩy bài sang Facebook Pages...")
        ok_fb, msg_fb = dang_bai_facebook(
            tieu_de_seo_auto, html_content_auto, l_bai, feat_url_auto
        )
        if ok_fb:
            cap_nhat_trang_thai_func(f"🎉 Đã lên bài FB: {msg_fb}")
        else:
            cap_nhat_trang_thai_func(f"⚠️ Lỗi đăng FB: {msg_fb}")

    return True, "Hoàn thành xuất sắc", l_bai


def tu_dong_goi_y_lsi(tk_chinh, client_ai):
    """
    Hàm tự động đào từ khóa phụ (LSI) và mã lỗi từ kho tài liệu nội bộ.
    """
    # 1. Truy vấn kho dữ liệu để lấy kiến thức thực tế
    import module_kho_du_lieu

    du_lieu_kho = module_kho_du_lieu.tim_kiem_tai_lieu(tk_chinh)

    prompt_lsi = f"""
    Bạn là chuyên gia SEO Technical. Với từ khóa chính: "{tk_chinh}", hãy tìm các từ khóa phụ (LSI) chất lượng cao.
    Dựa trên dữ liệu thực tế này (nếu có): {du_lieu_kho}
    
    Hãy trả về danh sách từ khóa chia làm 3 nhóm:
    1. Mã lỗi cụ thể (VD: Error 1603, Error 2...).
    2. Thành phần hệ thống (VD: ODIS, Registry Editor, .NET Framework...).
    3. Câu hỏi Long-tail (VD: Cách gỡ sạch AutoCAD, Tại sao cài Revit báo lỗi...).
    
    Chỉ trả về danh sách các từ khóa, cách nhau bởi dấu phẩy. Không giải thích thêm.
    """
    try:
        # Sử dụng client AI để phân tích và trích xuất từ khóa
        res = client_ai.models.generate_content(
            model="gemini-2.0-flash", contents=prompt_lsi
        )
        return res.text.strip()
    except Exception as e:
        print(f"Lỗi gợi ý LSI: {e}")
        return ""
