import streamlit as st
import requests
import time
import pandas as pd
import string
import json
import re
from datetime import datetime
import gspread
# 💥 ĐÃ SỬA LỖI Ở ĐÂY: Thêm biến GOOGLE_KEY_PATH
from my_config import client, GOOGLE_KEY_PATH

# ==========================================
# 🛠️ KHU VỰC HÀM TRỢ LÝ (DÙNG CHUNG)
# ==========================================
def lay_id_tu_url(url):
    pattern = r"/spreadsheets/d/([a-zA-Z0-9-_]+)"
    match = re.search(pattern, url)
    return match.group(1) if match else None

def lay_goi_y_google(tu_khoa):
    url = f"http://suggestqueries.google.com/complete/search?client=chrome&q={tu_khoa}&hl=vi&gl=vn"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200: return response.json()[1] 
    except: pass
    return []

# --- HÀM AI TAB 1 ---
# --- HÀM AI TAB 1 (ĐÃ TỐI ƯU CHUẨN SEO) ---
def gom_nhom_tu_khoa_bang_ai(danh_sach_tk):
    prompt = f"""
    Bạn là một Chuyên gia SEO Master. Nhiệm vụ của bạn là Gom nhóm từ khóa (Keyword Clustering) theo chiến lược Topic Cluster.
    
    🔴 QUY TẮC GOM NHÓM (BẮT BUỘC TUÂN THỦ):
    1. GOM THEO SEARCH INTENT: Các từ khóa có cùng chung 1 mục đích tìm kiếm, có thể giải quyết trọn vẹn trong CÙNG 1 bài viết thì gom vào 1 nhóm. (VD: "sửa máy tính" và "sửa máy vi tính" là 1 nhóm).
    2. CHỌN TỪ KHÓA CHÍNH (tu_khoa_chinh): Phải chọn từ khóa gốc, ngắn gọn nhất, mang tính bao quát và có khả năng mang lại lượng Volume (Lưu lượng tìm kiếm) cao nhất làm từ khóa chính.
    3. CHỌN TỪ KHÓA PHỤ (tu_khoa_phu): Là các từ khóa đuôi dài (Long-tail), biến thể đồng nghĩa, truy vấn liên quan ngữ nghĩa hoặc câu hỏi để sếp của tôi dùng làm thẻ H2, H3 trong bài.
    4. CHIA TÁCH RÕ RÀNG: Tuyệt đối KHÔNG gom từ khóa "Bán hàng/Dịch vụ" chung với từ khóa "Miễn phí/Thủ thuật/Crack". Phải tách làm 2 bài riêng.
    
    🔴 ĐỊNH DẠNG ĐẦU RA:
    Trả về DUY NHẤT một mảng JSON hợp lệ, tuyệt đối KHÔNG giải thích, KHÔNG dùng markdown ```json bọc bên ngoài.
    Mẫu chuẩn: [{{"chu_de": "Dịch vụ cài Win tận nơi", "tu_khoa_chinh": "cài win tại nhà", "tu_khoa_phu": ["giá cài win 10", "dịch vụ cài win 11 tận nơi", "cài win máy tính"]}}]
    
    Danh sách từ khóa cần xử lý:
    {danh_sach_tk}
    """
    
    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        
        # 🟢 Lọc rác Markdown siêu an toàn
        clean_json = response.text.strip()
        if clean_json.startswith("```json"):
            clean_json = clean_json[7:]
        if clean_json.endswith("```"):
            clean_json = clean_json[:-3]
        clean_json = clean_json.strip()
        
        return json.loads(clean_json)
    except Exception as e:
        print(f"Lỗi gom nhóm AI: {e}")
        return None

# --- HÀM AI TAB 2 (MỚI): LỌC & RÚT GỌN TỪ KHÓA ĐỐI THỦ ---
def loc_tu_khoa_doi_thu_bang_ai(danh_sach_tho):
    prompt = f"""
    Bạn là một chuyên gia SEO thực chiến. Dưới đây là danh sách tiêu đề bài viết cào được từ web đối thủ.
    Nhiệm vụ của bạn:
    1. LỌC BỎ các tiêu đề không mang tính chất Thủ thuật, Hướng dẫn, Sửa lỗi, hoặc Tải phần mềm.
    2. CHUYỂN ĐỔI các tiêu đề được giữ lại thành TỪ KHÓA SEO NGẮN GỌN (từ khóa gốc mang lại traffic, khoảng 3-7 chữ).
       Ví dụ 1: "Hướng Dẫn Download Windows 11 26H2 ISO arm64 & x64 Từ A-Z" -> Chuyển thành từ khóa: "download windows 11 iso"
       Ví dụ 2: "Cách khắc phục lỗi Unikey không gõ được tiếng Việt" -> Chuyển thành từ khóa: "lỗi unikey không gõ được tiếng việt"
    3. Trả về đúng định dạng JSON Array: [^{{"tu_khoa_seo": "...", "link_tham_khao": "..."}}^]
    Tuyệt đối chỉ trả về mảng JSON, không giải thích.
    
    Dữ liệu thô cần xử lý: {danh_sach_tho}
    """
    try:
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        clean_json = re.sub(r'```json|```', '', response.text).strip()
        return json.loads(clean_json)
    except Exception as e:
        print("Lỗi AI Lọc:", e)
        return None

# --- HÀM LƯU SHEETS TAB 1 ---
def day_data_gom_nhom_vao_sheets(danh_sach_gom_nhom, tu_khoa_goc, url_sheets, ten_tab):
    try:
        # 💥 ĐÃ SỬA LỖI Ở ĐÂY: Dùng đường dẫn tĩnh GOOGLE_KEY_PATH
        gc = gspread.service_account(filename=GOOGLE_KEY_PATH)
        sheet_id = lay_id_tu_url(url_sheets)
        if not sheet_id: return False, "Đường dẫn URL Google Sheets không hợp lệ!"
        sh = gc.open_by_key(sheet_id)
        
        try: ws = sh.worksheet(ten_tab)
        except:
            ws = sh.add_worksheet(title=ten_tab, rows="1000", cols="20")
            ws.append_row(["THỜI GIAN ĐÀO", "TỪ KHÓA GỐC", "CHỦ ĐỀ", "TỪ KHÓA CHÍNH (Tiêu đề)", "TỪ KHÓA PHỤ (Dàn ý H2, H3)"])
            
        thoi_gian = datetime.now().strftime("%d/%m/%Y %H:%M")
        rows_to_add = []
        for nhom in danh_sach_gom_nhom:
            chu_de = nhom.get('chu_de', '')
            tk_chinh = nhom.get('tu_khoa_chinh', '')
            tk_phu = ", ".join(nhom.get('tu_khoa_phu', []))
            rows_to_add.append([thoi_gian, tu_khoa_goc.upper(), chu_de, tk_chinh, tk_phu])
            
        ws.append_rows(rows_to_add)
        return True, len(rows_to_add)
    except Exception as e: return False, str(e)

# --- HÀM LƯU SHEETS TAB 2 ---
def day_data_doi_thu_vao_sheets(danh_sach_tu_khoa_sach, domain_doi_thu, url_sheets, ten_tab):
    try:
        # 💥 ĐÃ SỬA LỖI Ở ĐÂY: Dùng đường dẫn tĩnh GOOGLE_KEY_PATH
        gc = gspread.service_account(filename=GOOGLE_KEY_PATH)
        sheet_id = lay_id_tu_url(url_sheets)
        if not sheet_id: return False, "URL Sheets không hợp lệ!"
        sh = gc.open_by_key(sheet_id)
        
        try: ws = sh.worksheet(ten_tab)
        except:
            ws = sh.add_worksheet(title=ten_tab, rows="1000", cols="10")
            ws.append_row(["THỜI GIAN CÀO", "NGUỒN ĐỐI THỦ", "TỪ KHÓA SEO ĐÃ LỌC", "LINK THAM KHẢO"])
            
        thoi_gian = datetime.now().strftime("%d/%m/%Y %H:%M")
        rows_to_add = []
        for item in danh_sach_tu_khoa_sach:
            rows_to_add.append([thoi_gian, domain_doi_thu, item.get('tu_khoa_seo', ''), item.get('link_tham_khao', '')])
            
        ws.append_rows(rows_to_add)
        return True, len(rows_to_add)
    except Exception as e: return False, str(e)

# ==========================================
# 🚀 GIAO DIỆN CHÍNH (MASTER APP)
# ==========================================
def app_quan_ly_tu_khoa():
    st.set_page_config(page_title="Hệ Sinh Thái Từ Khóa SEO", page_icon="🚀", layout="wide")
    
    st.title("🚀 Hệ Sinh Thái Khai Thác Từ Khóa SEO 2026")
    
    with st.expander("⚙️ CẤU HÌNH LƯU TRỮ GOOGLE SHEETS", expanded=True):
        col_gs1, col_gs2, col_gs3 = st.columns([2, 1, 1])
        with col_gs1: gs_url_chung = st.text_input("🔗 URL Google Sheets:", "https://docs.google.com/spreadsheets/d/1c7FDAe4HASvEGU15WDAK8IkcyaULKh3OquWL7FZfXfA/edit#gid=0")
        with col_gs2: gs_tab_dao = st.text_input("Tab data ĐÀO (Tab 1):", "KeHoachSEO")
        with col_gs3: gs_tab_cao = st.text_input("Tab data CÀO (Tab 2):", "TuKhoaDoiThu")

    st.markdown("---")
    tab1, tab2 = st.tabs(["⛏️ MÁY ĐÀO TỪ KHÓA (Google)", "🕵️‍♂️ ĐIỆP VIÊN CÀO ĐỐI THỦ (Lọc AI)"])

    # ==========================================
    # TAB 1: MÁY ĐÀO TỪ KHÓA TỪ GOOGLE
    # ==========================================
    with tab1:
        with st.form("form_dao_tu_khoa"):
            tu_khoa_goc = st.text_input("Nhập Từ Khóa Mồi (Ví dụ: autocad, sửa máy tính...):")
            c1, c2 = st.columns(2)
            with c1: az = st.checkbox("Đào A-Z", value=True)
            with c2: hd = st.checkbox("Đào Hỏi Đáp", value=True)
            btn_dao = st.form_submit_button("🚀 BẮT ĐẦU ĐÀO DATA", type="primary")

        if btn_dao and tu_khoa_goc.strip():
            tk_clean = tu_khoa_goc.strip().lower()
            danh_sach = set()
            queries = [tk_clean]
            if hd:
                for t in ["cách", "lỗi", "tại sao", "hướng dẫn", "giá", "không được"]: queries.extend([f"{t} {tk_clean}", f"{tk_clean} {t}"])
            if az:
                for char in string.ascii_lowercase: queries.append(f"{tk_clean} {char}")
                
            bar = st.progress(0)
            for i, q in enumerate(queries):
                res = lay_goi_y_google(q)
                for k in res:
                    if tk_clean in k.lower(): danh_sach.add(k)
                time.sleep(0.2)
                bar.progress((i + 1) / len(queries))
                    
            if 'ket_qua_gom_nhom' in st.session_state: del st.session_state['ket_qua_gom_nhom']
            st.session_state['data_tk_tho'] = sorted(list(danh_sach))
            st.session_state['tk_goc_active'] = tk_clean
            st.success(f"🎉 Khui mỏ thành công! Lấy được {len(st.session_state['data_tk_tho'])} từ khóa thô.")

        if 'data_tk_tho' in st.session_state and st.session_state['data_tk_tho']:
            tk_list = st.session_state['data_tk_tho']
            tk_goc = st.session_state['tk_goc_active']
            
            if st.button("🪄 CHẠY BỘ NÃO AI ĐỂ GOM NHÓM", type="primary", use_container_width=True, key="btn_ai_gom"):
                with st.spinner("AI đang gom nhóm..."):
                    clusters = gom_nhom_tu_khoa_bang_ai(tk_list[:150])
                    if clusters:
                        st.session_state['ket_qua_gom_nhom'] = clusters
                        st.success("✅ Gom nhóm hoàn tất!")
                    else: st.error("Lỗi AI!")

            if 'ket_qua_gom_nhom' in st.session_state and st.session_state['ket_qua_gom_nhom']:
                clusters = st.session_state['ket_qua_gom_nhom']
                danh_sach_xuat_excel = []
                for nhom in clusters:
                    with st.expander(f"📚 Chủ đề: {nhom.get('chu_de')} (Có {len(nhom.get('tu_khoa_phu', [])) + 1} bài viết)"):
                        st.markdown(f"**🔑 Từ Khóa Chính:** `{nhom.get('tu_khoa_chinh')}`")
                        tk_phu_str = ", ".join(nhom.get('tu_khoa_phu', []))
                        st.code(tk_phu_str)
                        danh_sach_xuat_excel.append({"Chủ Đề": nhom.get('chu_de', ''), "Từ Khóa Chính": nhom.get('tu_khoa_chinh', ''), "Từ Khóa Phụ": tk_phu_str})
                        
                col_luu1, col_luu2 = st.columns(2)
                with col_luu1:
                    if st.button("📊 ĐẨY VÀO SHEETS", use_container_width=True, key="btn_day_gom"):
                        ok, msg = day_data_gom_nhom_vao_sheets(clusters, tk_goc, gs_url_chung, gs_tab_dao)
                        if ok: st.success("✅ Đã chép lên Sheets!")
                with col_luu2:
                    df_gom = pd.DataFrame(danh_sach_xuat_excel)
                    st.download_button("⬇️ TẢI FILE CSV", data=df_gom.to_csv(index=False).encode('utf-8-sig'), file_name="ke_hoach_seo.csv", mime="text/csv", use_container_width=True)

    # ==========================================
    # TAB 2: ĐIỆP VIÊN CÀO ĐỐI THỦ (CÓ LỌC AI)
    # ==========================================
    with tab2:
        st.info("💡 Bot sẽ cào dữ liệu thô, sau đó dùng AI loại bỏ rác và tách ra Từ Khóa chuẩn SEO để sếp mang đi viết bài.")
        with st.form("form_cao_tu_khoa_v2"):
            col1, col2 = st.columns([3, 1])
            with col1: domain_input = st.text_input("🌐 Link Web Đối Thủ (VD: https://huyanphat.com)")
            with col2: so_trang_input = st.number_input("📄 Số trang quét", min_value=1, value=2)
            btn_scan = st.form_submit_button("🕵️‍♂️ BƯỚC 1: CÀO DATA THÔ", type="primary")

        # BƯỚC 1: CÀO THÔ
        if btn_scan and domain_input:
            domain_clean = domain_input.rstrip('/')
            danh_sach_tho = []
            headers = {'User-Agent': 'Mozilla/5.0'}
            
            bar_cao = st.progress(0)
            for page in range(1, so_trang_input + 1):
                try:
                    res = requests.get(f"{domain_clean}/wp-json/wp/v2/posts?per_page=100&page={page}", headers=headers, timeout=10)
                    if res.status_code != 200 or not res.json(): break
                    for post in res.json():
                        tieu_de = re.sub(r'<[^>]+>', '', post.get('title', {}).get('rendered', '')).replace('&#038;', '&')
                        danh_sach_tho.append({"tieude": tieu_de, "link": post.get('link', '')})
                    time.sleep(1)
                except: break
                bar_cao.progress(page / so_trang_input)
            
            if danh_sach_tho:
                st.session_state['data_doi_thu_tho'] = danh_sach_tho
                st.session_state['domain_hien_tai'] = domain_clean
                # Xóa data sạch cũ nếu có
                if 'data_doi_thu_sach' in st.session_state: del st.session_state['data_doi_thu_sach']
                st.success(f"🎉 Cào xong {len(danh_sach_tho)} tiêu đề thô!")
            else: st.error("❌ Không cào được data!")

        # BƯỚC 2: HIỆN NÚT LỌC AI
        if 'data_doi_thu_tho' in st.session_state:
            st.markdown("---")
            st.write(f"Đang có **{len(st.session_state['data_doi_thu_tho'])}** tiêu đề thô cần xử lý.")
            
            if st.button("🪄 BƯỚC 2: AI LỌC RÁC & RÚT GỌN THÀNH TỪ KHÓA", type="primary", use_container_width=True):
                with st.spinner("AI đang cặm cụi đọc tiêu đề, vứt rác và gọt giũa từ khóa..."):
                    # Gửi tối đa 150 bài cho AI 1 lần để tránh quá tải JSON
                    data_sach = loc_tu_khoa_doi_thu_bang_ai(st.session_state['data_doi_thu_tho'][:150])
                    if data_sach:
                        st.session_state['data_doi_thu_sach'] = data_sach
                        st.success(f"✅ AI đã lọc giữ lại được {len(data_sach)} Từ Khóa tinh khiết!")
                    else: st.error("❌ Lỗi mạng hoặc AI bận, sếp thử lại nhé.")

        # BƯỚC 3: HIỆN DATA ĐÃ LỌC & NÚT LƯU
        if 'data_doi_thu_sach' in st.session_state:
            st.markdown("### 🏆 DANH SÁCH TỪ KHÓA SEO ĐÃ GỌT GIŨA")
            df_dt = pd.DataFrame(st.session_state['data_doi_thu_sach'])
            st.dataframe(df_dt, use_container_width=True)
            
            col_save1, col_save2 = st.columns(2)
            with col_save1:
                if st.button("📊 ĐẨY VÀO GOOGLE SHEETS", use_container_width=True, type="primary", key="btn_day_cao"):
                    with st.spinner("Đang chép..."):
                        ok, msg = day_data_doi_thu_vao_sheets(st.session_state['data_doi_thu_sach'], st.session_state['domain_hien_tai'], gs_url_chung, gs_tab_cao)
                        if ok: st.success(f"✅ Đã chép vào Tab '{gs_tab_cao}'.")
                        else: st.error(f"Lỗi: {msg}")
                        
            with col_save2:
                # Đổi thành tải CSV, chia tay xlsxwriter
                csv_data = df_dt.to_csv(index=False).encode('utf-8-sig')
                st.download_button("⬇️ TẢI FILE CSV TỪ KHÓA", data=csv_data, file_name="tu_khoa_doi_thu_sach.csv", mime="text/csv", use_container_width=True)

if __name__ == "__main__":
    app_quan_ly_tu_khoa()