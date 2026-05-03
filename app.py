import sys
import streamlit as st
import pandas as pd
import json
import gspread
import time
import markdown
import re
import random
import requests
import os
import urllib.parse
from datetime import datetime, timedelta
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx

# Fix encoding cho Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except:
        pass

from satellite_worker import thuc_thi_ban_ve_tinh
from my_config import *

# 💥 ĐÂY LÀ ĐƯỜNG DÂY MÁU: NÓ SẼ GỌI TOÀN BỘ HÀM XỬ LÝ TỪ MY_MODULES.PY SANG
from my_modules import *
from module_content import (
    sinh_dan_y,
    sinh_bai_viet,
)  # Lấy trực tiếp từ content cho tab Thủ công
import seo_doctor


# ==========================================
# 💥 BẢN VÁ LỖI: HÀM GỌI API CÓ AUTH TRỰC TIẾP TRONG APP.PY
# (Ép quyền Admin để khắc phục lỗi WordPress ẩn Tags/Categories)
# ==========================================
@st.cache_data(ttl=3600)
def lay_tat_ca_the_auth():
    try:
        response = requests.get(
            f"{WP_TAGS_URL}?per_page=100", auth=(WP_USER, WP_APP_PASS), timeout=15
        )
        return response.json() if response.status_code == 200 else []
    except Exception as e:
        print(f"Lỗi lấy Tags: {e}")
        return []


@st.cache_data(ttl=3600)
def lay_tat_ca_danh_muc_auth():
    try:
        response = requests.get(
            f"{WP_CAT_URL}?per_page=100", auth=(WP_USER, WP_APP_PASS), timeout=15
        )
        return response.json() if response.status_code == 200 else []
    except Exception as e:
        print(f"Lỗi lấy Categories: {e}")
        return []


# ==========================================

# ==========================================
# 💾 BỘ NHỚ LƯU CẤU HÌNH UI
# ==========================================
UI_FILE = "ui_settings.json"


def load_ui_settings():
    if os.path.exists(UI_FILE):
        try:
            with open(UI_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


ui_data = load_ui_settings()


def get_safe_index(danh_sach, gia_tri):
    try:
        return danh_sach.index(gia_tri)
    except:
        return 0


# ==========================================

st.set_page_config(page_title="Bot AI Huỳnh Khang - System Manager", layout="wide")
st.title("🤖 Cỗ Máy SEO Auto 100% - Phân Hệ Modules")

if "outline" not in st.session_state:
    st.session_state.outline = ""
if "step1_done" not in st.session_state:
    st.session_state.step1_done = False
if "bai_viet" not in st.session_state:
    st.session_state.bai_viet = ""
if "step2_done" not in st.session_state:
    st.session_state.step2_done = False
if "tieu_de_seo" not in st.session_state:
    st.session_state.tieu_de_seo = ""
if "meta_seo" not in st.session_state:
    st.session_state.meta_seo = ""

st.sidebar.header("⚙️ Cấu Hình Đăng Bài (Mặc định)")
danh_muc_du_lieu = lay_tat_ca_danh_muc_auth()
ten_cac_danh_muc = (
    [dm["name"] for dm in danh_muc_du_lieu]
    if danh_muc_du_lieu
    else ["Phần Mềm", "Tin Tức"]
)

cat_index = get_safe_index(ten_cac_danh_muc, ui_data.get("danh_muc"))
danh_muc_chon = st.sidebar.selectbox(
    "Chọn Danh Mục (Dùng chung cho toàn bộ Sheet):", ten_cac_danh_muc, index=cat_index
)

# 🟢 CÔNG TẮC 3 CHẾ ĐỘ ĐĂNG BÀI ĐỈNH CAO 🟢
list_trang_thai = [
    "⏱️ Lên lịch tự động (Drip-feed 3 bài/ngày)",
    "🔥 Đăng nóng ngay lập tức (Real-time)",
    "📝 Lưu nháp (Draft)",
]
stt_index = get_safe_index(list_trang_thai, ui_data.get("trang_thai"))
trang_thai = st.sidebar.selectbox(
    "Trạng thái bài viết:", list_trang_thai, index=stt_index
)

st.sidebar.markdown("**📱 Các Kênh Đăng Bài:**")
cho_phep_web = st.sidebar.checkbox(
    "🌍 Đăng lên Website (WordPress)", value=ui_data.get("dang_web", True)
)
cho_phep_zalo = st.sidebar.checkbox(
    "🚀 Tự động đẩy bài sang Zalo OA", value=ui_data.get("dang_zalo", False)
)
cho_phep_facebook = st.sidebar.checkbox(
    "🌐 Tự động đẩy bài sang Facebook Pages", value=ui_data.get("dang_fb", False)
)

if "Lên lịch" in trang_thai and (cho_phep_zalo or cho_phep_facebook):
    st.sidebar.error(
        "🚨 LƯU Ý: Sếp đang chọn Hẹn Giờ mà lại bật Zalo/FB!\n\nBài trên Web sẽ bị giấu đi chờ đến ngày đăng, nếu bắn link lên Zalo/FB bây giờ khách bấm vào sẽ bị LỖI 404. Vui lòng tắt Zalo/FB nếu chạy Auto số lượng lớn."
    )

with st.sidebar.expander("📘 Quản lý Facebook Pages", expanded=False):
    fb_file = "fb_pages.json"
    if os.path.exists(fb_file):
        try:
            with open(fb_file, "r", encoding="utf-8") as f:
                fb_pages = json.load(f)
        except:
            fb_pages = []
    else:
        fb_pages = []

    st.markdown("**Danh sách Page đang lưu:**")
    if not fb_pages:
        st.caption("Chưa có Page nào.")
    else:
        for i, p in enumerate(fb_pages):
            cols = st.columns([4, 1])
            cols[0].write(f"- {p['name']}")
            if cols[1].button("Xóa", key=f"del_fb_{i}"):
                fb_pages.pop(i)
                with open(fb_file, "w", encoding="utf-8") as f:
                    json.dump(fb_pages, f, ensure_ascii=False, indent=4)
                st.rerun()

    st.markdown("---")
    st.markdown("**Thêm Page mới:**")
    new_fb_name = st.text_input("Tên Page (để nhớ):")
    new_fb_id = st.text_input("Page ID:")
    new_fb_token = st.text_input("Page Access Token:")
    if st.button("➕ Thêm Page"):
        if new_fb_name and new_fb_id and new_fb_token:
            fb_pages.append(
                {
                    "name": new_fb_name,
                    "page_id": new_fb_id,
                    "access_token": new_fb_token,
                }
            )
            with open(fb_file, "w", encoding="utf-8") as f:
                json.dump(fb_pages, f, ensure_ascii=False, indent=4)
            st.success("Đã thêm thành công!")
            time.sleep(1)
            st.rerun()
        else:
            st.warning("Sếp điền đủ 3 ô nhé!")

with st.sidebar.expander("🛠 Cấu hình Khối Cuối Bài", expanded=False):
    danh_sach_block = {
        "🧑‍💻 Tác giả bài viết": '[block id="tac-gia-bai-viet"]',
        "🤠 Tác giả Bình Dương": '[block id="tac-gia-binh-duong"]',
        "📞 TT liên hệ ngoài BD": '[block id="thong-tin-lien-he-ngoai-bd"]',
        "❌ Không chèn Block nào": "",
    }
    ten_block_chon = st.selectbox("👉 Chọn Block:", list(danh_sach_block.keys()))
    author_block_code = danh_sach_block[ten_block_chon]
    flatsome_shortcode = st.text_area(
        "Mã Slider Phần Mềm:",
        '[blog_posts style="normal" columns="4" category="tin-tuc" posts="8" orderby="rand" show_date="false" excerpt="false" show_category="false" comments="false" image_height="56.25%" auto_slide="4000"]',
    )

the_du_lieu = lay_tat_ca_the_auth()
st.sidebar.markdown("**🏷 Thẻ bài viết (Dùng chung cho toàn bộ Sheet):**")
ten_cac_the = [the["name"] for the in the_du_lieu]
the_da_luu = [tag for tag in ui_data.get("the_bai", []) if tag in ten_cac_the]
the_duoc_chon = st.sidebar.multiselect(
    "Chọn thẻ bài viết:", ten_cac_the, default=the_da_luu
)

st.sidebar.markdown("---")
if st.sidebar.button("💾 Lưu Cấu Hình Mặc Định Này"):
    new_settings = {
        "danh_muc": danh_muc_chon,
        "trang_thai": trang_thai,
        "dang_web": cho_phep_web,
        "dang_zalo": cho_phep_zalo,
        "dang_fb": cho_phep_facebook,
        "the_bai": the_duoc_chon,
    }
    with open(UI_FILE, "w", encoding="utf-8") as f:
        json.dump(new_settings, f, ensure_ascii=False, indent=4)
    st.sidebar.success("✅ Đã lưu cấu hình! Lần sau F5 sẽ không bị mất nữa.")


# ==========================================
# KHU VỰC TABS (GIAO DIỆN STREAMLIT)
# ==========================================
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    [
        "✍️ Chế Độ Thủ Công",
        "⚡ Chế Độ Tự Động",
        "🩺 Bác Sĩ SEO",
        "🚀 Trạm Bắn Vệ Tinh",
        "📚 Kho Dữ Liệu (RAG)",
        "🕷️ Cào Web -> PDF",
    ]
)

# ----------------- TAB 1: THỦ CÔNG -----------------
with tab1:
    st.subheader("Quy trình duyệt tay từng bài")
    col1, col2 = st.columns(2)
    with col1:
        tk_chinh_goc = st.text_input("🔑 Từ khóa chính:")
    with col2:
        tk_phu = st.text_area("🗝 Chủ đề/Từ khóa phụ:", height=68)

    st.markdown("---")
    st.markdown("**🔗 Chèn Link Nội Bộ:**")
    col_link1, col_link2 = st.columns(2)
    with col_link1:
        anchor_1 = st.text_input("Từ khóa Link 1 (Dưới mở bài):")
        url_1 = st.text_input("URL 1:")
    with col_link2:
        anchor_2 = st.text_input("Từ khóa Link 2 (Giữa bài):")
        url_2 = st.text_input("URL 2:")

    st.markdown("**🌍 Chèn Link Ngoài:**")
    col_out1, col_out2 = st.columns(2)
    with col_out1:
        outbound_anchor = st.text_input("Từ khóa Link Ngoài:")
    with col_out2:
        outbound_url = st.text_input("URL Link Ngoài:")
    st.markdown("---")

    if st.button("1️⃣ Lên Dàn Ý & Viết Thẻ SEO", type="primary"):
        if tk_chinh_goc:
            tk_chinh = rut_gon_tu_khoa(tk_chinh_goc)
            with st.spinner(
                f"Đang phân tích Search Intent cho từ khóa: '{tk_chinh}'..."
            ):

                def update_msg(m):
                    pass

                ok, outline, title, meta, keywords = sinh_dan_y(
                    tk_chinh, tk_phu, "", update_msg
                )

                if ok:
                    st.session_state.tieu_de_seo = title
                    st.session_state.meta_seo = meta
                    st.session_state.outline = outline
                    st.session_state.step1_done = True
                    st.success("🎉 Dàn ý chuẩn SEO E-E-A-T đã xong!")
                else:
                    st.error(f"Lỗi AI: {outline}")
        else:
            st.warning("⚠️ Nhập từ khóa chính đi anh ơi!")

    if st.session_state.step1_done:
        tk_chinh = rut_gon_tu_khoa(tk_chinh_goc)
        st.session_state.tieu_de_seo = st.text_input(
            "📌 Tiêu đề SEO:", st.session_state.tieu_de_seo
        )
        st.session_state.meta_seo = st.text_area(
            "📌 Thẻ mô tả SEO:", st.session_state.meta_seo, height=68
        )
        st.session_state.outline = st.text_area(
            "📝 Khung Dàn Ý:", st.session_state.outline, height=250
        )

        if st.button("2️⃣ Viết Bài", type="primary"):
            with st.spinner("Chuyên gia Huỳnh Khang đang múa phím..."):
                short_slug = tao_slug(tk_chinh)
                link_instruction = ""
                if anchor_1 and url_1:
                    link_instruction += f"\n- Link Nội Bộ 1 (DƯỚI MỞ BÀI): 👉 **Xem thêm: [{anchor_1}]({url_1})**"
                if anchor_2 and url_2:
                    link_instruction += (
                        f"\n- Link Nội Bộ 2 (GIỮA BÀI): **[{anchor_2}]({url_2})**"
                    )
                if outbound_anchor and outbound_url:
                    link_instruction += (
                        f"\n- Liên Kết Ngoài: **[{outbound_anchor}]({outbound_url})**."
                    )

                dia_diem_temp = random.choice(
                    ["Tân Uyên", "Thuận An", "Dĩ An", "Quận 9"]
                )
                khach_temp = random.choice(
                    ["một văn phòng thiết kế", "anh em game thủ", "một bạn sinh viên"]
                )

                def update_msg(m):
                    pass

                ok, content = sinh_bai_viet(
                    tk_chinh,
                    st.session_state.tieu_de_seo,
                    short_slug,
                    link_instruction,
                    st.session_state.outline,
                    datetime.now().year,
                    khach_temp,
                    dia_diem_temp,
                    "",
                    update_msg,
                )

                if ok:
                    st.session_state.bai_viet = content
                    st.session_state.step2_done = True
                    st.success("🎉 Bài viết đã hoàn thiện theo đúng module!")
                else:
                    st.error(f"Lỗi: {content}")

# ----------------- TAB 2: TỰ ĐỘNG GOOGLE SHEETS -----------------
with tab2:
    st.subheader("⚡ Cỗ Máy Kết Nối Trực Tiếp Google Sheets")
    col_gs1, col_gs2 = st.columns(2)
    with col_gs1:
        gs_url = st.text_input(
            "🔗 Đường dẫn (URL) Google Sheets:",
            "https://docs.google.com/spreadsheets/d/1c7FDAe4HASvEGU15WDAK8IkcyaULKh3OquWL7FZfXfA/edit#gid=0",
        )
    with col_gs2:
        gs_sheet_name = st.text_input("Tên Tab trong Sheets:", "Tukhoa")

    st.caption(
        "✅ Hệ thống đã được nâng cấp: Loại bỏ rác thừa, gọi điện thẳng vào API lõi."
    )

    if gs_url:
        try:
            if not os.path.exists(GOOGLE_KEY_PATH):
                st.error("❌ KHÔNG TÌM THẤY FILE KEY!")
                st.stop()
            gc = gspread.service_account(filename=GOOGLE_KEY_PATH)
            sh = gc.open_by_url(gs_url)
            worksheet = sh.worksheet(gs_sheet_name)
            df = pd.DataFrame(worksheet.get_all_records())
            if not df.empty:
                headers = df.columns.tolist()
            else:
                headers = []

            try:
                ws_kho = sh.worksheet("KhoLink")
                kho_data = ws_kho.get_all_values()
                kho_link_list = []
                if len(kho_data) > 1:
                    for i, r in enumerate(kho_data[1:]):
                        if (
                            len(r) >= 2
                            and str(r[1]).startswith("http")
                            and "lỗi" not in str(r[2]).lower()
                        ):
                            kho_link_list.append(
                                {
                                    "row": i + 2,
                                    "anchor": str(r[0]).strip(),
                                    "url": str(r[1]).strip(),
                                }
                            )
            except:
                ws_kho = None
                kho_link_list = []

            st.success("✅ Đã kết nối Google Sheets thành công!")
            st.markdown("---")

            df_hien_thi = df[df["Trạng thái"] != "Hoàn thành"]
            st.write("📊 **Danh sách các từ khóa ĐANG CHỜ xử lý:**")

            if df_hien_thi.empty:
                st.info("Sạch sẽ! Không còn bài nào đang chờ.")
            else:
                cols_to_show = ["Từ khóa"]
                if "Từ khóa phụ" in df_hien_thi.columns:
                    cols_to_show.append("Từ khóa phụ")
                cols_to_show.extend(["Trạng thái", "Link bài viết"])
                cols_to_show = [c for c in cols_to_show if c in df_hien_thi.columns]
                st.dataframe(df_hien_thi[cols_to_show])

            try:
                col_trang_thai = headers.index("Trạng thái") + 1
                col_link_bai = headers.index("Link bài viết") + 1
            except:
                st.error(
                    "❌ Lỗi: Sheets không có cột 'Trạng thái' hoặc 'Link bài viết'."
                )
                st.stop()

            if st.button("🧹 1. Quét & Lọc Từ Khóa Trùng Lặp Ý Định"):
                with st.spinner("AI đang phân tích Search Intent toàn bộ danh sách..."):
                    list_tk = df[df["Trạng thái"] == ""]["Từ khóa"].tolist()
                    if list_tk:
                        prompt_loc = f"""Bạn là chuyên gia SEO. Dưới đây là danh sách từ khóa.
Nhiệm vụ: Phân tích Ý định tìm kiếm (Search Intent). Nếu có các từ khóa khác chữ nhưng mang cùng 1 ý định tìm kiếm, hãy chọn 1 từ hay nhất để giữ lại, và LOẠI BỎ từ còn lại.
TRẢ VỀ DUY NHẤT danh sách các từ khóa CẦN BỊ LOẠI BỎ, mỗi từ khóa cách nhau bởi dấu |. Nếu không có từ nào bị trùng, trả về KHONG_CO.
Danh sách: {list_tk}"""
                        try:
                            from my_config import client

                            res_loc = client.models.generate_content(
                                model="gemini-2.5-flash", contents=prompt_loc
                            )
                            tu_khoa_loai_bo = [
                                tk.strip()
                                for tk in res_loc.text.strip().split("|")
                                if tk.strip()
                            ]
                            count_loai = 0
                            if "KHONG_CO" not in tu_khoa_loai_bo:
                                for idx, row in df.iterrows():
                                    if row["Từ khóa"] in tu_khoa_loai_bo:
                                        row_sheet = idx + 2
                                        worksheet.update_cell(
                                            row_sheet,
                                            col_trang_thai,
                                            "Trùng lặp ý định (Bỏ qua)",
                                        )
                                        count_loai += 1
                            st.success(
                                f"✅ Đã quét xong! Loại bỏ {count_loai} từ khóa trùng lặp. Đã lưu trực tiếp lên Sheets!"
                            )
                            time.sleep(2)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Lỗi khi quét: {e}")

            if st.button("🚀 2. KHỞI ĐỘNG CỖ MÁY AUTO", type="primary"):
                try:
                    ws_api = sh.worksheet("API_KEY")
                    danh_sach_api_keys = [
                        k.strip() for k in ws_api.col_values(1)[1:] if k.strip()
                    ][::-1]
                except:
                    st.error("⚠️ Lỗi không tìm thấy Tab API_KEY")
                    st.stop()

                danh_sach_cho = df[(df["Trạng thái"] == "") & (df["Từ khóa"] != "")]
                reset_dem_so_bai()

                if len(danh_sach_cho) == 0:
                    st.warning("⚠️ Không có từ khóa nào hợp lệ.")
                else:
                    st.success(f"🔥 Bắt đầu chạy {len(danh_sach_cho)} bài viết...")
                    progress_bar = st.progress(0)
                    so_luong_tong = len(danh_sach_cho)
                    dem = 0

                    for idx, row in danh_sach_cho.iterrows():
                        row_sheet = idx + 2

                        try:
                            worksheet.update_cell(
                                row_sheet, col_trang_thai, "⏳ Đang viết bài..."
                            )
                        except:
                            pass

                        tk_auto = rut_gon_tu_khoa(str(row["Từ khóa"]).strip())
                        tk_phu_excel = str(row.get("Từ khóa phụ", "")).strip()

                        link_goc_excel = ""
                        try:
                            if "Link Bài Gốc" in row:
                                link_goc_excel = str(row["Link Bài Gốc"]).strip()
                            elif "Link tham khảo" in row:
                                link_goc_excel = str(row["Link tham khảo"]).strip()
                            elif len(row.values) >= 7:
                                link_goc_excel = str(row.values[6]).strip()
                            if not link_goc_excel.startswith("http"):
                                link_goc_excel = ""
                        except:
                            pass

                        link_tai_tay = ""
                        try:
                            if len(row.values) >= 8:
                                link_tai_tay = str(row.values[7]).strip()
                            if not link_tai_tay.startswith("http"):
                                link_tai_tay = ""
                        except:
                            pass

                        danh_sach_dm_id_auto = (
                            [
                                dm["id"]
                                for dm in danh_muc_du_lieu
                                if dm["name"] == danh_muc_chon
                            ]
                            if danh_muc_du_lieu
                            else []
                        )
                        danh_sach_the_id_auto = (
                            [
                                the["id"]
                                for the in the_du_lieu
                                if the["name"] in the_duoc_chon
                            ]
                            if the_duoc_chon
                            else []
                        )

                        if "Lên lịch" in trang_thai:
                            wp_status_auto = "scheduled"
                        elif "Đăng nóng" in trang_thai:
                            wp_status_auto = "publish_now"
                        else:
                            wp_status_auto = "draft"

                        with st.expander(f"⏳ Đang xử lý: {tk_auto}", expanded=True):
                            if f"seen_{tk_auto}" not in st.session_state:
                                st.session_state[f"seen_{tk_auto}"] = set()

                            def cap_nhat_ui(msg):
                                if msg not in st.session_state[f"seen_{tk_auto}"]:
                                    st.write(msg)
                                    st.session_state[f"seen_{tk_auto}"].add(msg)

                            thanh_cong, msg_tt, link_bai = quy_trinh_dang_bai_full(
                                tk_auto=tk_auto,
                                tieu_de_excel=tk_phu_excel,
                                danh_sach_api_keys=danh_sach_api_keys,
                                kho_link_list=kho_link_list,
                                ws_kho=ws_kho,
                                author_block_code=author_block_code,
                                flatsome_shortcode=flatsome_shortcode,
                                danh_sach_dm_id_auto=danh_sach_dm_id_auto,
                                danh_sach_the_id_auto=danh_sach_the_id_auto,
                                trang_thai_wp=wp_status_auto,
                                cap_nhat_trang_thai_func=cap_nhat_ui,
                                cho_phep_zalo=cho_phep_zalo,
                                cho_phep_facebook=cho_phep_facebook,
                                cho_phep_web=cho_phep_web,
                                row_index=row_sheet,
                                sh=sh,
                                link_bai_goc=link_goc_excel,
                                link_tai_thu_cong=link_tai_tay,
                            )

                            if thanh_cong:
                                worksheet.update_cell(
                                    row_sheet, col_trang_thai, "Hoàn thành"
                                )
                                worksheet.update_cell(row_sheet, col_link_bai, link_bai)

                                if ws_kho and link_bai.startswith("http"):
                                    try:
                                        ws_kho.append_row([tk_auto, link_bai, "Sống"])
                                        kho_link_list.append(
                                            {
                                                "row": 999,
                                                "anchor": tk_auto,
                                                "url": link_bai,
                                            }
                                        )
                                    except:
                                        pass

                                st.success(f"✅ Đã xử lý xong! (Link: {link_bai})")

                                if link_bai.startswith("http"):
                                    cap_nhat_ui(
                                        "🚀 Đang bắn tín hiệu ép Google Index bài mới..."
                                    )
                                    ok_index, msg_index = seo_doctor.ep_index_url(
                                        link_bai
                                    )
                                    if ok_index:
                                        cap_nhat_ui(f"🎉 {msg_index}")
                                    else:
                                        cap_nhat_ui(f"⚠️ {msg_index}")
                            else:
                                worksheet.update_cell(
                                    row_sheet, col_trang_thai, f"Lỗi: {msg_tt}"
                                )
                                st.error(f"❌ Bị lỗi bài {tk_auto}: {msg_tt}")

                        dem += 1
                        progress_bar.progress(dem / so_luong_tong)

                        if dem < so_luong_tong:
                            thoi_gian_cho = random.randint(300, 600)
                            phut = thoi_gian_cho // 60
                            giay = thoi_gian_cho % 60
                            with st.spinner(
                                f"☕ Đăng xong 1 bài! Bot đang đi uống cafe nghỉ {phut} phút {giay} giây để lách luật Spam..."
                            ):
                                time.sleep(thoi_gian_cho)

                    st.balloons()
                    st.success("🎉 CỖ MÁY ĐÃ HOÀN THÀNH CHIẾN DỊCH!")
                    time.sleep(2)
                    st.rerun()
        except Exception as e:
            st.error(f"Lỗi hệ thống: {e}")

# ----------------- TAB 3: BÁC SĨ SEO -----------------
with tab3:
    st.header("🩺 Trung Tâm Chẩn Đoán & Phẫu Thuật SEO")
    site_url = "https://huynhkhang.com/"
    service = seo_doctor.ket_noi_gsc()

    if not service:
        st.error("⚠️ Kết nối Search Console thất bại.")
    else:
        st.subheader("📅 Thiết lập thời gian quét")
        days_select = st.selectbox(
            "Soi dữ liệu trong vòng:",
            [7, 14, 30, 60, 90, 180],
            index=2,
            format_func=lambda x: f"{x} ngày qua",
        )

        st.divider()
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("⚔️ Check Ăn Thịt Từ Khóa", use_container_width=True):
                df_seo = seo_doctor.fetch_gsc_data(
                    service, site_url, days_start=days_select
                )
                st.session_state.seo_result = seo_doctor.audit_cannibalization(df_seo)
                st.session_state.seo_type = "Ăn thịt từ khóa"
        with c2:
            if st.button("📉 Tìm Bài Tụt Hạng", use_container_width=True):
                st.session_state.seo_result = seo_doctor.audit_content_decay(
                    service, site_url
                )
                st.session_state.seo_type = "Tụt hạng traffic"
        with c3:
            if st.button("🧟 Diệt Trang Thây Ma", use_container_width=True):
                df_seo = seo_doctor.fetch_gsc_data(
                    service, site_url, days_start=days_select
                )
                st.session_state.seo_result = seo_doctor.audit_zombie_pages(
                    service, site_url
                )
                st.session_state.seo_type = "Trang thây ma (0 Click)"

        c4, c5 = st.columns(2)
        with c4:
            if st.button("🔬 Nội Soi Full On-Page", use_container_width=True):
                df_base = seo_doctor.fetch_gsc_data(
                    service, site_url, days_start=days_select
                )
                st.session_state.seo_result = seo_doctor.audit_onpage_full(df_base)
                st.session_state.seo_type = "Lỗi On-page kỹ thuật"
        with c5:
            if st.button("🎯 Lọc Organic (Bỏ Brand)", use_container_width=True):
                df_seo = seo_doctor.fetch_gsc_data(
                    service, site_url, days_start=days_select
                )
                st.session_state.seo_result = seo_doctor.audit_organic_only(df_seo)
                st.session_state.seo_type = "Từ khóa tiềm năng"

        st.divider()
        st.subheader("🎯 Trạm Khai Thác Từ Khóa GSC")
        st.caption(
            "Tự động hút từ khóa tiềm năng (Impressions cao, Clicks thấp) và lọc bỏ các 'Ông kẹ'."
        )

        if st.button(
            "💎 VÉT MÁNG & BƠM VÀO SHEETS", type="primary", use_container_width=True
        ):
            with st.spinner("Đang soi GSC và đối chiếu danh sách Blacklist..."):
                try:
                    current_kws = df["Từ khóa"].tolist() if "df" in locals() else []
                    count = seo_doctor.fetch_and_push_to_sheets(
                        service, site_url, worksheet, current_kws
                    )

                    if count > 0:
                        st.success(
                            f"✅ Đã lọc sạch và bơm thành công {count} từ khóa mới vào Sheets!"
                        )
                        st.balloons()
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.warning(
                            "⚠️ Không tìm thấy từ khóa nào mới đạt chuẩn hoặc đã bị Blacklist chặn hết."
                        )
                except NameError:
                    st.error(
                        "⚠️ Sếp phải qua Tab 2 dán link Sheets để kết nối trước thì em mới biết chỗ mà bơm chứ!"
                    )

        st.subheader("⚡ Trạm Nạp Năng Lượng: Kiểm Tra & Ép Index Hàng Loạt")
        st.caption(
            "Quota Google cấp: Kiểm tra 2.000 link/ngày | Ép Index 200 link/ngày."
        )

        url_input_index = st.text_area(
            "🔗 Nhập danh sách URL (Mỗi dòng 1 link):",
            placeholder="https://huynhkhang.com/bai-viet-1/\nhttps://huynhkhang.com/bai-viet-2/\nhttps://huynhkhang.com/bai-viet-3/",
            height=150,
        )

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🔍 Check Index Hàng Loạt", use_container_width=True):
                if url_input_index:
                    urls = [u.strip() for u in url_input_index.split("\n") if u.strip()]
                    with st.spinner(
                        f"Đang soi trạng thái {len(urls)} link trên Google..."
                    ):
                        for u in urls:
                            ok, msg = seo_doctor.check_url_index(site_url, u)
                            if ok:
                                st.success(f"{u} ➔ {msg}")
                            else:
                                st.warning(f"{u} ➔ {msg}")
                else:
                    st.warning("Sếp dán danh sách Link vào ô đã nhé!")

        with col_btn2:
            if st.button(
                "🚀 Ép Index Hàng Loạt", type="primary", use_container_width=True
            ):
                if url_input_index:
                    urls = [u.strip() for u in url_input_index.split("\n") if u.strip()]
                    with st.spinner(
                        f"Đang thúc đít Google Bot chui vào {len(urls)} link..."
                    ):
                        thanh_cong = 0
                        for u in urls:
                            ok, msg = seo_doctor.ep_index_url(u)
                            if ok:
                                st.success(f"✅ {u} ➔ Bắn tín hiệu thành công!")
                                thanh_cong += 1
                            else:
                                st.error(f"❌ {u} ➔ Lỗi: {msg}")
                        if thanh_cong > 0:
                            st.balloons()
                            st.info(
                                f"🎉 Hoàn tất ép index cho {thanh_cong}/{len(urls)} bài viết!"
                            )
                else:
                    st.warning("Sếp dán danh sách Link vào ô đã nhé!")

        st.divider()

        if "seo_result" in st.session_state:
            res_goc = st.session_state.seo_result
            tp = st.session_state.seo_type

            if res_goc.empty:
                st.success(f"✅ Website của sếp đang rất khỏe mạnh ở mục: {tp}")
            else:
                st.subheader(f"📊 Kết quả chẩn đoán: {tp}")

                res_hien_thi = res_goc.copy()
                res_hien_thi.insert(0, "👉 Chọn", False)

                st.caption(
                    "👇 Sếp TÍCH VÀO Ô VUÔNG ở cột '👉 Chọn' để đưa bài viết vào phòng phẫu thuật nhé!"
                )

                edited_df = st.data_editor(
                    res_hien_thi,
                    hide_index=True,
                    column_config={
                        "👉 Chọn": st.column_config.CheckboxColumn(required=True)
                    },
                    disabled=res_goc.columns.tolist(),
                    use_container_width=True,
                )

                import io

                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                    res_goc.to_excel(writer, index=False, sheet_name="Chẩn Đoán SEO")

                st.download_button(
                    label="📊 Tải Bảng Dữ Liệu Này (File Excel .xlsx Chuẩn)",
                    data=buffer.getvalue(),
                    file_name=f"Bao_Cao_{tp}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                )

                st.divider()
                selected_rows = edited_df[edited_df["👉 Chọn"] == True]

                if not selected_rows.empty:
                    st.markdown("### 🛠️ Phòng Phẫu Thuật SEO (Tuân thủ quy trình)")
                    row_data = selected_rows.iloc[0]

                    danh_sach_url_de_mo = []
                    if "URL" in row_data:
                        danh_sach_url_de_mo = [row_data["URL"]]
                    elif "Danh sách bài" in row_data:
                        danh_sach_url_de_mo = [
                            u.strip()
                            for u in str(row_data["Danh sách bài"]).split("|")
                            if u.strip()
                        ]

                    if danh_sach_url_de_mo:
                        if len(danh_sach_url_de_mo) > 1:
                            st.warning(
                                f"⚠️ Từ khóa **'{row_data['Từ khóa']}'** đang có {len(danh_sach_url_de_mo)} bài tranh chấp. Sếp muốn điều trị bài nào?"
                            )
                            selected_url = st.radio(
                                "📌 Chọn 1 URL cụ thể để mổ:", danh_sach_url_de_mo
                            )
                        else:
                            selected_url = danh_sach_url_de_mo[0]
                            st.info(f"📌 Đang phẫu thuật URL: **{selected_url}**")

                        if "current_url" not in st.session_state:
                            st.session_state.current_url = selected_url
                        if selected_url != st.session_state.current_url:
                            st.session_state.current_url = selected_url
                            if "phac_do_hien_tai" in st.session_state:
                                del st.session_state["phac_do_hien_tai"]

                        if st.button(
                            "🩺 BƯỚC 1: AI Khám Bệnh & Lên Phác Đồ Điều Trị",
                            type="primary",
                            use_container_width=True,
                        ):
                            with st.spinner(
                                f"AI đang soi kỹ bệnh án của bài: {selected_url}..."
                            ):
                                loi_khuyen = seo_doctor.ke_don_seo_ai(
                                    row_data, tp, selected_url
                                )
                                st.session_state.phac_do_hien_tai = loi_khuyen

                        if (
                            "phac_do_hien_tai" in st.session_state
                            and st.session_state.phac_do_hien_tai
                        ):
                            st.markdown("---")
                            st.markdown("### 💊 Phác Đồ Điều Trị (Toa Thuốc):")

                            with st.expander(
                                "👉 Bấm để xem chi tiết Phác Đồ", expanded=True
                            ):
                                st.write(st.session_state.phac_do_hien_tai)

                            col_sx1, col_sx2, col_sx3 = st.columns(3)
                            with col_sx1:
                                loi_khuyen_sach = (
                                    st.session_state.phac_do_hien_tai.replace("**", "")
                                    .replace("##", "")
                                    .replace("*", "•")
                                )
                                st.download_button(
                                    label="📥 Tải Phác Đồ Này Ra Word",
                                    data=loi_khuyen_sach,
                                    file_name=f"Phac_Do_{tp}.doc",
                                    mime="application/msword",
                                    use_container_width=True,
                                )

                            with col_sx2:
                                if st.button(
                                    "🩹 BƯỚC 2: Mổ Bài Viết Theo Phác Đồ",
                                    use_container_width=True,
                                ):
                                    with st.spinner(
                                        "AI đang đọc phác đồ và tiến hành 'mổ' bài viết..."
                                    ):
                                        ok, msg = (
                                            seo_doctor.phau_thuat_nang_cap_bai_viet(
                                                selected_url,
                                                tp,
                                                st.session_state.phac_do_hien_tai,
                                            )
                                        )
                                        if ok:
                                            st.success(
                                                "✅ Phẫu thuật thành công! Bài viết đã được nâng cấp trên Web."
                                            )
                                            st.balloons()
                                            with st.spinner(
                                                "🚀 Đang gọi Googlebot vào Index bài vừa sửa..."
                                            ):
                                                ok_index, msg_index = (
                                                    seo_doctor.ep_index_url(
                                                        selected_url
                                                    )
                                                )
                                                if ok_index:
                                                    st.success(msg_index)
                                                else:
                                                    st.warning(msg_index)
                                        else:
                                            st.error(f"Lỗi phẫu thuật: {msg}")

                            with col_sx3:
                                if st.button(
                                    "🔗 Tạo Mã Redirect 301", use_container_width=True
                                ):
                                    target = st.text_input(
                                        "Nhập URL chính muốn giữ lại:"
                                    )
                                    if target:
                                        st.code(
                                            f"Redirect 301 {selected_url.replace(site_url[:-1], '')} {target}"
                                        )
                else:
                    st.info(
                        "👆 Sếp hãy TÍCH CHỌN 1 ô vuông trên bảng để đưa bài viết vào Phòng Phẫu Thuật nhé!"
                    )

# ----------------- TAB 4: BẮN VỆ TINH -----------------
with tab4:
    st.header("🚀 Trạm Bắn Vệ Tinh - Khang IT")
    st.markdown(
        "Hệ thống tự động sinh 'Ma trận Content' và rải link ngẫu nhiên lên 5 Site vệ tinh."
    )

    st.subheader("⚙️ Cấu Hình Chống Spam (Anti-Spam Brakes)")
    col1, col2, col3 = st.columns(3)

    with col1:
        quota_day = st.number_input(
            "🎯 Quota (Số bài tối đa/ngày)", min_value=1, max_value=50, value=10
        )
    with col2:
        max_satellite_posts = st.number_input(
            "♻️ Số bài vệ tinh/1 Từ khóa", min_value=1, max_value=5, value=3
        )
    with col3:
        sleep_time = st.slider(
            "⏳ Thời gian nghỉ (Phút) Random từ:",
            min_value=10,
            max_value=180,
            value=(45, 120),
        )

    st.caption(
        f"*Bot sẽ tự động nghỉ ngẫu nhiên từ {sleep_time[0]} đến {sleep_time[1]} phút sau mỗi lần đăng.*"
    )
    st.divider()

    st.subheader("🌐 Mạng Lưới Vệ Tinh")
    st.info("Trạng thái kết nối API: Blogger (✅), WordPress (✅), Tumblr (✅)")

    st.subheader("📊 Nguyên Liệu Sẵn Sàng (Từ Khóa Đã 'Hoàn thành')")

    try:
        if "Trạng thái" in df.columns:
            df_ve_tinh = df[df["Trạng thái"] == "Hoàn thành"].copy()

            if "Số bài Vệ tinh" not in df_ve_tinh.columns:
                df_ve_tinh["Số bài Vệ tinh"] = "0/3"

            df_hien_thi_vt = df_ve_tinh[["Từ khóa", "Trạng thái", "Số bài Vệ tinh"]]

            if df_hien_thi_vt.empty:
                st.info(
                    "Hiện tại chưa có từ khóa nào đạt trạng thái 'Hoàn thành' để bắn vệ tinh."
                )
            else:
                st.dataframe(df_hien_thi_vt, use_container_width=True)
                st.caption(
                    f"🎯 Đang có sẵn {len(df_hien_thi_vt)} từ khóa đã hoàn thành trên Web chính chờ xuất xưởng!"
                )
        else:
            st.warning(
                "⚠️ Vui lòng qua Tab 2 (Chế Độ Tự Động) nhập Link Google Sheets để kết nối dữ liệu trước!"
            )
    except NameError:
        st.warning(
            "⚠️ Cỗ máy chưa thấy File Google Sheets. Vui lòng qua Tab 2 dán link và kết nối trước nhé sếp!"
        )

    st.divider()

    st.subheader("👁️ Chế Độ Duyệt Bài (Review)")
    col_rv1, col_rv2 = st.columns([1, 2])

    with col_rv1:
        st.write("Chọn 1 từ khóa để AI viết mẫu:")
        kw_options = (
            df_ve_tinh["Từ khóa"].tolist()
            if not df_ve_tinh.empty
            else ["Chưa có dữ liệu"]
        )
        target_kw = st.selectbox("Mục tiêu:", kw_options)
        btn_review = st.button("👁️ XEM THỬ MẪU 1 BÀI")

    if btn_review and target_kw != "Chưa có dữ liệu":
        with st.spinner("AI đang 'nhập vai' thợ máy để viết bài..."):
            from satellite_worker import xem_truoc_bai_ve_tinh

            link_goc = df[df["Từ khóa"] == target_kw]["Link bài viết"].values[0]
            ket_qua = xem_truoc_bai_ve_tinh(target_kw, link_goc, client)

            if "error" in ket_qua:
                st.error(f"Lỗi AI: {ket_qua['error']}")
            else:
                st.markdown("---")
                st.info(f"🎭 **Góc nhìn AI chọn:** {ket_qua['goc_nhin']}")
                st.subheader(f"📌 {ket_qua['tieu_de']}")
                st.caption(f"🎨 **Prompt vẽ ảnh:** {ket_qua['prompt_anh']}")

                with st.container(border=True):
                    st.markdown(ket_qua["noi_dung"], unsafe_allow_html=True)

                st.success(
                    "☝️ Đây là mẫu bài viết sẽ được rải lên vệ tinh. Anh thấy văn phong này ổn chưa?"
                )

    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        start_satellite = st.button(
            "🔥 KÍCH HOẠT TRẠM VỆ TINH", use_container_width=True, type="primary"
        )
    with col_btn3:
        stop_satellite = st.button("🛑 DỪNG KHẨN CẤP", use_container_width=True)

    if stop_satellite:
        with open("stop_vetinh.txt", "w") as f:
            f.write("DUNG_LAI")
        st.error(
            "🚨 ĐÃ PHÁT LỆNH DỪNG! Bot sẽ lập tức dừng luồng ngầm sau khi xử lý xong bài viết hiện tại."
        )

    if start_satellite:
        if os.path.exists("stop_vetinh.txt"):
            try:
                os.remove("stop_vetinh.txt")
            except:
                pass

        try:
            df_hop_le = df[df["Trạng thái"] == "Hoàn thành"].copy()

            def check_posted(val):
                try:
                    return int(str(val).split("/")[0])
                except:
                    return 0

            df_hop_le["Da_dang"] = df_hop_le["Số bài Vệ tinh"].apply(check_posted)
            df_final = df_hop_le[df_hop_le["Da_dang"] < max_satellite_posts]
            danh_sach_cho = df_final.to_dict("records")

            if not danh_sach_cho:
                st.warning(
                    "⚠️ Không tìm thấy từ khóa nào đạt chuẩn 'Hoàn thành' hoặc tất cả đã bắn đủ 3 bài vệ tinh rồi anh ơi!"
                )
            else:
                st.success(
                    f"🚀 Phát hiện {len(danh_sach_cho)} mục tiêu chuẩn bị 'oanh tạc'!"
                )

                import threading

                def chay_ngam_ve_tinh():
                    try:
                        print("🚀 [VPS-LOG]: Luồng ngầm Vệ Tinh đã khởi động!")
                        thuc_thi_ban_ve_tinh(
                            danh_sach_cho=danh_sach_cho,
                            quota_day=quota_day,
                            max_satellite_posts=max_satellite_posts,
                            sleep_time=sleep_time,
                            worksheet=worksheet,
                            df=df,
                            client_ai=client,
                        )
                        print(
                            "🎉 [VPS-LOG]: Luồng ngầm Vệ Tinh đã hoàn thành toàn bộ chiến dịch!"
                        )
                    except Exception as e:
                        print(f"❌ [VPS-LOG]: Lỗi luồng ngầm: {e}")

                thread_vt = threading.Thread(target=chay_ngam_ve_tinh)
                add_script_run_ctx(thread_vt)
                thread_vt.start()

                st.balloons()
                st.success("✅ ĐÃ ĐẨY LỆNH XUỐNG HẦM NGẦM!")
                st.info(
                    "😎 Cỗ máy đang âm thầm hoạt động trên VPS. Sếp có thể tắt trình duyệt Web này đi uống cà phê thoải mái. Tiến độ đăng bài sẽ được Bot tự động cập nhật thẳng vào Google Sheets!"
                )

        except Exception as e:
            st.error(f"❌ Lỗi hệ thống điều phối: {e}")

# ----------------- TAB 5: KHO DỮ LIỆU (RAG) -----------------
with tab5:
    st.subheader("📚 Kho Dữ Liệu RAG")
    st.caption("Upload PDF/TXT, nhai vào kho vector để AI dùng khi viết bài.")

    import os as _os

    _KHO_PATH = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "Kho_Du_Lieu_Vector")
    _TAI_LIEU_PATH = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "Nguon_Tai_Lieu_Tho")

    # ── Thống kê kho ────────────────────────────────────────────
    def _lay_thong_ke_kho():
        try:
            import chromadb as _chroma
            cli = _chroma.PersistentClient(path=_KHO_PATH)
            col = cli.get_collection("tai_lieu_seo")
            so_doan = col.count()
            items = col.get(limit=1000, include=["metadatas"])
            nguon = set()
            for m in (items.get("metadatas") or []):
                src = m.get("source", "")
                if src:
                    nguon.add(_os.path.basename(src))
            return so_doan, len(nguon), sorted(nguon)
        except Exception as _e:
            return 0, 0, []

    so_doan, so_file, ds_file = _lay_thong_ke_kho()

    col_r1, col_r2, col_r3 = st.columns(3)
    col_r1.metric("📦 Knowledge chunks", so_doan)
    col_r2.metric("📄 Source files", so_file)
    col_r3.metric("📁 Thư mục nguồn", "Nguon_Tai_Lieu_Tho")

    if ds_file:
        with st.expander(f"📋 Danh sách {so_file} file đã nạp"):
            for _f in ds_file:
                st.text(f"• {_f}")

    st.divider()

    # ── Upload file ──────────────────────────────────────────────
    st.markdown("#### 📂 Upload PDF / TXT vào kho")
    uploaded_files = st.file_uploader(
        "Kéo thả hoặc chọn file",
        type=["pdf", "txt"],
        accept_multiple_files=True,
        key="rag_upload"
    )

    if uploaded_files:
        _os.makedirs(_TAI_LIEU_PATH, exist_ok=True)
        for _uf in uploaded_files:
            _save_path = _os.path.join(_TAI_LIEU_PATH, _uf.name)
            with open(_save_path, "wb") as _fp:
                _fp.write(_uf.getbuffer())
        st.success(f"✅ Đã lưu {len(uploaded_files)} file vào `{_TAI_LIEU_PATH}`")

    # ── Nhai dữ liệu ───────────────────────────────────────────
    st.markdown("#### 🧠 Nhai Toàn Bộ Thư Mục Nguồn")
    st.caption(f"Nhai tất cả PDF/TXT trong `{_TAI_LIEU_PATH}`")

    col_b1, col_b2, col_b3 = st.columns(3)
    with col_b1:
        if st.button("🧠 Nhai Thư Mục", type="primary", key="rag_nap"):
            with st.spinner("Đang nhai tài liệu vào kho..."):
                try:
                    import nap_tai_lieu
                    nap_tai_lieu.nap_vao_kho()
                    st.success("🎉 Nhai xong! Kho đã được cập nhật.")
                    st.rerun()
                except Exception as _e:
                    st.error(f"❌ Lỗi: {_e}")

    with col_b2:
        if st.button("👁️ Xem Kho", key="rag_xem"):
            try:
                import chromadb as _chroma
                cli = _chroma.PersistentClient(path=_KHO_PATH)
                col_kho = cli.get_collection("tai_lieu_seo")
                items = col_kho.get(limit=5, include=["documents", "metadatas"])
                st.markdown(f"**Tổng: {col_kho.count()} chunks**")
                for i, (doc, meta) in enumerate(zip(
                    items.get("documents", []), items.get("metadatas", [])
                )):
                    src = _os.path.basename(meta.get("source", ""))
                    with st.expander(f"[{i+1}] {src}"):
                        st.text(doc[:500])
            except Exception as _e:
                st.warning(f"Kho rỗng hoặc lỗi: {_e}")

    with col_b3:
        if st.button("🗑️ Xoá Kho RAG", key="rag_xoa", type="secondary"):
            try:
                import chromadb as _chroma
                cli = _chroma.PersistentClient(path=_KHO_PATH)
                cli.delete_collection("tai_lieu_seo")
                st.success("✅ Đã xoá sạch kho RAG!")
                st.rerun()
            except Exception as _e:
                st.error(f"❌ {_e}")

# ----------------- TAB 6: CÀO WEB SANG PDF -----------------
with tab6:
    st.subheader("🕷️ Siêu Nhện Cào Web → PDF")
    st.caption("Bot mở từng dấu '+' trong menu, thu link, in từng trang thành PDF sạch (không ảnh, không quảng cáo). Tự bỏ qua trang 404.")

    urls_input = st.text_area(
        "🔗 URL trang mục lục (mỗi dòng 1 link):",
        height=80,
        placeholder="https://help.autodesk.com/view/INVNTOR/2025/ENU/",
    )
    col_t6a, col_t6b = st.columns(2)
    with col_t6a:
        gioi_han_link = st.number_input("🛑 Số bài tối đa:", min_value=10, max_value=10000, value=2000)
    with col_t6b:
        tu_dong_nap = st.checkbox("🧠 Bơm RAG sau khi cào xong", value=True)

    output_folder = st.text_input("📁 Thư mục lưu file:", value="./Nguon_Tai_Lieu_Tho")

    loc_chat_luong = st.checkbox(
        "🤖 AI lọc trang rác trước khi in PDF",
        value=True,
        help="Gemini sẽ đọc nội dung từng trang, bỏ qua trang ít thông tin / không có hướng dẫn / không hữu ích. Tránh bơm rác vào RAG."
    )

    if st.button("🚀 BẮT ĐẦU CÀO DỮ LIỆU", type="primary"):
        if not urls_input.strip():
            st.warning("⚠️ Dán link vào ô đi sếp!")
        else:
            urls_ban_dau = [u.strip() for u in urls_input.split("\n") if u.strip()]
            os.makedirs(output_folder, exist_ok=True)

            progress_bar = st.progress(0)
            ket_qua = []

            # ==================================================================
            # WORKER FUNCTION — chạy trong thread ngầm
            # ==================================================================
            def worker_cao_web(danh_sach_url_goc, thu_muc, result_list, max_bai, nap_rag,
                               loc_ai=True):
                try:
                    import asyncio, urllib.parse, re, time, os, sys, json, requests as req_lib
                    if sys.platform == "win32":
                        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                    from playwright.sync_api import sync_playwright

                    _MODEL = "gemini-2.5-flash"
                    if loc_ai:
                        result_list.append({"type": "success",
                            "msg": "🤖 Vertex AI Gemini sẵn sàng lọc chất lượng trang!"})

                    # ─────────────────────────────────────────────────────────
                    # HELPER: AI kiểm tra chất lượng nội dung trang
                    # Trả về True = giữ lại để in PDF, False = bỏ qua
                    # ─────────────────────────────────────────────────────────
                    def _kiem_tra_chat_luong(noi_dung_text):
                        if not loc_ai:
                            return True
                        noi_dung_text = noi_dung_text.strip()
                        # Trang quá ngắn (<150 ký tự) → rác ngay, không cần hỏi AI
                        if len(noi_dung_text) < 150:
                            return False
                        try:
                            prompt = (
                                "Bạn là bộ lọc nội dung chuyên nghiệp. Đánh giá đoạn văn bản sau "
                                "có chứa thông tin hữu ích không.\n"
                                "Thông tin HỮU ÍCH gồm: hướng dẫn sử dụng, tutorial, giới thiệu tính năng, "
                                "tài liệu kỹ thuật, FAQ, mô tả sản phẩm, review, quy trình, ví dụ thực tế.\n"
                                "Thông tin KHÔNG HỮU ÍCH gồm: trang chỉ có danh sách link điều hướng, "
                                "trang trống, trang chờ, trang chỉ có vài câu mô tả chung chung không có nội dung.\n"
                                "Trả lời CHỈ bằng một từ: YES hoặc NO. Không giải thích.\n\n"
                                f"Nội dung (tối đa 3000 ký tự đầu):\n{noi_dung_text[:3000]}"
                            )
                            resp = client.models.generate_content(model=_MODEL, contents=[prompt])
                            answer = resp.text.strip().upper()
                            return answer.startswith("YES")
                        except Exception:
                            return True  # Nếu AI lỗi → giữ lại, không bỏ

                    with sync_playwright() as pw:
                        browser = pw.chromium.launch(
                            headless=True,
                            args=["--disable-web-security", "--no-sandbox"],
                        )
                        ctx = browser.new_context(
                            viewport={"width": 1440, "height": 900},
                            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
                        )
                        trang = ctx.new_page()

                        tat_ca_link = []   # danh sách link cuối cùng để in PDF

                        # ══════════════════════════════════════════════════════════
                        # HELPER: lấy tất cả href từ TOÀN TRANG, lọc theo base_path
                        # Không giới hạn trong nav-container vì selector nav có thể sai
                        # ══════════════════════════════════════════════════════════
                        def _lay_link_tu_nav(base_path):
                            raw = trang.evaluate("""(() => {
                                var s = new Set();
                                document.querySelectorAll('a[href]').forEach(function(a) {
                                    var href = a.getAttribute('href');
                                    if (!href || href.startsWith('#') || href.startsWith('javascript:')) return;
                                    try { s.add(new URL(href, window.location.href).href.split('#')[0]); }
                                    catch(e) {}
                                });
                                return Array.from(s);
                            })()""")
                            return [lnk for lnk in (raw or []) if lnk.startswith(base_path)]

                        # ══════════════════════════════════════════════════════════
                        # HELPER: phân tích DOM để biết trang dùng framework gì
                        # Trả về dict {selector: count} để debug
                        # ══════════════════════════════════════════════════════════
                        def _debug_dom():
                            return trang.evaluate("""(() => {
                                var d = {};
                                var checks = [
                                    'li.jstree-closed', 'li.jstree-open',
                                    '[aria-expanded="false"]', '[aria-expanded="true"]',
                                    'details:not([open])', 'details[open]',
                                    'button', 'nav a', 'aside a',
                                    '[role="treeitem"]', '[role="tree"]',
                                    '[class*="collapsed"]', '[class*="expanded"]',
                                    '[class*="toc"]', '[class*="nav"]',
                                ];
                                checks.forEach(function(s) {
                                    try { d[s] = document.querySelectorAll(s).length; } catch(e) {}
                                });
                                // Thống kê class của các phần tử có thể là nav
                                var navEl = document.querySelector('nav, aside, [role="navigation"], [class*="nav"]');
                                if (navEl) d['__nav_class'] = navEl.className.substring(0,80);
                                return d;
                            })()""")

                        # ══════════════════════════════════════════════════════════
                        # HELPER: tìm và click NÚT MỞ RỘNG ĐẦU TIÊN còn đóng
                        # Thử nhiều chiến lược: jstree → aria → details → brute-force click
                        # QUAN TRỌNG: chỉ scroll NAV container, không scroll window (tránh loop vô tận)
                        # ══════════════════════════════════════════════════════════
                        def _tim_va_click_nut_dong():
                            """Trả về (True, msg) nếu click được, (False, msg) nếu không."""
                            info = trang.evaluate("""(() => {
                                var H = window.innerHeight;
                                var candidates = [];

                                function addCand(el, label) {
                                    var rect = el.getBoundingClientRect();
                                    if (rect.width > 0 && rect.height > 0
                                        && rect.top > -100 && rect.top < H + 100) {
                                        candidates.push({
                                            x: Math.round(rect.left + rect.width / 2),
                                            y: Math.round(rect.top + rect.height / 2),
                                            top: rect.top,
                                            label: label
                                        });
                                    }
                                }

                                // Strategy 1 (ưu tiên): treeitem + aria-expanded=false
                                // Đây là pattern Autodesk dùng (nav-class=ui-nav-home là header, không phải TOC)
                                document.querySelectorAll('[role="treeitem"][aria-expanded="false"]').forEach(function(el) {
                                    addCand(el, 'treeitem-aria');
                                });

                                // Strategy 2: jstree standard
                                if (candidates.length === 0) {
                                    document.querySelectorAll('li.jstree-closed').forEach(function(li) {
                                        var ocl = li.querySelector('i.jstree-ocl, ins.jstree-ocl, .jstree-ocl');
                                        addCand(ocl || li, 'jstree-closed');
                                    });
                                }

                                // Strategy 3: aria-expanded=false BÊN TRONG [role="tree"] hoặc [role="treeitem"]
                                // (tránh bắt các dropdown ngoài TOC)
                                if (candidates.length === 0) {
                                    var trees = document.querySelectorAll('[role="tree"], [role="group"]');
                                    trees.forEach(function(tree) {
                                        tree.querySelectorAll('[aria-expanded="false"]').forEach(function(el) {
                                            addCand(el, 'tree-aria');
                                        });
                                    });
                                }

                                // Strategy 4: details/summary
                                if (candidates.length === 0) {
                                    document.querySelectorAll('details:not([open]) > summary').forEach(function(el) {
                                        addCand(el, 'details');
                                    });
                                }

                                if (candidates.length === 0) return null;
                                candidates.sort(function(a, b) { return a.top - b.top; });
                                return candidates[0];
                            })()""")

                            if not info:
                                return False, "không tìm thấy nút đóng"
                            try:
                                trang.mouse.click(info["x"], info["y"])
                                return True, info.get("label", "?")
                            except Exception as e:
                                return False, str(e)

                        # ══════════════════════════════════════════════════════════
                        # HELPER: scroll CHỈ nav container, không scroll window
                        # Trả về True nếu scroll được (còn chỗ scroll)
                        # ══════════════════════════════════════════════════════════
                        def _scroll_nav_xuong():
                            return trang.evaluate("""(() => {
                                var ss = [
                                    '#left-nav-container', '.left-nav-container',
                                    '[class*="toc"]', '[class*="leftNav"]',
                                    '[class*="sidebar"]', 'nav', 'aside',
                                    '[role="navigation"]', '[role="tree"]'
                                ];
                                for (var s of ss) {
                                    var el = document.querySelector(s);
                                    if (el && el.scrollHeight > el.clientHeight + 5) {
                                        var before = el.scrollTop;
                                        el.scrollTop = Math.min(el.scrollTop + 400, el.scrollHeight);
                                        if (el.scrollTop > before) return true;
                                    }
                                }
                                return false;  // KHÔNG scroll window để tránh loop vô tận
                            })()""")

                        def _scroll_nav_len_dau():
                            trang.evaluate("""(() => {
                                var ss = [
                                    '#left-nav-container', '.left-nav-container',
                                    '[class*="toc"]', '[class*="leftNav"]',
                                    '[class*="sidebar"]', 'nav', 'aside'
                                ];
                                for (var s of ss) {
                                    var el = document.querySelector(s);
                                    if (el) { el.scrollTop = 0; return; }
                                }
                            })()""")

                        # ══════════════════════════════════════════════════════════
                        # PHA 1: BUNG CÂY MENU + THU THẬP LINK
                        #
                        # Chiến lược chính:
                        # A. Chặn network để bắt link từ AJAX response (jstree lazy-load)
                        # B. Click từng nút đóng trên→xuống, thu link sau mỗi click
                        # C. Scroll NAV (không scroll window) khi hết nút trong viewport
                        # D. Dừng khi không còn nút đóng sau 3 lần reset
                        # ══════════════════════════════════════════════════════════
                        for url_goc in danh_sach_url_goc:
                            base_path = url_goc.split("?")[0].rstrip("/") + "/"
                            result_list.append({"type": "info", "msg": f"📍 Đang tải trang gốc: {url_goc}"})

                            # --- Chặn AJAX để bắt link từ response ---
                            ajax_links = set()

                            def _on_response(resp):
                                try:
                                    if base_path.split("/")[2] not in resp.url:
                                        return
                                    ct = resp.headers.get("content-type", "")
                                    if not any(t in ct for t in ["json", "html", "xml"]):
                                        return
                                    body = resp.text()
                                    # Tìm href hoặc guid patterns trong response
                                    found = re.findall(
                                        r'href["\s:=\']+([^"\'>\s]+(?:guid|GUID)[^"\'>\s]*)',
                                        body
                                    )
                                    for f in found:
                                        try:
                                            full = urllib.parse.urljoin(base_path, f).split("#")[0]
                                            if full.startswith(base_path):
                                                ajax_links.add(full)
                                        except Exception:
                                            pass
                                except Exception:
                                    pass

                            trang.on("response", _on_response)

                            try:
                                trang.goto(url_goc, wait_until="networkidle", timeout=60000)
                                time.sleep(2)
                            except Exception as e:
                                result_list.append({"type": "error", "msg": f"❌ Không tải được trang: {e}"})
                                trang.remove_listener("response", _on_response)
                                continue

                            # Debug: in ra DOM structure để biết page dùng gì
                            dom_info = _debug_dom()
                            nav_cls = dom_info.get('__nav_class', '?')[:50]
                            aria_false = dom_info.get('[aria-expanded="false"]', 0)
                            treeitem = dom_info.get('[role="treeitem"]', 0)
                            jstree_closed = dom_info.get('li.jstree-closed', 0)
                            nav_a = dom_info.get('nav a', 0)
                            result_list.append({
                                "type": "info",
                                "msg": (f"🔍 DOM: jstree-closed={jstree_closed} | "
                                        f"aria-false={aria_false} | "
                                        f"treeitem={treeitem} | "
                                        f"nav-a={nav_a} | nav-class={nav_cls}"),
                            })

                            tap_link = set(_lay_link_tu_nav(base_path))
                            lan_reset = 0
                            so_click = 0
                            MAX_CLICK = 300       # Giới hạn tổng số click
                            CLICK_KHONG_MOI = 0   # Đếm số click liên tiếp không có link mới
                            MAX_CLICK_KHONG_MOI = 50  # Dừng nếu 50 click liên tiếp vô ích

                            result_list.append({
                                "type": "info",
                                "msg": f"🌲 Bắt đầu mở cây menu. Link ban đầu: {len(tap_link)}",
                            })

                            while True:
                                # Dừng nếu quá giới hạn tổng click
                                if so_click >= MAX_CLICK:
                                    result_list.append({"type": "warning",
                                        "msg": f"⚠️ Đã click {MAX_CLICK} lần, dừng PHA 1."})
                                    break
                                # Dừng sớm nếu nhiều click liên tiếp không mở ra link mới
                                if CLICK_KHONG_MOI >= MAX_CLICK_KHONG_MOI:
                                    result_list.append({"type": "info",
                                        "msg": f"✅ {CLICK_KHONG_MOI} click không có link mới → kết thúc sớm."})
                                    break

                                ok, label = _tim_va_click_nut_dong()

                                if not ok:
                                    # Không thấy nút đóng → scroll NAV xuống
                                    if _scroll_nav_xuong():
                                        time.sleep(0.5)
                                        lan_reset = 0
                                        continue
                                    # Nav hết scroll → reset lên đầu, kiểm tra lần cuối
                                    _scroll_nav_len_dau()
                                    time.sleep(0.4)
                                    ok2, label2 = _tim_va_click_nut_dong()
                                    if ok2:
                                        # Vẫn còn nút → xử lý click này
                                        so_click += 1
                                        lan_reset = 0
                                        try:
                                            trang.wait_for_load_state("networkidle", timeout=8000)
                                        except Exception:
                                            time.sleep(1.5)
                                        link_moi = set(_lay_link_tu_nav(base_path)) - tap_link
                                        tap_link.update(link_moi)
                                        if link_moi:
                                            CLICK_KHONG_MOI = 0
                                            result_list.append({"type": "info",
                                                "msg": f"🔗 Click #{so_click} [{label2}] → +{len(link_moi)} link. Tổng: {len(tap_link)}"})
                                        else:
                                            CLICK_KHONG_MOI += 1
                                        continue
                                    lan_reset += 1
                                    if lan_reset >= 3:
                                        break
                                    continue

                                # Click thành công → chờ AJAX + thu link
                                so_click += 1
                                lan_reset = 0
                                try:
                                    trang.wait_for_load_state("networkidle", timeout=8000)
                                except Exception:
                                    time.sleep(1.5)

                                link_moi = set(_lay_link_tu_nav(base_path)) - tap_link
                                tap_link.update(link_moi)
                                if link_moi:
                                    CLICK_KHONG_MOI = 0
                                    result_list.append({"type": "info",
                                        "msg": f"🔗 Click #{so_click} [{label}] → +{len(link_moi)} link. Tổng: {len(tap_link)}"})
                                else:
                                    CLICK_KHONG_MOI += 1

                            trang.remove_listener("response", _on_response)

                            # Gộp thêm link từ AJAX (nếu có)
                            before_ajax = len(tap_link)
                            tap_link.update(ajax_links)
                            if len(tap_link) > before_ajax:
                                result_list.append({"type": "info",
                                    "msg": f"📡 AJAX capture thêm {len(tap_link)-before_ajax} link. Tổng: {len(tap_link)}"})

                            result_list.append({
                                "type": "success",
                                "msg": f"✅ Hết dấu '+'. Tổng thu được {len(tap_link)} link từ {url_goc}",
                            })

                            # Gộp vào danh sách cuối, giới hạn max_bai
                            for lnk in sorted(tap_link):
                                if lnk not in tat_ca_link:
                                    tat_ca_link.append(lnk)
                                    if len(tat_ca_link) >= max_bai:
                                        break

                        result_list.append({
                            "type": "success",
                            "msg": f"🎯 PHA 1 Hoàn Tất! {len(tat_ca_link)} link sẽ được in PDF.",
                        })

                        # ══════════════════════════════════════════════════════════
                        # PHA 2: IN TỪNG TRANG THÀNH PDF SẠCH
                        # - Kiểm tra HTTP 404 và CSR-404
                        # - (Tùy chọn) Gemini phân tích ảnh/video → text mô tả
                        # - Xóa nav, sidebar, rác; giữ nội dung chính + mô tả AI
                        # ══════════════════════════════════════════════════════════
                        tong = len(tat_ca_link)
                        thanh_cong = 0
                        bo_qua = 0

                        for idx, url_bai in enumerate(tat_ca_link):
                            result_list.append({
                                "type": "info",
                                "msg": f"[{idx+1}/{tong}] Đang xử lý: {url_bai}",
                            })

                            try:
                                resp = trang.goto(url_bai, wait_until="networkidle", timeout=45000)
                                time.sleep(1)

                                # ─ Tầng 1: HTTP 4xx/5xx ─
                                if resp and resp.status >= 400:
                                    result_list.append({"type": "warning", "msg": f"⚠️ HTTP {resp.status} — bỏ qua: {url_bai}"})
                                    bo_qua += 1
                                    result_list.append({"type": "progress", "value": (idx + 1) / tong})
                                    continue

                                # ─ Tầng 2: CSR-404 ─
                                body_text = trang.evaluate("(() => document.body.innerText.toLowerCase())()")
                                loi_csr = ["404", "lost your page", "page not found",
                                           "we couldn't find", "this page doesn't exist",
                                           "we lost this page", "looks like we lost"]
                                if any(k in body_text for k in loi_csr):
                                    result_list.append({"type": "warning", "msg": f"⚠️ CSR-404 — bỏ qua: {url_bai}"})
                                    bo_qua += 1
                                    result_list.append({"type": "progress", "value": (idx + 1) / tong})
                                    continue

                                # ─ Tầng 3: AI lọc chất lượng nội dung ─
                                noi_dung_kiem_tra = trang.evaluate(
                                    "(() => document.body.innerText)()")
                                if not _kiem_tra_chat_luong(noi_dung_kiem_tra):
                                    result_list.append({"type": "warning",
                                        "msg": f"   🚫 AI lọc: trang ít thông tin — bỏ qua: {url_bai}"})
                                    bo_qua += 1
                                    result_list.append({"type": "progress", "value": (idx + 1) / tong})
                                    continue

                                # ─ Làm sạch DOM: xóa rác, giữ nội dung chính ─
                                trang.evaluate("""(() => {
                                    var xoa = [
                                        'header','footer','nav','aside',
                                        'video','audio','form','button','input','select',
                                        'script','noscript','style',
                                        '[class*="sidebar"]','[class*="nav"]','[id*="nav"]',
                                        '[class*="banner"]','[class*="ads"]','[class*="cookie"]',
                                        '[class*="feedback"]','[class*="social"]','[class*="share"]',
                                        '[class*="related"]','[class*="recommend"]',
                                        '[id*="feedback"]','[id*="cookie"]',
                                        'iframe[src*="youtube"]'
                                    ];
                                    xoa.forEach(function(sel) {
                                        document.querySelectorAll(sel).forEach(function(el) {
                                            try { el.remove(); } catch(e) {}
                                        });
                                    });
                                    // Xóa img CÒN LẠI (chưa được Gemini thay thế)
                                    document.querySelectorAll('img').forEach(function(el) {
                                        try { el.remove(); } catch(e) {}
                                    });
                                    // Xóa figure rỗng
                                    document.querySelectorAll('figure').forEach(function(el) {
                                        if (!el.querySelector('.gemini-desc') && el.querySelectorAll('img').length === 0)
                                            try { el.remove(); } catch(e) {}
                                    });

                                    // Tìm vùng nội dung chính
                                    var main = document.querySelector('main, article, [role="main"], '
                                        + '#content, .content, .main-content, .article-body, '
                                        + '.help-content, .doc-content')
                                        || document.body;
                                    if (main !== document.body) {
                                        document.body.innerHTML = main.outerHTML;
                                    }

                                    // CSS in PDF
                                    var style = document.createElement('style');
                                    style.textContent = [
                                        'body{font-family:Arial,sans-serif;font-size:11pt;',
                                        'max-width:750px;margin:0 auto;padding:24px;',
                                        'color:#111;background:#fff;line-height:1.6}',
                                        'h1,h2,h3,h4{color:#1a1a1a;margin-top:1.2em}',
                                        'table{border-collapse:collapse;width:100%}',
                                        'td,th{border:1px solid #ccc;padding:6px 8px}',
                                        'pre,code{background:#f5f5f5;padding:2px 6px;',
                                        'font-size:10pt;border-radius:3px}',
                                        'a{color:#1155cc}'
                                    ].join('');
                                    document.head.appendChild(style);
                                })()""")
                                time.sleep(0.5)

                                # ─ Tên file PDF từ guid hoặc slug ─
                                parsed = urllib.parse.urlparse(url_bai)
                                qp = urllib.parse.parse_qs(parsed.query)
                                if "guid" in qp:
                                    safe = re.sub(r"[^A-Za-z0-9]", "_", qp["guid"][0])[:60]
                                else:
                                    slug = parsed.path.rstrip("/").split("/")[-1] or "trang_chu"
                                    safe = re.sub(r"[^A-Za-z0-9]", "_", slug)[:60]
                                if not safe:
                                    safe = f"bai_{idx}"

                                filepath = os.path.join(thu_muc, f"doc_{idx:04d}_{safe}.pdf")
                                trang.pdf(
                                    path=filepath,
                                    format="A4",
                                    print_background=False,
                                    margin={"top": "1.5cm", "bottom": "1.5cm",
                                            "left": "2cm", "right": "2cm"},
                                )
                                thanh_cong += 1

                            except Exception as err:
                                result_list.append({"type": "error", "msg": f"❌ Lỗi: {url_bai} — {err}"})

                            result_list.append({"type": "progress", "value": (idx + 1) / tong})

                        browser.close()

                        # ─ Bơm RAG ─
                        if nap_rag and thanh_cong > 0:
                            result_list.append({"type": "info", "msg": "🧠 Đang bơm tài liệu vào kho RAG..."})
                            try:
                                import nap_tai_lieu
                                nap_tai_lieu.nap_vao_kho()
                                result_list.append({"type": "success", "msg": "🚀 Bơm RAG hoàn tất!"})
                            except Exception:
                                result_list.append({"type": "error", "msg": "❌ Lỗi khi bơm RAG."})

                        result_list.append({
                            "type": "done",
                            "thanh_cong": thanh_cong,
                            "bo_qua": bo_qua,
                            "tong": tong,
                        })

                except Exception as fatal:
                    result_list.append({"type": "fatal", "msg": str(fatal)})

            # ── Khởi động thread ──────────────────────────────────────────
            import threading
            thread = threading.Thread(
                target=worker_cao_web,
                args=(urls_ban_dau, output_folder, ket_qua, gioi_han_link, tu_dong_nap),
                kwargs={"loc_ai": loc_chat_luong},
            )
            thread.start()

            with st.spinner("🕷️ Bot đang làm việc, sếp pha cà phê chờ nhé..."):
                while thread.is_alive() or ket_qua:
                    if ket_qua:
                        msg = ket_qua.pop(0)
                        t = msg.get("type", "")
                        if t == "info":
                            st.write(msg["msg"])
                        elif t == "success":
                            st.success(msg["msg"])
                        elif t == "warning":
                            st.warning(msg["msg"])
                        elif t == "error":
                            st.error(msg["msg"])
                        elif t == "progress":
                            progress_bar.progress(min(msg["value"], 1.0))
                        elif t == "done":
                            st.balloons()
                            st.success(
                                f"🎉 Hoàn tất! Lưu {msg['thanh_cong']}/{msg['tong']} PDF | Bỏ qua {msg['bo_qua']} trang lỗi."
                            )
                        elif t == "fatal":
                            st.error(f"❌ Lỗi hệ thống: {msg['msg']}")
                    time.sleep(0.1)

    # ══════════════════════════════════════════════════════════
    # SECTION RIÊNG: PHÂN TÍCH VIDEO / ẢNH BẤT KỲ BẰNG AI
    # Không cần cào web, chỉ cần dán link → Gemini phân tích → hiện kết quả
    # Có thể lưu thành PDF / bơm RAG
    # ══════════════════════════════════════════════════════════
    st.divider()
    st.subheader("📹 Phân Tích Video / Ảnh Bất Kỳ Bằng AI")
    st.caption("Dán link YouTube, video hoặc ảnh trực tiếp — AI sẽ phân tích và hiển thị mô tả chi tiết.")

    col_le1, col_le2 = st.columns([3, 1])
    with col_le1:
        media_urls_input = st.text_area(
            "🔗 Link video / ảnh (mỗi dòng 1 link):",
            height=100,
            placeholder="https://www.youtube.com/watch?v=...\nhttps://example.com/image.jpg",
            key="media_urls_le",
        )
    with col_le2:
        ngon_ngu_le = st.selectbox("🌐 Ngôn ngữ:", ["Tiếng Việt", "English"], key="lang_le")
        luu_pdf_le = st.checkbox("💾 Lưu PDF", value=False, key="luu_pdf_le")
        nap_rag_le = st.checkbox("🧠 Bơm RAG", value=False, key="nap_rag_le")
        thu_muc_le = st.text_input("📁 Thư mục:", value="./Phan_Tich_Media", key="thu_muc_le")

    if st.button("🤖 PHÂN TÍCH NGAY", type="secondary", key="btn_phan_tich_le"):
        if not media_urls_input.strip():
            st.warning("⚠️ Dán link vào ô trên đi sếp!")
        else:
            from google.genai import types as _gt
            import requests as _req

            _MODEL_LE = "gemini-2.5-flash"
            prompt_img_le = (
                "Mô tả chi tiết nội dung kỹ thuật của hình ảnh này bằng tiếng Việt. Nêu rõ thành phần, số liệu, quy trình."
                if ngon_ngu_le == "Tiếng Việt"
                else "Describe the technical content of this image in detail. Include components, figures, and processes."
            )
            prompt_vid_le = (
                "Tóm tắt toàn bộ nội dung kỹ thuật chính của video này bằng tiếng Việt một cách chi tiết."
                if ngon_ngu_le == "Tiếng Việt"
                else "Provide a detailed technical summary of this video in English."
            )

            urls_le = [u.strip() for u in media_urls_input.split("\n") if u.strip()]
            ket_qua_le = []

            if luu_pdf_le:
                os.makedirs(thu_muc_le, exist_ok=True)

            for i_le, url_le in enumerate(urls_le):
                with st.spinner(f"🤖 Đang phân tích ({i_le+1}/{len(urls_le)}): {url_le[:60]}..."):
                    try:
                        # Phân loại: ảnh hay video
                        _ext = url_le.lower().split("?")[0]
                        _is_img = any(_ext.endswith(e) for e in [".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp"])
                        _is_yt = "youtube.com" in url_le or "youtu.be" in url_le

                        if _is_img:
                            _r = _req.get(url_le, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
                            _ct = _r.headers.get("content-type", "image/jpeg").split(";")[0].strip()
                            _resp = client.models.generate_content(
                                model=_MODEL_LE,
                                contents=[_gt.Part.from_bytes(data=_r.content, mime_type=_ct), prompt_img_le],
                            )
                            _loai = "🖼️ Ảnh"
                        else:
                            # YouTube hoặc video URL khác
                            _resp = client.models.generate_content(
                                model=_MODEL_LE,
                                contents=[
                                    _gt.Part.from_uri(file_uri=url_le, mime_type="video/mp4"),
                                    prompt_vid_le,
                                ],
                            )
                            _loai = "🎬 Video"

                        _mo_ta = _resp.text.strip()
                        ket_qua_le.append({"url": url_le, "loai": _loai, "mo_ta": _mo_ta})

                        st.success(f"{_loai} phân tích xong!")
                        st.markdown(f"**{url_le}**")
                        st.write(_mo_ta)

                        # Lưu PDF nếu được bật
                        if luu_pdf_le:
                            try:
                                from reportlab.lib.pagesizes import A4
                                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
                                from reportlab.lib.styles import getSampleStyleSheet
                                from reportlab.pdfbase import pdfmetrics
                                from reportlab.pdfbase.ttfonts import TTFont
                                import re as _re

                                _safe = _re.sub(r"[^A-Za-z0-9]", "_", url_le.split("/")[-1][:40] or f"media_{i_le}")
                                _pdf_path = os.path.join(thu_muc_le, f"media_{i_le:03d}_{_safe}.pdf")
                                _doc = SimpleDocTemplate(_pdf_path, pagesize=A4)
                                _styles = getSampleStyleSheet()
                                _story = [
                                    Paragraph(f"<b>Nguồn:</b> {url_le}", _styles["Normal"]),
                                    Spacer(1, 12),
                                    Paragraph(f"<b>Loại:</b> {_loai}", _styles["Normal"]),
                                    Spacer(1, 12),
                                    Paragraph("<b>Mô tả AI:</b>", _styles["Normal"]),
                                    Spacer(1, 6),
                                    Paragraph(_mo_ta.replace("\n", "<br/>"), _styles["Normal"]),
                                ]
                                _doc.build(_story)
                                st.info(f"💾 Đã lưu: {_pdf_path}")
                            except Exception as _ep:
                                st.warning(f"⚠️ Không lưu được PDF: {_ep}")

                    except Exception as _e:
                        st.error(f"❌ Lỗi phân tích {url_le}: {_e}")
                        ket_qua_le.append({"url": url_le, "loai": "?", "mo_ta": str(_e)})

            # Bơm RAG nếu chọn
            if nap_rag_le and any(k["mo_ta"] for k in ket_qua_le if "Lỗi" not in k.get("loai", "")):
                try:
                    import nap_tai_lieu
                    nap_tai_lieu.nap_vao_kho()
                    st.success("🚀 Đã bơm kết quả phân tích vào kho RAG!")
                except Exception:
                    st.warning("⚠️ Không tự bơm RAG được, kiểm tra lại nap_tai_lieu.py")
