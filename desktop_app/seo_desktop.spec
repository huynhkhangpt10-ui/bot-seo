# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file cho "Phần Mềm Auto SEO"
# Build: pyinstaller seo_desktop.spec

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# ── Thư mục gốc của project ──────────────────────────────────────────────────
SPEC_DIR    = os.path.dirname(os.path.abspath(SPEC))   # desktop_app/
PROJECT_DIR = os.path.dirname(SPEC_DIR)                # Bot_SEO/

# ── File & thư mục cần đưa vào bundle ────────────────────────────────────────
added_datas = [
    # Giao diện web
    (os.path.join(SPEC_DIR, "web"), "web"),

    # Credentials Vertex AI
    (os.path.join(PROJECT_DIR, "vertex-key.json"), "."),

    # Module Python từ project chính (copy vào root của bundle)
    (os.path.join(PROJECT_DIR, "my_config.py"),          "."),
    (os.path.join(PROJECT_DIR, "module_content.py"),     "."),
    (os.path.join(PROJECT_DIR, "module_prompts.py"),     "."),
    (os.path.join(PROJECT_DIR, "module_scenarios.py"),   "."),
    (os.path.join(PROJECT_DIR, "my_modules.py"),         "."),
    (os.path.join(PROJECT_DIR, "nap_tai_lieu.py"),       "."),
    (os.path.join(PROJECT_DIR, "module_kho_du_lieu.py"), "."),
    (os.path.join(PROJECT_DIR, "seo_doctor.py"),         "."),
    (os.path.join(PROJECT_DIR, "satellite_worker.py"),   "."),
    (os.path.join(PROJECT_DIR, "master_api.py"),         "."),
    (os.path.join(PROJECT_DIR, "module_images.py"),      "."),
]

# Thêm logo nếu tồn tại
_logo = os.path.join(PROJECT_DIR, "logo_hk.png")
if os.path.exists(_logo):
    added_datas.append((_logo, "."))

# Thêm Playwright browsers nếu cần
_pw = os.path.join(PROJECT_DIR, "Playwright_Browsers")
if os.path.exists(_pw):
    added_datas.append((_pw, "Playwright_Browsers"))

# ── Hidden imports cần thiết ──────────────────────────────────────────────────
hidden = [
    # Eel & web server
    "eel", "bottle", "bottle_websocket",
    "gevent", "gevent.socket", "gevent.monkey", "gevent.event",
    "geventwebsocket", "geventwebsocket.handler",
    # Google Vertex AI / Auth
    "google.genai", "google.genai.types",
    "google.auth", "google.auth.transport", "google.oauth2",
    "google.api_core", "google.auth.credentials",
    # Sheets / GSC
    "gspread", "googleapiclient", "googleapiclient.discovery",
    "google_auth_oauthlib",
    # ChromaDB / RAG
    "chromadb", "chromadb.api", "chromadb.config",
    "fitz",  # PyMuPDF
    # Playwright
    "playwright", "playwright.sync_api",
    # Requests / HTTP
    "requests", "urllib3", "certifi",
    # Tumblr
    "pytumblr",
    # Hỗ trợ
    "importlib_resources", "pyparsing", "bs4", "lxml",
    "PIL", "PIL.Image",
]

a = Analysis(
    [os.path.join(SPEC_DIR, "seo_desktop.py")],
    pathex=[SPEC_DIR, PROJECT_DIR],
    binaries=[],
    datas=added_datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["streamlit", "matplotlib", "cv2"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AutoSEO",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # Không hiện cửa sổ cmd đen
    icon=os.path.join(SPEC_DIR, "icon.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="AutoSEO",
)
