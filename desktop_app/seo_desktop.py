"""
seo_desktop.py — Desktop App "Cỗ Máy SEO Auto 100%"
Eel backend — bọc toàn bộ tính năng từ Bot_SEO/app.py
"""

import eel, os, sys, json, re, random, threading, base64, time, subprocess
from datetime import datetime

# ── Đường dẫn ─────────────────────────────────────────────────────────────────
def _find_git_root(start_path: str, max_levels: int = 6) -> str | None:
    """Tìm thư mục gốc có .git bằng cách đi lên từ start_path."""
    path = os.path.abspath(start_path)
    for _ in range(max_levels):
        if os.path.isdir(os.path.join(path, ".git")):
            return path
        parent = os.path.dirname(path)
        if parent == path:
            break
        path = parent
    return None

if getattr(sys, "frozen", False):
    BUNDLE_DIR  = sys._MEIPASS
    # Tìm thư mục git thực từ vị trí file .exe (để git pull hoạt động)
    _exe_dir    = os.path.dirname(sys.executable)
    GIT_ROOT    = _find_git_root(_exe_dir)
    # Nếu tìm thấy git root → dùng làm PROJECT_DIR để code Python cập nhật ngay sau git pull
    PROJECT_DIR = GIT_ROOT if GIT_ROOT else BUNDLE_DIR
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(PROJECT_DIR, "vertex-key.json")
else:
    BUNDLE_DIR  = os.path.dirname(os.path.abspath(__file__))
    PROJECT_DIR = os.path.dirname(BUNDLE_DIR)
    GIT_ROOT    = _find_git_root(PROJECT_DIR)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(PROJECT_DIR, "vertex-key.json")

# WEB_DIR: ưu tiên load từ git source để git pull cập nhật UI ngay lập tức
# Nếu không tìm thấy git root (ví dụ chạy trên máy khác không có source) → dùng bundle
_web_from_git = os.path.join(GIT_ROOT, "desktop_app", "web") if GIT_ROOT else None
if _web_from_git and os.path.isdir(_web_from_git):
    WEB_DIR = _web_from_git
else:
    WEB_DIR = os.path.join(BUNDLE_DIR, "web")

STOP_FILE   = os.path.join(PROJECT_DIR, "stop_auto.txt")   # tuyệt đối, tránh lỗi CWD

# Khi chạy .exe: thêm site-packages THẬT của Python để tránh lỗi
# "No module named 'chromadb.api.rust'" và các Rust/C extension bị thiếu trong bundle
if getattr(sys, "frozen", False):
    import shutil as _shutil
    _python = _shutil.which("python") or _shutil.which("python3")
    if _python:
        _pydir = os.path.dirname(os.path.abspath(_python))
        # Thử cả python_dir/Lib/site-packages và parent/Lib/site-packages
        _candidates = [
            os.path.join(_pydir, "Lib", "site-packages"),
            os.path.join(os.path.dirname(_pydir), "Lib", "site-packages"),
        ]
        for _sp in _candidates:
            if os.path.isdir(_sp) and _sp not in sys.path:
                sys.path.insert(1, _sp)
                break

# Custom modules (my_modules.py, module_kho_du_lieu.py...) ưu tiên từ git source
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

_ORIGINAL_TAO_PROMPT_ANH = mm.tao_prompt_anh_software_interface

def _tao_prompt_anh_co_rag(tk_chinh, noi_dung=""):
    """Desktop-only: bổ sung ngữ cảnh RAG vào prompt ảnh, không sửa module_images.py."""
    nd = str(noi_dung or "")
    try:
        import module_kho_du_lieu

        truy_van = f"{tk_chinh} {nd[:500]}".strip()
        tai_lieu_rag = module_kho_du_lieu.tim_kiem_tai_lieu(truy_van)
        if tai_lieu_rag:
            nd = (
                f"{nd}\n\n"
                "[RAG CONTEXT FOR IMAGE PROMPT - summarize visually, do not draw text]:\n"
                f"{str(tai_lieu_rag)[:1800]}"
            )
    except Exception as e:
        print(f"[IMAGE-RAG] Skip RAG for image prompt: {e}", flush=True)

    return _ORIGINAL_TAO_PROMPT_ANH(tk_chinh, nd)

# my_modules.py đã import trực tiếp hàm từ module_images; thay global trong my_modules
# để chỉ desktop app dùng RAG khi tạo prompt ảnh.
mm.tao_prompt_anh_software_interface = _tao_prompt_anh_co_rag

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
        # Merge với config hiện có để không mất blocks_list v.v. khi sidebar save
        existing = tai_cau_hinh()
        existing.update(cfg)
        with open(UI_FILE, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
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
            # Frontend lưu: "publish" | "draft" | "future"
            st_cfg = cfg.get("trang_thai", "publish")
            if st_cfg == "future":      trang_thai_wp = "scheduled"
            elif st_cfg == "draft":     trang_thai_wp = "draft"
            else:                       trang_thai_wp = "publish_now"
            _push_log("log_tab2", f"📋 Trạng thái WP: {trang_thai_wp} (raw='{st_cfg}')")

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

            # Xoá stop cũ (nếu có) trước khi bắt đầu
            if os.path.exists(STOP_FILE):
                os.remove(STOP_FILE)

            dem = 0
            for idx, row in hang_doi.iterrows():
                if os.path.exists(STOP_FILE):
                    os.remove(STOP_FILE)
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

                class _StopNow(Exception):
                    pass

                def cb(msg, _tk=tk):
                    # Kiểm tra lệnh dừng ngay trong callback — được gọi hàng trăm lần
                    if os.path.exists(STOP_FILE):
                        raise _StopNow("Dừng khẩn cấp")
                    _push_log("log_tab2", str(msg))

                # ── GỌI PIPELINE ĐẦY ĐỦ ────────────────────────────────────
                try:
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
                except _StopNow:
                    if os.path.exists(STOP_FILE):
                        os.remove(STOP_FILE)
                    try: ws.update_cell(row_sheet, col_tt, "⏸ Đã dừng")
                    except Exception: pass
                    _push_log("log_tab2", "🛑 Dừng khẩn cấp — bài đang viết bị huỷ!")
                    break
                except Exception as _ep:
                    thanh_cong, msg_tt, link_bai = False, str(_ep), ""

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
                              f"☕ Nghỉ {sleep_s//60}p{sleep_s%60}s trước bài tiếp... (Nhấn Dừng để bỏ qua)")
                    # Sleep interruptible: kiểm tra stop file mỗi 10 giây
                    for _ in range(sleep_s // 10):
                        if os.path.exists(STOP_FILE):
                            os.remove(STOP_FILE)
                            _push_log("log_tab2", "🛑 Nhận lệnh dừng trong lúc nghỉ!")
                            dem = len(hang_doi)  # force exit outer loop
                            break
                        time.sleep(10)
                    if dem >= len(hang_doi):
                        break

            _push_log("log_tab2", f"\n🎉 Hoàn tất! Đã viết {dem}/{len(hang_doi)} bài")
            eel.tab2_done()()

        except Exception as e:
            import traceback
            _push_log("log_tab2", f"❌ Lỗi hệ thống: {e}\n{traceback.format_exc()[-300:]}")

    threading.Thread(target=_worker, daemon=True).start()
    return {"ok": True, "msg": "🚀 Đã khởi động cỗ máy — xem Nhật Ký bên dưới!"}

@eel.expose
def dung_auto():
    """Tạo file stop để dừng vòng lặp auto ngay lập tức."""
    try:
        with open(STOP_FILE, "w") as f:
            f.write("stop")
        return {"ok": True, "msg": "🛑 Đã gửi lệnh dừng — đang dừng sau bước hiện tại!"}
    except Exception as e:
        return {"ok": False, "msg": str(e)}

@eel.expose
def loc_y_dinh_tu_khoa(gs_url: str, tab_name: str = "Tukhoa") -> dict:
    """Quét & lọc từ khoá trùng lặp ý định tìm kiếm bằng Gemini Flash."""
    try:
        import gspread, pandas as pd
        gc = gspread.service_account(filename=GOOGLE_KEY_PATH)
        sh = gc.open_by_url(gs_url)
        ws = sh.worksheet(tab_name)
        data = ws.get_all_records()
        df = pd.DataFrame(data)

        if df.empty or "Trạng thái" not in df.columns or "Từ khóa" not in df.columns:
            return {"ok": False, "msg": "Sheet trống hoặc thiếu cột 'Trạng thái'/'Từ khóa'"}

        cols = df.columns.tolist()
        col_tt = cols.index("Trạng thái") + 1

        list_tk = df[df["Trạng thái"].astype(str).str.strip() == ""]["Từ khóa"].tolist()
        if not list_tk:
            return {"ok": True, "loai_bo": 0, "msg": "Không có từ khoá nào đang chờ xử lý."}

        prompt_loc = (
            "Bạn là chuyên gia SEO. Dưới đây là danh sách từ khóa.\n"
            "Nhiệm vụ: Phân tích Ý định tìm kiếm (Search Intent). Nếu có các từ khóa "
            "khác chữ nhưng mang cùng 1 ý định tìm kiếm, hãy chọn 1 từ hay nhất để "
            "giữ lại, và LOẠI BỎ từ còn lại.\n"
            "TRẢ VỀ DUY NHẤT danh sách các từ khóa CẦN BỊ LOẠI BỎ, mỗi từ khóa cách "
            "nhau bởi dấu |. Nếu không có từ nào bị trùng, trả về KHONG_CO.\n"
            f"Danh sách: {list_tk}"
        )

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
                if str(row.get("Từ khóa", "")).strip() in tu_khoa_loai_bo:
                    row_sheet = idx + 2
                    try:
                        ws.update_cell(row_sheet, col_tt, "Trùng lặp ý định (Bỏ qua)")
                    except Exception:
                        pass
                    count_loai += 1

        return {
            "ok": True,
            "loai_bo": count_loai,
            "msg": f"✅ Đã quét xong! Loại bỏ {count_loai} từ khoá trùng lặp ý định."
        }
    except Exception as e:
        return {"ok": False, "msg": str(e)}


_DEFAULT_BLOCKS = [
    {"name": "🧑‍💻 Tác giả bài viết",    "code": '[block id="tac-gia-bai-viet"]'},
    {"name": "🤠 Tác giả Bình Dương",    "code": '[block id="tac-gia-binh-duong"]'},
    {"name": "📞 TT liên hệ ngoài BD",   "code": '[block id="thong-tin-lien-he-ngoai-bd"]'},
    {"name": "❌ Không chèn Block nào",   "code": ""},
]

@eel.expose
def lay_danh_sach_blocks() -> list:
    """Trả về danh sách author blocks [{name, code}] từ ui_settings.json.
    Nếu chưa có → trả về danh sách mặc định giống Streamlit app."""
    try:
        cfg = tai_cau_hinh()
        blocks = cfg.get("blocks_list", [])
        if blocks:
            return blocks
        # Lần đầu chưa có → lưu mặc định và trả về
        cfg["blocks_list"] = _DEFAULT_BLOCKS
        luu_cau_hinh(cfg)
        return _DEFAULT_BLOCKS
    except Exception:
        return _DEFAULT_BLOCKS

@eel.expose
def luu_block_moi(name: str, code: str) -> dict:
    """Lưu một block mới vào danh sách."""
    try:
        cfg = tai_cau_hinh()
        blocks = cfg.get("blocks_list", [])
        # Cập nhật nếu trùng tên, thêm mới nếu chưa có
        for b in blocks:
            if b.get("name") == name:
                b["code"] = code
                break
        else:
            blocks.append({"name": name, "code": code})
        cfg["blocks_list"] = blocks
        luu_cau_hinh(cfg)
        return {"ok": True, "blocks": blocks}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@eel.expose
def xoa_block(name: str) -> dict:
    """Xoá một block theo tên."""
    try:
        cfg = tai_cau_hinh()
        blocks = [b for b in cfg.get("blocks_list", []) if b.get("name") != name]
        cfg["blocks_list"] = blocks
        luu_cau_hinh(cfg)
        return {"ok": True, "blocks": blocks}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@eel.expose
def them_fb_page(name: str, page_id: str, access_token: str) -> dict:
    """Thêm hoặc cập nhật một Facebook Page."""
    try:
        pages = lay_fb_pages()
        for p in pages:
            if p.get("page_id") == page_id:
                p["name"] = name
                p["access_token"] = access_token
                luu_fb_pages(pages)
                return {"ok": True, "pages": pages}
        pages.append({"name": name, "page_id": page_id, "access_token": access_token})
        luu_fb_pages(pages)
        return {"ok": True, "pages": pages}
    except Exception as e:
        return {"ok": False, "error": str(e)}

@eel.expose
def xoa_fb_page(page_id: str) -> dict:
    """Xoá một Facebook Page theo page_id."""
    try:
        pages = [p for p in lay_fb_pages() if p.get("page_id") != page_id]
        luu_fb_pages(pages)
        return {"ok": True, "pages": pages}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@eel.expose
def dang_bai_thu_cong_full(tu_khoa: str, tieu_de: str, outline: str,
                             cfg_dang: dict) -> dict:
    """Đăng bài đầy đủ: RAG + Search + Ảnh + WordPress + Zalo + Facebook."""
    tu_khoa = tu_khoa.strip()
    if not tu_khoa:
        return {"ok": False, "link": "", "msg": "Thiếu từ khoá!"}

    def _worker():
        try:
            from my_modules import (quy_trinh_dang_bai_full,
                                    reset_dem_so_bai)

            def cb(msg): _push_log("log_tab1", msg)

            cfg = tai_cau_hinh()

            # Resolve category / tag IDs
            danh_sach_dm_id = []
            danh_sach_the_id = []
            try:
                dm_val = cfg_dang.get("dm_id") or cfg.get("danh_muc", "")
                if dm_val:
                    cats = lay_wp_categories()
                    danh_sach_dm_id = [
                        c["id"] for c in cats
                        if str(c.get("id")) == str(dm_val) or c.get("name") == dm_val
                    ]
            except Exception: pass
            try:
                tag_val = cfg_dang.get("tag_id") or cfg.get("tag", "")
                if tag_val:
                    tags = lay_wp_tags()
                    danh_sach_the_id = [
                        t["id"] for t in tags
                        if str(t.get("id")) == str(tag_val)
                    ]
            except Exception: pass

            trang_thai_wp = cfg_dang.get("trang_thai") or cfg.get("trang_thai", "publish")

            author_block_code  = cfg_dang.get("author_block_code") or cfg.get("author_block_code", "")
            flatsome_shortcode = cfg_dang.get("flatsome_shortcode") or cfg.get("flatsome_shortcode", "")

            cho_phep_web   = bool(cfg_dang.get("cho_phep_web",  True))
            cho_phep_zalo  = bool(cfg_dang.get("cho_phep_zalo", False))
            cho_phep_fb    = bool(cfg_dang.get("cho_phep_fb",   False))

            anchor1    = cfg_dang.get("anchor1")    or cfg.get("anchor1", "")
            url1       = cfg_dang.get("url1")       or cfg.get("url1", "")
            anchor2    = cfg_dang.get("anchor2")    or cfg.get("anchor2", "")
            url2       = cfg_dang.get("url2")       or cfg.get("url2", "")
            anchor_out = cfg_dang.get("anchor_out", "")
            url_out    = cfg_dang.get("url_out",    "")

            # Xây kho link từ sidebar
            kho_link_list = []
            if anchor1 and url1:
                kho_link_list.append({"row": 1, "anchor": anchor1, "url": url1})
            if anchor2 and url2:
                kho_link_list.append({"row": 2, "anchor": anchor2, "url": url2})
            if anchor_out and url_out:
                kho_link_list.append({"row": 3, "anchor": anchor_out, "url": url_out})

            reset_dem_so_bai()
            cb(f"🚀 Bắt đầu đăng bài đầy đủ: «{tu_khoa}»...")

            thanh_cong, msg_tt, link_bai = quy_trinh_dang_bai_full(
                tk_auto               = tu_khoa,
                tieu_de_excel         = tieu_de,
                danh_sach_api_keys    = [],
                kho_link_list         = kho_link_list,
                ws_kho                = None,
                author_block_code     = author_block_code,
                flatsome_shortcode    = flatsome_shortcode,
                danh_sach_dm_id_auto  = danh_sach_dm_id,
                danh_sach_the_id_auto = danh_sach_the_id,
                trang_thai_wp         = trang_thai_wp,
                cap_nhat_trang_thai_func = cb,
                cho_phep_zalo         = cho_phep_zalo,
                cho_phep_facebook     = cho_phep_fb,
                cho_phep_web          = cho_phep_web,
            )

            if thanh_cong:
                cb(f"✅ Xong! Link bài: {link_bai}")
                eel.tab1_full_done(True, link_bai, msg_tt)()
            else:
                cb(f"❌ Lỗi: {msg_tt}")
                eel.tab1_full_done(False, "", msg_tt)()

        except Exception as e:
            import traceback
            err = f"❌ Lỗi hệ thống: {e}\n{traceback.format_exc()[-400:]}"
            _push_log("log_tab1", err)
            try: eel.tab1_full_done(False, "", str(e))()
            except Exception: pass

    threading.Thread(target=_worker, daemon=True).start()
    return {"ok": True, "msg": "🚀 Đã khởi động pipeline đầy đủ — xem log bên dưới!"}


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
def xem_kho_rag(limit: int = 10) -> dict:
    """Trả về thống kê + mẫu nội dung kho RAG."""
    try:
        import module_kho_du_lieu as _mkdl
        kp = _mkdl.THU_MUC_KHO   # dùng đường dẫn tuyệt đối từ module
        cli = chromadb.PersistentClient(path=kp)
        try:
            col = cli.get_collection("tai_lieu_seo")
        except Exception:
            return {"so_doan": 0, "so_file": 0, "mau": [], "loi": ""}

        so_doan = col.count()
        # Lấy danh sách nguồn gốc
        meta_all = col.get(include=["metadatas"], limit=99999)
        nguon_set = set(m.get("nguon_goc","?") for m in (meta_all.get("metadatas") or []) if m)

        # Lấy mẫu
        mau = []
        if so_doan > 0:
            peek = col.peek(limit=limit)
            for doc, meta in zip(peek.get("documents",[]), peek.get("metadatas",[])):
                mau.append({"nguon": meta.get("nguon_goc","?"), "doan": doc[:300]})

        return {
            "so_doan": so_doan,
            "so_file": len(nguon_set),
            "danh_sach_file": sorted(nguon_set),
            "mau": mau,
            "loi": ""
        }
    except Exception as e:
        return {"so_doan": 0, "so_file": 0, "mau": [], "loi": str(e)}

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
    Hoạt động cả khi chạy .py lẫn .exe (tìm git root từ vị trí exe).
    """
    repo = GIT_ROOT
    if not repo:
        return {"co_cap_nhat": False,
                "message": "Không tìm thấy thư mục Git.\nĐảm bảo app được cài trong thư mục có .git."}

    ok, err = _git(["fetch", "origin"], repo)
    if not ok:
        return {"co_cap_nhat": False,
                "message": f"Không kết nối được Git remote:\n{err}"}

    _, local = _git(["rev-parse", "HEAD"], repo)

    # Thử lần lượt origin/HEAD → origin/master → origin/main
    remote = ""
    for ref in ["origin/HEAD", "origin/master", "origin/main"]:
        ok2, remote = _git(["rev-parse", ref], repo)
        if ok2 and remote:
            break

    if not local or not remote:
        return {"co_cap_nhat": False, "message": "Không đọc được hash commit."}

    if local.strip() == remote.strip():
        return {"co_cap_nhat": False,
                "local_hash": local[:7],
                "remote_hash": remote[:7],
                "message": f"✅ Phiên bản mới nhất! (#{local[:7]})"}

    # Có bản mới — lấy danh sách commit
    diff_log = ""
    for ref in ["origin/HEAD", "origin/master", "origin/main"]:
        _, diff_log = _git(["log", f"HEAD..{ref}", "--oneline"], repo)
        if diff_log:
            break

    return {
        "co_cap_nhat": True,
        "local_hash":  local[:7],
        "remote_hash": remote[:7],
        "message": f"🔔 Có bản cập nhật! (#{local[:7]} → #{remote[:7]})",
        "danh_sach": diff_log or "(không có thông tin chi tiết)"
    }

@eel.expose
def thuc_hien_cap_nhat() -> dict:
    """Chạy git pull rồi restart app (hoạt động cả .py lẫn .exe)."""
    repo = GIT_ROOT
    if not repo:
        return {"ok": False, "message": "Không tìm thấy thư mục Git để cập nhật."}

    # Thử pull với các nhánh phổ biến
    ok, out = _git(["pull", "--rebase", "origin"], repo)
    if not ok:
        # Thử không --rebase
        ok, out = _git(["pull", "origin"], repo)
    if not ok:
        return {"ok": False, "message": f"❌ Git pull thất bại:\n{out}"}

    def _restart():
        time.sleep(2)
        try:
            if getattr(sys, "frozen", False):
                # Chạy lại file .exe
                subprocess.Popen([sys.executable] + sys.argv)
            else:
                os.execv(sys.executable, [sys.executable] + sys.argv)
        except Exception:
            pass
        sys.exit(0)

    threading.Thread(target=_restart, daemon=True).start()
    return {"ok": True, "message": f"✅ Cập nhật thành công!\n{out}\n\n⏳ App đang khởi động lại..."}

# ════════════════════════════════════════════════════════════════════════════════
# ════════════════════════════════════════════════════════════════════════════════
# PHIÊN BẢN
# ════════════════════════════════════════════════════════════════════════════════

@eel.expose
def lay_phien_ban() -> dict:
    """Trả về phiên bản hiện tại từ git log (commit date + hash ngắn)."""
    repo = GIT_ROOT or PROJECT_DIR
    try:
        # Lấy: "2026-05-03 22:10 #e1fe30c"
        ok, out = _git(["log", "-1", "--format=%cd %h", "--date=format:%Y-%m-%d %H:%M"], repo)
        if ok and out:
            parts = out.strip().split()
            date  = parts[0] if len(parts) >= 1 else "?"
            hhmm  = parts[1] if len(parts) >= 2 else ""
            hsh   = parts[2] if len(parts) >= 3 else ""
            label = f"v{date.replace('-','.')}  #{hsh}"
            return {"ok": True, "label": label, "date": date, "time": hhmm, "hash": hsh}
    except Exception:
        pass
    return {"ok": False, "label": "v?.?.?", "date": "", "time": "", "hash": ""}

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
