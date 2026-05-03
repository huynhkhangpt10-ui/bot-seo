"""
seo_desktop.py — Desktop App "Cỗ Máy SEO Auto 100%"
Eel backend — bọc toàn bộ tính năng từ Bot_SEO/app.py
"""

import eel, os, sys, json, re, random, threading, base64, time, subprocess
from datetime import datetime

# ── Đường dẫn ─────────────────────────────────────────────────────────────────
if getattr(sys, "frozen", False):
    BUNDLE_DIR  = sys._MEIPASS
    PROJECT_DIR = BUNDLE_DIR
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(BUNDLE_DIR, "vertex-key.json")
else:
    BUNDLE_DIR  = os.path.dirname(os.path.abspath(__file__))
    PROJECT_DIR = os.path.dirname(BUNDLE_DIR)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(PROJECT_DIR, "vertex-key.json")

WEB_DIR = os.path.join(BUNDLE_DIR, "web")
sys.path.insert(0, PROJECT_DIR)

# Chuyển CWD về Bot_SEO/ để tất cả đường dẫn tương đối hoạt động đúng
os.chdir(PROJECT_DIR)

# ── Mock Streamlit ─────────────────────────────────────────────────────────────
# my_modules.py, seo_doctor.py... có `import streamlit as st`.
# Khi chạy trong Eel/desktop app, Streamlit không có → cần mock để tránh crash.
import types as _types

def _make_st_mock():
    st = _types.ModuleType("streamlit")

    # Hàm trả về None (dùng cho gọi bình thường)
    _noop = lambda *a, **k: None

    # Decorator passthrough: dùng cho @st.cache_data / @st.cache_resource
    # Hỗ trợ cả @st.cache_data và @st.cache_data(ttl=3600)
    def _deco_factory(*a, **k):
        if len(a) == 1 and callable(a[0]) and not k:
            return a[0]          # @st.cache_data  (không có tham số)
        return lambda fn: fn     # @st.cache_data(ttl=...) (có tham số)

    for attr in ["error","warning","info","success","write","markdown",
                 "spinner","stop","rerun","caption",
                 "subheader","header","title","divider",
                 "dataframe","table","code","text","empty",
                 "button","checkbox","selectbox","multiselect",
                 "text_input","text_area","number_input","slider",
                 "file_uploader","progress","balloons","snow","toast",
                 "pyplot","image","video","audio",
                 "data_editor","metric","form","form_submit_button",
                 "set_page_config","experimental_rerun"]:
        setattr(st, attr, _noop)

    # Decorators đặc biệt
    st.cache_data     = _deco_factory
    st.cache_resource = _deco_factory

    # session_state
    st.session_state = {}

    # Context managers (columns, tabs, sidebar, expander, form...)
    class _CM:
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def __iter__(self): return iter([_CM(), _CM()])
        def __getattr__(self, name): return lambda *a, **k: None

    st.columns  = lambda *a, **k: _CM()
    st.tabs     = lambda labels: [_CM() for _ in labels]
    st.sidebar  = _CM()
    st.expander = lambda *a, **k: _CM()
    st.form     = lambda *a, **k: _CM()
    return st

import sys as _sys
if "streamlit" not in _sys.modules:
    _sys.modules["streamlit"] = _make_st_mock()
# ────────────────────────────────────────────────────────────────────────────────

# ── Import modules ─────────────────────────────────────────────────────────────
from my_config import (client, WP_USER, WP_APP_PASS, WP_POSTS_URL,
                        WP_TAGS_URL, WP_CAT_URL, WP_MEDIA_URL,
                        GOOGLE_SEARCH_API_KEY,
                        cons_key, cons_sec, oa_tok, oa_sec)

# Luôn trỏ đúng vị trí file key dù chạy từ thư mục nào
GOOGLE_KEY_PATH = os.path.join(PROJECT_DIR, "google-key.json")
import my_modules as mm
from module_content  import sinh_dan_y, sinh_bai_viet
import nap_tai_lieu
import chromadb, requests

eel.init(WEB_DIR)

# ════════════════════════════════════════════════════════════════════════════════
# TIỆN ÍCH NỘI BỘ
# ════════════════════════════════════════════════════════════════════════════════
UI_FILE = os.path.join(PROJECT_DIR, "ui_settings.json")

def _slug(text):
    s = text.lower().strip()
    for v,a in {"à":"a","á":"a","â":"a","ã":"a","ă":"a","ắ":"a","ặ":"a","ẵ":"a","ẫ":"a","ấ":"a","ầ":"a","ẩ":"a",
                "è":"e","é":"e","ê":"e","ế":"e","ề":"e","ệ":"e","ễ":"e","ẻ":"e","ẽ":"e",
                "ì":"i","í":"i","î":"i","ỉ":"i","ĩ":"i","ị":"i",
                "ò":"o","ó":"o","ô":"o","õ":"o","ố":"o","ồ":"o","ổ":"o","ỗ":"o","ộ":"o",
                "ơ":"o","ớ":"o","ờ":"o","ở":"o","ỡ":"o","ợ":"o",
                "ù":"u","ú":"u","û":"u","ứ":"u","ừ":"u","ử":"u","ữ":"u","ự":"u",
                "ý":"y","ỳ":"y","ỵ":"y","ỷ":"y","ỹ":"y","đ":"d"}.items():
        s = s.replace(v, a)
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    return re.sub(r"\s+", "-", s).strip("-")

def _chon_khach_dia(tu_khoa):
    dia = random.choice(["Quận 1","Quận 7","Bình Thạnh","Gò Vấp","Tân Bình","TP Thủ Đức"])
    tk = tu_khoa.lower()
    if any(x in tk for x in ["autocad","revit","inventor","solidworks","sketchup","autodesk"]):
        pool = ["một văn phòng kiến trúc","một xưởng cơ khí","một công ty xây dựng"]
    elif any(x in tk for x in ["photoshop","illustrator","premiere","adobe","capcut"]):
        pool = ["một studio thiết kế","một kênh YouTube","một công ty truyền thông"]
    elif any(x in tk for x in ["office","word","excel","windows"]):
        pool = ["một văn phòng hành chính","một công ty kế toán","một giáo viên"]
    else:
        pool = ["một anh kỹ thuật viên","một bạn trẻ yêu công nghệ","một doanh nghiệp vừa và nhỏ"]
    return random.choice(pool), dia

def _push_log(fn_name, msg):
    """Gửi log về JS. fn_name = tên hàm eel JS phía client."""
    try:
        getattr(eel, fn_name)(str(msg).replace("**",""))()
    except Exception:
        pass

# ════════════════════════════════════════════════════════════════════════════════
# CẤU HÌNH / SIDEBAR
# ════════════════════════════════════════════════════════════════════════════════

@eel.expose
def tai_cau_hinh():
    try:
        with open(UI_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

@eel.expose
def luu_cau_hinh(cfg: dict):
    try:
        with open(UI_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@eel.expose
def lay_wp_tags():
    try:
        r = requests.get(f"{WP_TAGS_URL}?per_page=100",
                         auth=(WP_USER, WP_APP_PASS), timeout=15)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []

@eel.expose
def lay_wp_categories():
    try:
        r = requests.get(f"{WP_CAT_URL}?per_page=100",
                         auth=(WP_USER, WP_APP_PASS), timeout=15)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []

@eel.expose
def lay_fb_pages():
    fp = os.path.join(PROJECT_DIR, "fb_pages.json")
    try:
        with open(fp, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

@eel.expose
def luu_fb_pages(pages: list):
    fp = os.path.join(PROJECT_DIR, "fb_pages.json")
    try:
        with open(fp, "w", encoding="utf-8") as f:
            json.dump(pages, f, ensure_ascii=False, indent=2)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ════════════════════════════════════════════════════════════════════════════════
# TAB 1 — VIẾT BÀI THỦ CÔNG
# ════════════════════════════════════════════════════════════════════════════════

@eel.expose
def buoc1_dan_y(tu_khoa: str, tieu_de_goi_y: str = "") -> dict:
    """Bước 1: Sinh dàn ý + tiêu đề SEO + meta."""
    tu_khoa = tu_khoa.strip()
    if not tu_khoa:
        return {"ok": False, "error": "Thiếu từ khoá!"}

    def cb(msg): _push_log("log_tab1", msg)
    try:
        ok, outline, tieu_de, meta, tu_khoa_phu = sinh_dan_y(
            tk_auto=tu_khoa, tieu_de_excel=tieu_de_goi_y,
            lenh_tim_kiem_ai="", cap_nhat_trang_thai_func=cb)
        if not ok:
            return {"ok": False, "error": outline}
        return {"ok": True, "outline": outline, "tieu_de": tieu_de,
                "meta": meta, "tu_khoa_phu": tu_khoa_phu}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@eel.expose
def buoc2_viet_bai(tu_khoa: str, tieu_de: str, outline: str,
                    anchor1: str = "", url1: str = "",
                    anchor2: str = "", url2: str = "",
                    anchor_out: str = "", url_out: str = "") -> dict:
    """Bước 2: Viết bài từ dàn ý."""
    tu_khoa = tu_khoa.strip()
    khach, dia = _chon_khach_dia(tu_khoa)
    nam = str(datetime.now().year)
    short_slug = _slug(tu_khoa)

    link_ins = ""
    if anchor1 and url1:
        link_ins += f"[LINK DÀNH CHO HỘP BÀI LIÊN QUAN]:\n- [{anchor1}]({url1})\n"
        if anchor2 and url2:
            link_ins += f"- [{anchor2}]({url2})\n"
    else:
        link_ins = "[LINK DÀNH CHO HỘP BÀI LIÊN QUAN]: TRỐNG! TUYỆT ĐỐI KHÔNG TẠO HỘP NÀY.\n"
    if anchor_out and url_out:
        link_ins += f"\n[LINK DỊCH VỤ - BẮT BUỘC CHÈN NGỮ CẢNH]:\n- [{anchor_out}]({url_out})\n"

    def cb(msg): _push_log("log_tab1", msg)
    try:
        ok, bai = sinh_bai_viet(
            tk_auto=tu_khoa, tieu_de_seo_auto=tieu_de, short_slug_auto=short_slug,
            link_ins_auto=link_ins, outline_auto=outline, nam_hien_tai=nam,
            khach_hang_rd=khach, dia_diem_rd=dia, lenh_tim_kiem_ai="",
            cap_nhat_trang_thai_func=cb)
        if not ok:
            return {"ok": False, "error": bai}
        return {"ok": True, "bai_viet": bai}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@eel.expose
def dang_bai_wp(tieu_de: str, noi_dung: str, danh_muc_ids: list,
                 the_ids: list, trang_thai: str = "publish",
                 meta_desc: str = "") -> dict:
    """Đăng bài lên WordPress."""
    try:
        payload = {"title": tieu_de, "content": noi_dung,
                   "status": trang_thai, "categories": danh_muc_ids,
                   "tags": the_ids}
        r = requests.post(WP_POSTS_URL, json=payload,
                          auth=(WP_USER, WP_APP_PASS), timeout=30)
        if r.status_code in (200, 201):
            data = r.json()
            return {"ok": True, "link": data.get("link", ""), "id": data.get("id")}
        return {"ok": False, "error": f"HTTP {r.status_code}: {r.text[:300]}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@eel.expose
def dang_bai_zalo(tieu_de: str, noi_dung_html: str, link_web: str,
                   mo_ta: str = "") -> dict:
    try:
        ok, msg = mm.dang_bai_zalo_oa(tieu_de, mo_ta or tieu_de,
                                       None, noi_dung_html, link_web)
        return {"ok": ok, "msg": msg}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@eel.expose
def dang_bai_facebook(tieu_de: str, noi_dung_html: str, link_web: str) -> dict:
    try:
        ok, msg = mm.dang_bai_facebook(tieu_de, noi_dung_html, link_web, None)
        return {"ok": ok, "msg": msg}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@eel.expose
def luu_bai(tieu_de: str, noi_dung: str) -> dict:
    try:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        slug = _slug(tieu_de) if tieu_de else "bai-viet-seo"
        fp = os.path.join(desktop, f"{slug}.html")
        html = (f'<!DOCTYPE html><html lang="vi"><head><meta charset="UTF-8">'
                f'<title>{tieu_de}</title></head><body>'
                f'<h1>{tieu_de}</h1>\n{noi_dung}\n</body></html>')
        with open(fp, "w", encoding="utf-8") as f:
            f.write(html)
        return {"ok": True, "path": fp}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# Alias cho Tab Tự Động
@eel.expose
def tao_bai(tu_khoa: str, so_trang: int = 5, nguon: str = "google") -> dict:
    def cb(msg): _push_log("log_tab1", msg)
    khach, dia = _chon_khach_dia(tu_khoa)
    nam = str(datetime.now().year)
    try:
        ok, outline, tieu_de, meta, tu_khoa_phu = sinh_dan_y(
            tk_auto=tu_khoa, tieu_de_excel="", lenh_tim_kiem_ai="",
            cap_nhat_trang_thai_func=cb)
        if not ok:
            return {"ok": False, "error": outline}
        cb(f"✅ Dàn ý xong → viết bài...")
        ok2, bai = sinh_bai_viet(
            tk_auto=tu_khoa, tieu_de_seo_auto=tieu_de,
            short_slug_auto=_slug(tu_khoa),
            link_ins_auto="[LINK DÀNH CHO HỘP BÀI LIÊN QUAN]: TRỐNG! TUYỆT ĐỐI KHÔNG TẠO HỘP NÀY.\n",
            outline_auto=outline, nam_hien_tai=nam,
            khach_hang_rd=khach, dia_diem_rd=dia, lenh_tim_kiem_ai="",
            cap_nhat_trang_thai_func=cb)
        if not ok2:
            return {"ok": False, "error": bai}
        return {"ok": True, "tieu_de": tieu_de, "noi_dung": bai,
                "meta": meta, "tu_khoa_phu": tu_khoa_phu}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ════════════════════════════════════════════════════════════════════════════════
# TAB 2 — TỰ ĐỘNG GOOGLE SHEETS
# ════════════════════════════════════════════════════════════════════════════════

_sheets_cache = {}  # gs_url -> {spreadsheet, worksheet, df}

@eel.expose
def ket_noi_sheets(gs_url: str, tab_name: str = "Tukhoa") -> dict:
    try:
        import gspread, pandas as pd
        gc = gspread.service_account(GOOGLE_KEY_PATH)
        sp = gc.open_by_url(gs_url)
        ws = sp.worksheet(tab_name)
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        _sheets_cache["current"] = {"spreadsheet": sp, "worksheet": ws,
                                     "df": df, "gs_url": gs_url}
        hang_doi = df[(df.get("Trạng thái", pd.Series(dtype=str)).astype(str) == "") &
                       (df.get("Từ khóa", pd.Series(dtype=str)).astype(str) != "")].shape[0] if "Trạng thái" in df.columns else 0
        return {"ok": True, "so_hang": len(df), "so_hang_doi": hang_doi,
                "columns": list(df.columns)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@eel.expose
def lay_hang_doi() -> list:
    if "current" not in _sheets_cache:
        return []
    import pandas as pd
    df = _sheets_cache["current"]["df"]
    if "Trạng thái" not in df.columns or "Từ khóa" not in df.columns:
        return []
    mask = (df["Trạng thái"].astype(str) == "") & (df["Từ khóa"].astype(str) != "")
    return df[mask]["Từ khóa"].tolist()

@eel.expose
def chay_auto_sheets(gs_url: str, tab_name: str,
                      cho_phep_web: bool = True,
                      cho_phep_zalo: bool = False,
                      cho_phep_fb: bool = False) -> dict:
    """Khởi động cỗ máy tự động — dùng quy_trinh_dang_bai_full() y hệt Streamlit."""

    def _worker():
        try:
            import gspread, pandas as pd
            import seo_doctor
            from my_modules import (quy_trinh_dang_bai_full,
                                    reset_dem_so_bai, rut_gon_tu_khoa)

            _push_log("log_tab2", "🚀 Cỗ máy khởi động — kết nối Sheets...")

            # ── Kết nối Sheets ──────────────────────────────────────────────
            gc = gspread.service_account(filename=GOOGLE_KEY_PATH)
            sh = gc.open_by_url(gs_url)
            ws = sh.worksheet(tab_name)
            df = pd.DataFrame(ws.get_all_records())

            if df.empty or "Trạng thái" not in df.columns:
                _push_log("log_tab2", "❌ Sheet trống hoặc thiếu cột 'Trạng thái'")
                return

            # ── Đọc API_KEY tab ─────────────────────────────────────────────
            try:
                ws_api = sh.worksheet("API_KEY")
                danh_sach_api_keys = [
                    k.strip() for k in ws_api.col_values(1)[1:] if k.strip()
                ][::-1]
                _push_log("log_tab2", f"🔑 Nạp {len(danh_sach_api_keys)} API key")
            except Exception:
                danh_sach_api_keys = []
                _push_log("log_tab2", "⚠️ Không tìm thấy tab API_KEY — dùng key mặc định")

            # ── Đọc KhoLink tab ─────────────────────────────────────────────
            kho_link_list = []
            ws_kho = None
            try:
                ws_kho = sh.worksheet("KhoLink")
                kho_data = ws_kho.get_all_values()
                for i, r in enumerate(kho_data[1:] if len(kho_data) > 1 else []):
                    if len(r) >= 2 and str(r[1]).startswith("http"):
                        kho_link_list.append({"row": i+2, "anchor": r[0], "url": r[1]})
                _push_log("log_tab2", f"🔗 Nạp {len(kho_link_list)} link nội bộ từ KhoLink")
            except Exception:
                _push_log("log_tab2", "⚠️ Không tìm thấy tab KhoLink")

            # ── Đọc cấu hình sidebar (ui_settings.json) ─────────────────────
            cfg = tai_cau_hinh()
            trang_thai_wp = "publish"
            st_cfg = cfg.get("trang_thai", "publish")
            if "Lên lịch" in st_cfg:   trang_thai_wp = "scheduled"
            elif "Đăng nóng" in st_cfg: trang_thai_wp = "publish_now"
            else:                        trang_thai_wp = "draft"

            # Lấy category/tag IDs
            danh_sach_dm_id = []
            danh_sach_the_id = []
            try:
                cats = lay_wp_categories()
                dm_name = cfg.get("danh_muc", "")
                danh_sach_dm_id = [c["id"] for c in cats if str(c.get("id")) == str(dm_name) or c.get("name") == dm_name]
            except Exception: pass
            try:
                tags = lay_wp_tags()
                tag_val = cfg.get("tag", "")
                danh_sach_the_id = [t["id"] for t in tags if str(t.get("id")) == str(tag_val)]
            except Exception: pass

            # Author block / shortcode từ ui_settings
            author_block_code  = cfg.get("author_block_code", "")
            flatsome_shortcode = cfg.get("flatsome_shortcode", "")

            # ── Hàng đợi ────────────────────────────────────────────────────
            hang_doi = df[
                (df["Trạng thái"].astype(str).str.strip() == "") &
                (df["Từ khóa"].astype(str).str.strip() != "")
            ]
            _push_log("log_tab2", f"📋 Tìm thấy {len(hang_doi)} bài cần viết")
            reset_dem_so_bai()

            cols = df.columns.tolist()
            col_tt   = cols.index("Trạng thái") + 1
            col_link = cols.index("Link bài viết") + 1 if "Link bài viết" in cols else None

            dem = 0
            for idx, row in hang_doi.iterrows():
                if os.path.exists("stop_auto.txt"):
                    os.remove("stop_auto.txt")
                    _push_log("log_tab2", "🛑 Nhận lệnh dừng khẩn cấp!")
                    break

                row_sheet = idx + 2
                tk = rut_gon_tu_khoa(str(row.get("Từ khóa", "")).strip())
                if not tk:
                    continue

                tk_phu    = str(row.get("Từ khóa phụ", "")).strip()
                link_goc  = str(row.get("Link Bài Gốc", row.get("Link tham khảo", ""))).strip()
                link_tai  = ""
                try:
                    vals = list(row.values)
                    if len(vals) >= 8 and str(vals[7]).startswith("http"):
                        link_tai = str(vals[7]).strip()
                except Exception: pass
                if not link_goc.startswith("http"): link_goc = ""

                _push_log("log_tab2", f"\n⚙️ [{row_sheet}] Đang viết: «{tk}»...")
                try:
                    ws.update_cell(row_sheet, col_tt, "⏳ Đang viết bài...")
                except Exception: pass

                def cb(msg, _tk=tk):
                    _push_log("log_tab2", str(msg))

                # ── GỌI PIPELINE ĐẦY ĐỦ ────────────────────────────────────
                thanh_cong, msg_tt, link_bai = quy_trinh_dang_bai_full(
                    tk_auto               = tk,
                    tieu_de_excel         = tk_phu,
                    danh_sach_api_keys    = danh_sach_api_keys,
                    kho_link_list         = kho_link_list,
                    ws_kho                = ws_kho,
                    author_block_code     = author_block_code,
                    flatsome_shortcode    = flatsome_shortcode,
                    danh_sach_dm_id_auto  = danh_sach_dm_id,
                    danh_sach_the_id_auto = danh_sach_the_id,
                    trang_thai_wp         = trang_thai_wp,
                    cap_nhat_trang_thai_func = cb,
                    cho_phep_zalo         = cho_phep_zalo,
                    cho_phep_facebook     = cho_phep_fb,
                    cho_phep_web          = cho_phep_web,
                    row_index             = row_sheet,
                    sh                    = sh,
                    link_bai_goc          = link_goc,
                    link_tai_thu_cong     = link_tai,
                )

                if thanh_cong:
                    try: ws.update_cell(row_sheet, col_tt, "Hoàn thành")
                    except Exception: pass
                    if col_link and link_bai:
                        try: ws.update_cell(row_sheet, col_link, link_bai)
                        except Exception: pass
                    # Append KhoLink
                    if ws_kho and link_bai.startswith("http"):
                        try:
                            ws_kho.append_row([tk, link_bai, "Sống"])
                            kho_link_list.append({"row": 999, "anchor": tk, "url": link_bai})
                        except Exception: pass
                    # Ép Google Index
                    if link_bai.startswith("http"):
                        try:
                            ok_idx, msg_idx = seo_doctor.ep_index_url(link_bai)
                            _push_log("log_tab2", f"{'🎉' if ok_idx else '⚠️'} Index: {msg_idx}")
                        except Exception as e_idx:
                            _push_log("log_tab2", f"⚠️ Ép index lỗi: {e_idx}")
                    _push_log("log_tab2", f"✅ Xong! {link_bai}")
                else:
                    try: ws.update_cell(row_sheet, col_tt, f"❌ Lỗi: {msg_tt[:80]}")
                    except Exception: pass
                    _push_log("log_tab2", f"❌ Lỗi: {msg_tt}")

                dem += 1
                if dem < len(hang_doi):
                    sleep_s = random.randint(300, 600)
                    _push_log("log_tab2",
                              f"☕ Nghỉ {sleep_s//60}p{sleep_s%60}s trước bài tiếp...")
                    time.sleep(sleep_s)

            _push_log("log_tab2", f"\n🎉 Hoàn tất! Đã viết {dem}/{len(hang_doi)} bài")
            eel.tab2_done()()

        except Exception as e:
            import traceback
            _push_log("log_tab2", f"❌ Lỗi hệ thống: {e}\n{traceback.format_exc()[-300:]}")

    threading.Thread(target=_worker, daemon=True).start()
    return {"ok": True, "msg": "🚀 Đã khởi động cỗ máy — xem Nhật Ký bên dưới!"}

@eel.expose
def dung_auto():
    with open("stop_auto.txt", "w") as f:
        f.write("stop")
    return {"ok": True}

# ════════════════════════════════════════════════════════════════════════════════
# TAB 3 — BÁC SĨ SEO
# ════════════════════════════════════════════════════════════════════════════════

@eel.expose
def bac_si_ket_noi_gsc() -> dict:
    try:
        import seo_doctor as sd
        service = sd.ket_noi_gsc()
        return {"ok": True, "msg": "✅ Đã kết nối Google Search Console!"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@eel.expose
def bac_si_chay_audit(loai: str, days: int = 30) -> dict:
    """loai: cannibalization | decay | zombie | onpage | organic"""
    try:
        import seo_doctor as sd
        import pandas as pd
        SITE = "https://huynhkhang.com/"
        service = sd.ket_noi_gsc()
        df = sd.fetch_gsc_data(service, SITE, days_start=days)

        if loai == "cannibalization":
            result_df = sd.audit_cannibalization(df)
        elif loai == "decay":
            result_df = sd.audit_content_decay(service, SITE)
        elif loai == "zombie":
            result_df = sd.audit_zombie_pages(service, SITE)
        elif loai == "onpage":
            result_df = sd.audit_onpage_full(df)
        elif loai == "organic":
            result_df = sd.audit_organic_only(df)
        else:
            return {"ok": False, "error": f"Loại audit không hợp lệ: {loai}"}

        if result_df is None or result_df.empty:
            return {"ok": True, "data": [], "msg": "Không có dữ liệu"}

        return {"ok": True, "data": result_df.head(50).to_dict("records"),
                "columns": list(result_df.columns), "total": len(result_df)}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@eel.expose
def bac_si_check_index(urls: list) -> dict:
    try:
        import seo_doctor as sd
        SITE = "https://huynhkhang.com/"
        results = []
        for u in urls[:50]:
            u = u.strip()
            if not u: continue
            try:
                r = sd.check_url_index(SITE, u)
                results.append({"url": u, "indexed": bool(r), "result": str(r)[:100]})
            except Exception as e:
                results.append({"url": u, "indexed": False, "result": str(e)[:80]})
        return {"ok": True, "results": results}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@eel.expose
def bac_si_ep_index(urls: list) -> dict:
    try:
        import seo_doctor as sd
        thanh_cong = 0
        for u in urls[:200]:
            u = u.strip()
            if not u: continue
            try:
                sd.ep_index_url(u)
                thanh_cong += 1
                _push_log("log_tab3", f"✅ Ép index: {u}")
            except Exception as e:
                _push_log("log_tab3", f"❌ Lỗi: {u} — {e}")
        return {"ok": True, "thanh_cong": thanh_cong}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@eel.expose
def bac_si_vet_mang_sheets(gs_url: str, tab_name: str = "Tukhoa") -> dict:
    try:
        import seo_doctor as sd
        import gspread
        SITE = "https://huynhkhang.com/"
        service = sd.ket_noi_gsc()
        gc = gspread.service_account(GOOGLE_KEY_PATH)
        sp = gc.open_by_url(gs_url)
        ws = sp.worksheet(tab_name)
        data = ws.get_all_records()
        current_kws = [r.get("Từ khóa","") for r in data if r.get("Từ khóa","")]
        sd.fetch_and_push_to_sheets(service, SITE, ws, current_kws)
        return {"ok": True, "msg": "✅ Đã vét mảng và bơm vào Sheets!"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@eel.expose
def bac_si_ke_don(url: str, loai_benh: str) -> dict:
    try:
        import seo_doctor as sd
        row_data = sd.tim_post_id_tu_url(url)
        phac_do = sd.ke_don_seo_ai(row_data, loai_benh, url)
        return {"ok": True, "phac_do": phac_do}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@eel.expose
def bac_si_phau_thuat(url: str, benh_ly: str, phac_do: str) -> dict:
    try:
        import seo_doctor as sd
        ok, msg = sd.phau_thuat_nang_cap_bai_viet(url, benh_ly, phac_do)
        return {"ok": ok, "msg": msg}
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ════════════════════════════════════════════════════════════════════════════════
# TAB 4 — TRẠM VỆ TINH
# ════════════════════════════════════════════════════════════════════════════════

@eel.expose
def ve_tinh_lay_nguyen_lieu() -> list:
    """Lấy danh sách từ khoá 'Hoàn thành' từ Sheets để bắn vệ tinh."""
    if "current" not in _sheets_cache:
        return []
    import pandas as pd
    df = _sheets_cache["current"]["df"]
    cols = df.columns.tolist()
    if "Trạng thái" not in cols or "Từ khóa" not in cols:
        return []
    mask = df["Trạng thái"].astype(str).str.contains("Hoàn thành", na=False)
    rows = df[mask]
    results = []
    for _, row in rows.iterrows():
        tk = str(row.get("Từ khóa","")).strip()
        link = str(row.get("Link bài viết","")).strip()
        so_ve_tinh = str(row.get("Số bài Vệ tinh","0"))
        if tk:
            results.append({"tu_khoa": tk, "link": link, "so_ve_tinh": so_ve_tinh})
    return results

@eel.expose
def ve_tinh_xem_truoc(tu_khoa: str, link_chinh: str = "") -> dict:
    try:
        from satellite_worker import xem_truoc_bai_ve_tinh
        res = xem_truoc_bai_ve_tinh(tu_khoa, link_chinh, client)
        if res:
            return {"ok": True, **res}
        # Nếu hàm chưa implement (pass), tạo preview giả
        return {"ok": True, "tieu_de": f"Bài vệ tinh về {tu_khoa}",
                "noi_dung": "(Preview sẽ có sau khi hàm xem_truoc_bai_ve_tinh được implement)"}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@eel.expose
def ve_tinh_khoi_dong(danh_sach: list, quota_day: int = 12,
                       max_posts: int = 3, sleep_min: int = 10) -> dict:
    def _worker():
        try:
            from satellite_worker import thuc_thi_ban_ve_tinh
            import pandas as pd
            if "current" in _sheets_cache:
                ws = _sheets_cache["current"]["worksheet"]
                df = _sheets_cache["current"]["df"]
            else:
                ws, df = None, pd.DataFrame()

            thuc_thi_ban_ve_tinh(
                danh_sach_cho=danh_sach,
                quota_day=quota_day,
                max_satellite_posts=max_posts,
                sleep_time=(sleep_min, sleep_min + 5),
                worksheet=ws, df=df, client_ai=client)
            _push_log("log_tab4", "🎉 Hoàn tất bắn vệ tinh!")
            eel.tab4_done()()
        except Exception as e:
            _push_log("log_tab4", f"❌ Lỗi vệ tinh: {e}")

    threading.Thread(target=_worker, daemon=True).start()
    return {"ok": True, "msg": "🚀 Đã khởi động trạm vệ tinh!"}

@eel.expose
def ve_tinh_dung():
    with open("stop_vetinh.txt", "w") as f:
        f.write("stop")
    return {"ok": True}

# ════════════════════════════════════════════════════════════════════════════════
# TAB 5 — KHO DỮ LIỆU (RAG)
# ════════════════════════════════════════════════════════════════════════════════

@eel.expose
def nap_file_vao_kho(files_data: list) -> dict:
    try:
        thu_muc = os.path.join(PROJECT_DIR, "Nguon_Tai_Lieu_Tho")
        os.makedirs(thu_muc, exist_ok=True)
        da_luu = []
        for f in files_data:
            fp = os.path.join(thu_muc, f["name"])
            with open(fp, "wb") as fh:
                fh.write(base64.b64decode(f["data"]))
            da_luu.append(f["name"])
            _push_log("log_rag", f"💾 Đã lưu: {f['name']}")

        _push_log("log_rag", f"✅ Lưu xong {len(da_luu)} file → bắt đầu nhai...")
        _orig = nap_tai_lieu.ghi_log
        nap_tai_lieu.ghi_log = lambda m: (_orig(m), _push_log("log_rag", m))
        try:
            nap_tai_lieu.nap_vao_kho()
        finally:
            nap_tai_lieu.ghi_log = _orig
        return {"ok": True, "msg": f"🎉 Nhai xong {len(da_luu)} file!"}
    except Exception as e:
        return {"ok": False, "msg": f"❌ {e}"}

@eel.expose
def nap_tu_thu_muc() -> dict:
    try:
        _orig = nap_tai_lieu.ghi_log
        nap_tai_lieu.ghi_log = lambda m: (_orig(m), _push_log("log_rag", m))
        try:
            nap_tai_lieu.nap_vao_kho()
        finally:
            nap_tai_lieu.ghi_log = _orig
        return {"ok": True, "msg": "🎉 Nhai xong toàn bộ thư mục!"}
    except Exception as e:
        return {"ok": False, "msg": f"❌ {e}"}

@eel.expose
def lay_thong_ke_kho() -> dict:
    try:
        kp = os.path.join(PROJECT_DIR, "Kho_Du_Lieu_Vector")
        cli = chromadb.PersistentClient(path=kp)
        col = cli.get_or_create_collection("tai_lieu_seo")
        so_doan = col.count()
        data = col.get(include=["metadatas"], limit=99999)
        nguon = set(m["nguon_goc"] for m in (data.get("metadatas") or [])
                    if m and m.get("nguon_goc"))
        return {"so_doan": so_doan, "so_file": len(nguon)}
    except Exception:
        return {"so_doan": 0, "so_file": 0}

@eel.expose
def xem_kho_rag(limit: int = 10) -> list:
    try:
        kp = os.path.join(PROJECT_DIR, "Kho_Du_Lieu_Vector")
        cli = chromadb.PersistentClient(path=kp)
        col = cli.get_collection("tai_lieu_seo")
        data = col.peek(limit=limit)
        results = []
        for doc, meta in zip(data["documents"], data["metadatas"]):
            results.append({"nguon": meta.get("nguon_goc","?"), "doan": doc[:400]})
        return results
    except Exception:
        return []

@eel.expose
def xoa_kho_rag() -> dict:
    try:
        kp = os.path.join(PROJECT_DIR, "Kho_Du_Lieu_Vector")
        cli = chromadb.PersistentClient(path=kp)
        cli.delete_collection("tai_lieu_seo")
        return {"ok": True, "msg": "🗑️ Đã xoá sạch kho RAG!"}
    except Exception as e:
        return {"ok": False, "msg": str(e)}

# ════════════════════════════════════════════════════════════════════════════════
# TAB 6 — CÀO WEB → PDF
# ════════════════════════════════════════════════════════════════════════════════

@eel.expose
def cao_web_bat_dau(urls: list, thu_muc: str = "./Nguon_Tai_Lieu_Tho",
                    max_bai: int = 2000, nap_rag: bool = True,
                    loc_ai: bool = True) -> dict:
    """Khởi động worker cào web trong thread riêng."""
    urls = [u.strip() for u in urls if u.strip()]
    if not urls:
        return {"ok": False, "error": "Chưa nhập URL!"}

    # Import worker từ app.py gốc (tái sử dụng logic)
    def _run():
        try:
            import asyncio, urllib.parse, re as _re, json as _json
            if sys.platform == "win32":
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            from playwright.sync_api import sync_playwright
            _MODEL = "gemini-2.5-flash"

            def _kiem_tra(text):
                if not loc_ai: return True
                text = text.strip()
                if len(text) < 150: return False
                try:
                    prompt = ("Nội dung trang web sau có hữu ích không (hướng dẫn, tutorial, "
                              "tài liệu kỹ thuật, FAQ)? Trả lời chỉ YES hoặc NO.\n\n"
                              f"{text[:3000]}")
                    r = client.models.generate_content(model=_MODEL, contents=[prompt])
                    return r.text.strip().upper().startswith("YES")
                except Exception:
                    return True

            os.makedirs(thu_muc, exist_ok=True)
            _push_log("log_cao_web", f"🕷️ Bắt đầu cào {len(urls)} URL gốc...")

            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True,
                    args=["--disable-web-security","--no-sandbox"])
                ctx = browser.new_context(
                    viewport={"width":1440,"height":900},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0")
                trang = ctx.new_page()

                tat_ca_link = []
                for url_goc in urls:
                    trang.goto(url_goc, wait_until="networkidle", timeout=45000)
                    time.sleep(2)
                    base_path = url_goc.split("?")[0].rstrip("/") + "/"

                    # Thu thập link đơn giản
                    raw = trang.evaluate("""(() => {
                        var s=new Set();
                        document.querySelectorAll('a[href]').forEach(a => {
                            try{s.add(new URL(a.href,location.href).href.split('#')[0]);}catch(e){}
                        });
                        return Array.from(s);
                    })()""")
                    links = [l for l in (raw or []) if l.startswith(base_path) and l != url_goc]
                    tat_ca_link.extend(links)
                    _push_log("log_cao_web", f"🔗 Thu được {len(links)} link từ {url_goc}")

                tat_ca_link = list(dict.fromkeys(tat_ca_link))[:max_bai]
                _push_log("log_cao_web", f"📋 Tổng {len(tat_ca_link)} link sẽ xử lý")

                thanh_cong = bo_qua = 0
                for i, url_bai in enumerate(tat_ca_link):
                    _push_log("log_cao_web", f"[{i+1}/{len(tat_ca_link)}] {url_bai}")
                    try:
                        resp = trang.goto(url_bai, wait_until="networkidle", timeout=45000)
                        if resp and resp.status >= 400:
                            _push_log("log_cao_web", f"   ⚠️ HTTP {resp.status} — bỏ qua")
                            bo_qua += 1; continue

                        body = trang.evaluate("(() => document.body.innerText.toLowerCase())()")
                        if any(k in body for k in ["404","page not found","we lost this page"]):
                            _push_log("log_cao_web", f"   ⚠️ CSR-404 — bỏ qua")
                            bo_qua += 1; continue

                        if not _kiem_tra(trang.evaluate("(()=>document.body.innerText)()")):
                            _push_log("log_cao_web", f"   🚫 AI lọc trang rác")
                            bo_qua += 1; continue

                        # Làm sạch DOM
                        trang.evaluate("""(() => {
                            ['header','footer','nav','aside','video','audio','form',
                             'script','noscript','style','img',
                             '[class*="sidebar"]','[class*="nav"]','[class*="ads"]',
                             '[class*="banner"]','[class*="cookie"]'].forEach(s => {
                                document.querySelectorAll(s).forEach(e => e.remove());
                            });
                        })()""")

                        ten_file = _slug(url_bai.split("/")[-1] or f"trang-{i+1}")
                        pdf_path = os.path.join(os.path.abspath(thu_muc), f"{ten_file}.pdf")
                        trang.pdf(path=pdf_path, format="A4",
                                  margin={"top":"20mm","bottom":"20mm",
                                          "left":"15mm","right":"15mm"})
                        thanh_cong += 1
                        _push_log("log_cao_web", f"   ✅ PDF: {ten_file}.pdf")
                    except Exception as e_bai:
                        _push_log("log_cao_web", f"   ❌ Lỗi: {e_bai}")

                browser.close()

            if nap_rag and thanh_cong > 0:
                _push_log("log_cao_web", "🧠 Bơm vào kho RAG...")
                nap_tai_lieu.nap_vao_kho()

            msg = f"🎉 Hoàn tất! {thanh_cong} PDF | bỏ qua {bo_qua} trang lỗi/rác"
            _push_log("log_cao_web", msg)
            eel.cao_web_done(msg)()

        except Exception as e:
            _push_log("log_cao_web", f"❌ Lỗi hệ thống: {e}")

    threading.Thread(target=_run, daemon=True).start()
    return {"ok": True, "msg": "🕷️ Đã khởi động bot cào web!"}

# ════════════════════════════════════════════════════════════════════════════════
# TỰ CẬP NHẬT (Git Pull)
# ════════════════════════════════════════════════════════════════════════════════

def _git(cmd: list, cwd: str) -> tuple[bool, str]:
    """Chạy lệnh git, trả về (ok, output)."""
    try:
        r = subprocess.run(["git"] + cmd, cwd=cwd,
                           capture_output=True, text=True, timeout=30)
        out = (r.stdout + r.stderr).strip()
        return r.returncode == 0, out
    except FileNotFoundError:
        return False, "Git chưa được cài đặt trên máy này."
    except subprocess.TimeoutExpired:
        return False, "Kết nối Git timeout (30s)."
    except Exception as e:
        return False, str(e)

@eel.expose
def kiem_tra_cap_nhat() -> dict:
    """
    Kiểm tra xem có commit mới trên remote chưa.
    Trả về: { co_cap_nhat, local_hash, remote_hash, message, danh_sach_thay_doi }
    """
    if getattr(sys, "frozen", False):
        return {"co_cap_nhat": False,
                "message": "App đang chạy dạng .exe — không hỗ trợ tự cập nhật.\nHãy liên hệ developer để nhận phiên bản mới."}

    ok, _ = _git(["fetch", "origin"], PROJECT_DIR)
    if not ok:
        # Thử không có remote (project local)
        return {"co_cap_nhat": False, "message": "Không tìm thấy remote Git. Đảm bảo project có kết nối Git."}

    _, local  = _git(["rev-parse", "HEAD"], PROJECT_DIR)
    _, remote = _git(["rev-parse", "origin/HEAD"], PROJECT_DIR)

    if not local or not remote:
        _, remote = _git(["rev-parse", "origin/main"], PROJECT_DIR)
    if not local or not remote:
        _, remote = _git(["rev-parse", "origin/master"], PROJECT_DIR)

    if local == remote:
        return {"co_cap_nhat": False,
                "local_hash": local[:7],
                "remote_hash": remote[:7],
                "message": f"✅ Bạn đang dùng phiên bản mới nhất! (#{local[:7]})"}

    # Có thay đổi — lấy danh sách file thay đổi
    _, diff_log = _git(["log", f"HEAD..origin/HEAD", "--oneline"], PROJECT_DIR)
    if not diff_log:
        _, diff_log = _git(["log", f"HEAD..origin/main", "--oneline"], PROJECT_DIR)

    return {
        "co_cap_nhat": True,
        "local_hash":  local[:7],
        "remote_hash": remote[:7],
        "message": f"🔔 Có bản cập nhật mới! (#{local[:7]} → #{remote[:7]})",
        "danh_sach": diff_log or "(không có thông tin chi tiết)"
    }

@eel.expose
def thuc_hien_cap_nhat() -> dict:
    """Chạy git pull và restart app."""
    if getattr(sys, "frozen", False):
        return {"ok": False, "message": "Không hỗ trợ tự cập nhật trên .exe."}

    ok, out = _git(["pull", "--rebase", "origin"], PROJECT_DIR)
    if not ok:
        return {"ok": False, "message": f"❌ Git pull thất bại:\n{out}"}

    # Restart app sau 1.5 giây
    def _restart():
        time.sleep(1.5)
        os.execv(sys.executable, [sys.executable] + sys.argv)

    threading.Thread(target=_restart, daemon=True).start()
    return {"ok": True, "message": f"✅ Cập nhật thành công!\n{out}\n\n⏳ App đang khởi động lại..."}

# ════════════════════════════════════════════════════════════════════════════════
# SYSTEM
# ════════════════════════════════════════════════════════════════════════════════

@eel.expose
def close_win(): sys.exit(0)

# ════════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════════

def main():
    print("🚀 Cỗ Máy SEO Auto 100% — Desktop App đang khởi động...")
    opts = dict(size=(1280, 800), position=(80, 40), block=True)
    try:
        eel.start("index.html", mode="chrome", **opts)
    except EnvironmentError:
        try:
            eel.start("index.html", mode="edge", **opts)
        except EnvironmentError:
            eel.start("index.html", mode="default", **opts)

if __name__ == "__main__":
    main()
