#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
google_stack_builder.py  —  v3 (site_map.json driven)
======================================================
Đọc dữ liệu từ site_map.json (đã crawl 373 URL), phân loại tự động,
rồi tạo toàn bộ Google Authority Stack:
  Drive Folder → Google Doc (anchor-text links) → Google Sheets (3 tab)
  → KML Map (local SEO) → entity_links.txt

YÊU CẦU:
  pip install google-api-python-client google-auth-oauthlib requests beautifulsoup4
  credentials.json = OAuth 2.0 Desktop App (từ Google Cloud Console)
"""

import os, sys, re, json, pickle, unicodedata, html as _html
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload
from google.oauth2 import service_account
from google.auth.transport.requests import Request

sys.stdout.reconfigure(encoding="utf-8")

# ============================================================
# 1. NAP — Thông tin doanh nghiệp
# ============================================================
NAP = {
    "brand":    "Dịch Vụ Tận Nơi Huỳnh Khang",
    "short":    "Huỳnh Khang Computer",
    "website":  "https://huynhkhang.com",
    "phone":    "+84325636239",
    "phone_d":  "0325.636.239",
    "email":    "huynhkhang112016@gmail.com",
    "address":  "475/B DT 747, Tổ 2, KP3, Tân Uyên, Bình Dương 820000",
    "city":     "Tân Uyên, Bình Dương",
    "lat":      11.0131,
    "lng":      106.9658,
    "facebook": "https://www.facebook.com/huynhkhangcomputer1/",
    "hours":    "Thứ 2 – Thứ 7, 08:00 – 17:00",
}

AREAS = [
    "Tân Uyên, Bình Dương", "Hội Nghĩa, Bình Dương", "Uyên Hưng, Bình Dương",
    "Thị Xã Bến Cát, Bình Dương", "Dĩ An, Bình Dương", "Thuận An, Bình Dương",
    "TP Thủ Dầu Một, Bình Dương",
    "Quận 1, TP.HCM", "Quận 3, TP.HCM", "Quận 4, TP.HCM", "Quận 5, TP.HCM",
    "Quận 6, TP.HCM", "Quận 7, TP.HCM", "Quận 8, TP.HCM", "Quận 10, TP.HCM",
    "Quận 11, TP.HCM", "Quận 12, TP.HCM", "TP Thủ Đức, TP.HCM",
    "Bình Thạnh, TP.HCM", "Bình Tân, TP.HCM", "Gò Vấp, TP.HCM",
    "Phú Nhuận, TP.HCM", "Tân Bình, TP.HCM", "Tân Phú, TP.HCM",
    "Huyện Bình Chánh, TP.HCM", "Huyện Củ Chi, TP.HCM",
    "Huyện Hóc Môn, TP.HCM", "Huyện Nhà Bè, TP.HCM",
]

# ============================================================
# 2. LOAD & CATEGORIZE site_map.json
# ============================================================
SITE_MAP_FILE = os.path.join(os.path.dirname(__file__), "site_map.json")

# URL slugs bị 404 — loại hoàn toàn
_BAD_SLUGS = {
    "sua-may-lanh", "ve-sinh-may-giat", "ve-sinh-may-lanh",
    "sua-tu-lanh",  "sua-may-nuoc-nong", "sua-may-giat",
    "payment-success", "gio-hang", "thanh-toan", "test-trang-chu",
}

# Regex nhận diện bài đánh giá phiên bản phần mềm (Tin tức)
_VER_RE = re.compile(
    r"(bridge|revit|indesign|premiere|autocad|photoshop|illustrator|"
    r"3ds-max|fusion-360|maya|word|excel|powerpoint|lightroom|"
    r"after-effect|coreldraw|sketchup|solidworks)-20\d\d",
    re.IGNORECASE,
)

# Slugs dịch vụ hợp lệ
_SVC_SLUGS = {
    "sua-may-tinh", "sua-laptop", "sua-may-in", "nap-muc-may-in",
    "ve-sinh-may-tinh", "ve-sinh-laptop", "cai-win",
    "ban-quyen", "phan-mem",
}


def _slug_parts(url: str):
    """Trả về tuple (cat_slug, post_slug) từ full URL."""
    path = url.replace("https://huynhkhang.com/", "").strip("/")
    parts = path.split("/")
    return parts[0] if parts else "", parts[1] if len(parts) > 1 else ""


def load_site_data():
    """Đọc site_map.json và phân loại thành 3 nhóm."""
    if not os.path.exists(SITE_MAP_FILE):
        print(f"⚠️  Thiếu {SITE_MAP_FILE}. Chạy crawler trước.")
        raise SystemExit(1)

    with open(SITE_MAP_FILE, encoding="utf-8") as f:
        raw = json.load(f)

    dich_vu, thu_thuat, tin_tuc = [], [], []

    for url, info in raw.items():
        title = info.get("title", "").strip()
        typ   = info.get("type", "")

        # Bỏ qua tiêu đề rỗng / lỗi
        if not title or title in ("(no title)", "(err)"):
            continue

        cat_slug, post_slug = _slug_parts(url)

        # Bỏ qua category / post 404
        if cat_slug in _BAD_SLUGS or post_slug in _BAD_SLUGS:
            continue
        if any(b in url for b in _BAD_SLUGS):
            continue

        entry = {"url": url, "title": _html.unescape(title), "type": typ}

        if typ in ("page", "category"):
            dich_vu.append(entry)
        elif cat_slug in _SVC_SLUGS:
            # Bài dịch vụ theo khu vực
            dich_vu.append(entry)
        elif cat_slug == "tin-tuc":
            # Phân biệt review phiên bản vs thủ thuật
            if _VER_RE.search(post_slug):
                tin_tuc.append(entry)
            else:
                thu_thuat.append(entry)
        else:
            thu_thuat.append(entry)

    print(f"   📊 Đã phân loại: Dịch vụ={len(dich_vu)} | "
          f"Thủ thuật={len(thu_thuat)} | Tin tức={len(tin_tuc)}")
    return dich_vu, thu_thuat, tin_tuc


# ============================================================
# 3. AUTHENTICATION
# ============================================================
ROOT_FOLDER_ID = "1qN2mnkGBsX0Nsaf-iKN94dV4BFp7zb4f"

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets",
]
CREDS_FILE = "credentials.json"
TOKEN_FILE = "stack_token.pickle"


def get_credentials():
    if not os.path.exists(CREDS_FILE):
        print(f"❌ Thiếu {CREDS_FILE}.")
        raise SystemExit(1)
    with open(CREDS_FILE, encoding="utf-8") as f:
        info = json.load(f)
    if info.get("type") == "service_account":
        print(f"   🔑 Service Account: {info.get('client_email','?')}")
        return service_account.Credentials.from_service_account_file(
            CREDS_FILE, scopes=SCOPES)
    print("   🔑 OAuth2 Desktop App...")
    from google_auth_oauthlib.flow import InstalledAppFlow
    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)
    return creds


def build_services(creds):
    drive  = build("drive",  "v3", credentials=creds)
    docs   = build("docs",   "v1", credentials=creds)
    sheets = build("sheets", "v4", credentials=creds)
    return drive, docs, sheets


# ============================================================
# 4. HELPERS
# ============================================================
def _nfc(t): return unicodedata.normalize("NFC", t)

def set_public_permission(drive_svc, file_id):
    drive_svc.permissions().create(
        fileId=file_id,
        body={"type": "anyone", "role": "reader"},
        fields="id",
    ).execute()


def _move_to_folder(drive_svc, file_id, folder_id):
    meta = drive_svc.files().get(fileId=file_id, fields="parents").execute()
    drive_svc.files().update(
        fileId=file_id,
        addParents=folder_id,
        removeParents=",".join(meta.get("parents", [])),
        fields="id,parents",
    ).execute()


# ============================================================
# 5. GOOGLE DOC — Profile chuyên gia với anchor-text links
# ============================================================
def _link(url, title):
    """Tạo thẻ <a> với anchor text là tiêu đề bài viết."""
    safe = _nfc(title).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f'<a href="{url}">{safe}</a>'


def _list_items(items, limit=18):
    """Tạo <ul><li> với anchor text link cho mỗi bài."""
    li = "\n".join(
        f"    <li>{_link(x['url'], x['title'])}</li>"
        for x in items[:limit]
    )
    return f"<ul>\n{li}\n</ul>"


def build_doc_html(dich_vu, thu_thuat, tin_tuc):
    n   = NAP
    yr  = datetime.now().year

    # Chọn bài dịch vụ theo khu vực (có "tai-nha" hoặc "quan-" trong URL)
    svc_posts = [x for x in dich_vu if x["type"] == "post"]
    svc_cats  = [x for x in dich_vu if x["type"] in ("category", "page")]

    # Local posts cho SEO địa phương
    local_posts = [x for x in svc_posts if
                   any(kw in x["url"] for kw in
                       ["tai-nha", "thuan-an", "tan-uyen", "di-an",
                        "thu-dau-mot", "quan-1", "quan-7", "tp-hcm", "tphcm"])]

    areas_str = ", ".join(AREAS)

    parts = [
        "<!DOCTYPE html>",
        "<html><head><meta charset='UTF-8'></head><body>",

        # ── TIÊU ĐỀ ──────────────────────────────────────────
        f"<h1>{_nfc(n['brand'])} – Chuyên Gia IT Tận Nơi Bình Dương &amp; TP.HCM</h1>",

        # ── GIỚI THIỆU ───────────────────────────────────────
        "<h2>Giới Thiệu</h2>",
        f"<p>{_nfc(n['brand'])} là đơn vị kỹ thuật máy tính uy tín tại {n['city']} "
        f"với hơn 15 năm kinh nghiệm thực chiến. Chúng tôi đã xử lý hơn 5.000 ca sửa máy tính, "
        f"laptop, máy in tận nơi và cài đặt phần mềm bản quyền cho cá nhân, văn phòng, doanh nghiệp.</p>",
        f"<p><strong>Website:</strong> <a href='{n['website']}'>{n['website']}</a><br>",
        f"<strong>Hotline / Zalo:</strong> <a href='tel:{n['phone']}'>{n['phone_d']}</a><br>",
        f"<strong>Email:</strong> {n['email']}<br>",
        f"<strong>Địa chỉ:</strong> {n['address']}<br>",
        f"<strong>Giờ làm việc:</strong> {n['hours']}</p>",

        # ── DỊCH VỤ CHÍNH ────────────────────────────────────
        "<h2>Danh Mục Dịch Vụ</h2>",
        "<p>Các trang dịch vụ chính trên website:</p>",
        _list_items(svc_cats, limit=len(svc_cats)),

        # ── DỊCH VỤ THEO KHU VỰC ─────────────────────────────
        "<h2>Dịch Vụ Sửa Chữa Theo Khu Vực</h2>",
        f"<p>Đội ngũ kỹ thuật viên {n['short']} phục vụ tận nơi tại: {areas_str}.</p>",
        _list_items(local_posts, limit=20),

        # ── THỦ THUẬT ────────────────────────────────────────
        "<h2>Bài Viết Thủ Thuật &amp; Hướng Dẫn</h2>",
        "<p>Các bài viết hướng dẫn, mẹo và khắc phục sự cố máy tính, phần mềm:</p>",
        _list_items(thu_thuat, limit=18),

        # ── TIN TỨC ──────────────────────────────────────────
        "<h2>Tin Tức Công Nghệ &amp; Phần Mềm</h2>",
        "<p>Cập nhật phiên bản mới nhất và tổng quan các phần mềm đồ họa, thiết kế:</p>",
        _list_items(tin_tuc, limit=18),

        # ── KHU VỰC PHỤC VỤ ─────────────────────────────────
        "<h2>Khu Vực Phục Vụ</h2>",
        f"<p>{n['brand']} phục vụ tận nơi toàn bộ Bình Dương và TP.HCM:</p>",
        "<ul>" + "".join(f"<li>{a}</li>" for a in AREAS) + "</ul>",

        # ── BẢNG GIÁ ─────────────────────────────────────────
        "<h2>Bảng Giá Tham Khảo {yr}</h2>".replace("{yr}", str(yr)),
        "<ul>",
        "<li>Cài Windows 10/11: 150.000đ – 250.000đ</li>",
        "<li>Vệ sinh + tra keo tản nhiệt: 150.000đ – 250.000đ</li>",
        "<li>Sửa mainboard laptop không nguồn: 480.000đ – 870.000đ</li>",
        "<li>Nạp mực máy in: 120.000đ – 250.000đ</li>",
        f"<li>Autodesk EDU (AutoCAD, Revit, 3DS Max...): từ 470.000đ/năm</li>",
        f"<li>Adobe Creative Cloud (Full App): ~190.000đ/tháng</li>",
        "<li>Key Windows 10/11 vĩnh viễn: ~350.000đ</li>",
        "</ul>",

        # ── LIÊN HỆ ──────────────────────────────────────────
        f"<h2>Liên Hệ {_nfc(n['brand'])}</h2>",
        f"<p><strong>Địa chỉ:</strong> {n['address']}<br>",
        f"<strong>Hotline / Zalo:</strong> <a href='tel:{n['phone']}'>{n['phone_d']}</a><br>",
        f"<strong>Email:</strong> {n['email']}<br>",
        f"<strong>Website:</strong> <a href='{n['website']}'>{n['website']}</a><br>",
        f"<strong>Facebook:</strong> <a href='{n['facebook']}'>{n['facebook']}</a></p>",

        "</body></html>",
    ]
    return "\n".join(parts)


def create_google_doc(docs_svc, drive_svc, folder_id, dich_vu, thu_thuat, tin_tuc):
    print("\n📄 [BƯỚC 2] Tạo Google Doc (Profile chuyên gia + anchor-text links)...")
    html_content = build_doc_html(dich_vu, thu_thuat, tin_tuc)
    html_bytes   = _nfc(html_content).encode("utf-8")
    media        = MediaInMemoryUpload(html_bytes, mimetype="text/html")

    title     = f"{NAP['brand']} – Chuyên Gia IT Tận Nơi Bình Dương & TP.HCM"
    file_meta = {
        "name":     _nfc(title),
        "mimeType": "application/vnd.google-apps.document",
        "parents":  [folder_id],
    }
    doc     = drive_svc.files().create(
        body=file_meta, media_body=media, fields="id,webViewLink"
    ).execute()
    doc_id  = doc["id"]
    doc_url = doc.get("webViewLink", f"https://docs.google.com/document/d/{doc_id}")
    set_public_permission(drive_svc, doc_id)
    print(f"   ✅ Google Doc: {doc_url}")
    return doc_id, doc_url


# ============================================================
# 6. GOOGLE SHEETS — 3 tab: Dịch vụ | Thủ thuật | Tin tức
# ============================================================
def _sheet_rows(items):
    """Chuyển list entry thành rows cho Sheets."""
    rows = [["STT", "Tiêu Đề Bài Viết", "URL", "Loại"]]
    for i, x in enumerate(items, 1):
        rows.append([i, x["title"], x["url"], x["type"]])
    return rows


def _nap_rows():
    n = NAP
    rows = [["THÔNG TIN", "GIÁ TRỊ"],
            ["Tên thương hiệu",   n["brand"]],
            ["Tên ngắn",          n["short"]],
            ["Địa chỉ (NAP)",     n["address"]],
            ["Điện thoại",        n["phone_d"]],
            ["Email",             n["email"]],
            ["Website",           n["website"]],
            ["Facebook",          n["facebook"]],
            ["Giờ mở cửa",        n["hours"]],
            ["Vĩ độ (Lat)",       str(n["lat"])],
            ["Kinh độ (Lng)",     str(n["lng"])],
            [""],
            ["KHU VỰC PHỤC VỤ",  ""]]
    rows += [[a, ""] for a in AREAS]
    return rows


def create_google_sheets(sheets_svc, drive_svc, folder_id, dich_vu, thu_thuat, tin_tuc):
    print("\n📊 [BƯỚC 3] Tạo Google Sheets (3 tab: Dịch vụ | Thủ thuật | Tin tức)...")
    title = f"Entity Stack – {NAP['short']} – {datetime.now().strftime('%Y-%m-%d')}"

    spreadsheet = sheets_svc.spreadsheets().create(body={
        "properties": {"title": title},
        "sheets": [
            {"properties": {"title": "Dịch vụ"}},
            {"properties": {"title": "Thủ thuật"}},
            {"properties": {"title": "Tin tức"}},
            {"properties": {"title": "Entity NAP"}},
        ],
    }).execute()
    sheet_id  = spreadsheet["spreadsheetId"]
    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"

    _move_to_folder(drive_svc, sheet_id, folder_id)

    # Ghi dữ liệu 4 sheet
    batch_data = [
        {"range": "Dịch vụ!A1",    "values": _sheet_rows(dich_vu)},
        {"range": "Thủ thuật!A1",  "values": _sheet_rows(thu_thuat)},
        {"range": "Tin tức!A1",    "values": _sheet_rows(tin_tuc)},
        {"range": "Entity NAP!A1", "values": _nap_rows()},
    ]
    sheets_svc.spreadsheets().values().batchUpdate(
        spreadsheetId=sheet_id,
        body={"valueInputOption": "RAW", "data": batch_data},
    ).execute()

    # Format header (bold + màu xanh) — lấy sheetId thực từ response
    real_ids = [s["properties"]["sheetId"] for s in spreadsheet["sheets"]]
    fmt_reqs = []
    for sid in real_ids:
        fmt_reqs.append({
            "repeatCell": {
                "range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1},
                "cell": {"userEnteredFormat": {
                    "textFormat": {"bold": True, "foregroundColor": {"red":1,"green":1,"blue":1}},
                    "backgroundColor": {"red": 0.13, "green": 0.37, "blue": 0.72},
                }},
                "fields": "userEnteredFormat(textFormat,backgroundColor)",
            }
        })
        # Auto-resize cột
        fmt_reqs.append({
            "autoResizeDimensions": {
                "dimensions": {"sheetId": sid, "dimension": "COLUMNS",
                               "startIndex": 0, "endIndex": 4}
            }
        })
    sheets_svc.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id, body={"requests": fmt_reqs}
    ).execute()

    set_public_permission(drive_svc, sheet_id)
    print(f"   ✅ Google Sheets ({len(dich_vu)} dịch vụ | "
          f"{len(thu_thuat)} thủ thuật | {len(tin_tuc)} tin tức): {sheet_url}")
    return sheet_id, sheet_url


# ============================================================
# 7. KML MAP — Thêm local service posts vào description
# ============================================================
def _build_kml_xml(dich_vu):
    n = NAP
    # Bài vệ sinh / sửa tại nhà địa phương
    local_posts = [x for x in dich_vu if x["type"] == "post" and
                   any(kw in x["url"] for kw in
                       ["tai-nha", "thuan-an", "tan-uyen", "di-an",
                        "thu-dau-mot", "quan-1", "quan-7"])]
    local_links = "".join(
        f"<li><a href='{x['url']}'>{_nfc(x['title'])}</a></li>"
        for x in local_posts[:15]
    )
    services_html = "".join(
        f"<li><a href='{x['url']}'>{_nfc(x['title'])}</a></li>"
        for x in dich_vu if x["type"] in ("category", "page")
    )

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>{n['brand']} – IT Service Map</name>
    <description>Google Authority Stack | {n['website']}</description>
    <Style id="pinStyle">
      <IconStyle>
        <color>ff0000ff</color><scale>1.2</scale>
        <Icon><href>http://maps.google.com/mapfiles/kml/paddle/wht-stars.png</href></Icon>
      </IconStyle>
    </Style>

    <Placemark>
      <name>{n['brand']}</name>
      <styleUrl>#pinStyle</styleUrl>
      <description><![CDATA[
        <h2>{n['brand']}</h2>
        <p><strong>📍 NAP:</strong> {n['address']}</p>
        <p><strong>📞 Zalo:</strong> <a href="tel:{n['phone']}">{n['phone_d']}</a></p>
        <p><strong>🌐 Web:</strong> <a href="{n['website']}">{n['website']}</a></p>
        <p><strong>🕐 Giờ:</strong> {n['hours']}</p>
        <hr/>
        <h3>Dịch Vụ Tại Địa Phương (Local SEO)</h3>
        <ul>{local_links}</ul>
        <hr/>
        <h3>Toàn Bộ Dịch Vụ</h3>
        <ul>{services_html}</ul>
      ]]></description>
      <Point><coordinates>{n['lng']},{n['lat']},0</coordinates></Point>
    </Placemark>

    <Placemark>
      <name>{n['short']} – TP.HCM</name>
      <styleUrl>#pinStyle</styleUrl>
      <description><![CDATA[
        <h2>Dịch Vụ IT Tận Nơi TP.HCM</h2>
        <p>{n['brand']} phục vụ toàn bộ TP.HCM.</p>
        <p><strong>📞</strong> <a href="tel:{n['phone']}">{n['phone_d']}</a></p>
        <p><strong>🌐</strong> <a href="{n['website']}">{n['website']}</a></p>
        <ul>{local_links}</ul>
      ]]></description>
      <Point><coordinates>106.7009,10.7769,0</coordinates></Point>
    </Placemark>

  </Document>
</kml>"""


def create_kml_map(drive_svc, folder_id, dich_vu):
    print("\n🗺️  [BƯỚC 4] Tạo file KML (Local SEO + dịch vụ khu vực)...")
    n         = NAP
    kml_bytes = _build_kml_xml(dich_vu).encode("utf-8")
    media     = MediaInMemoryUpload(kml_bytes, mimetype="application/vnd.google-earth.kml+xml")
    file_meta = {
        "name":    f"{n['short']} – Entity Map.kml",
        "parents": [folder_id],
        "description": (
            f"KML Authority Stack | NAP: {n['address']} | {n['phone_d']} | {n['website']}\n"
            "IMPORT: maps.google.com → Tạo bản đồ mới → Nhập → chọn file KML này."
        ),
    }
    kml_file = drive_svc.files().create(
        body=file_meta, media_body=media, fields="id,webViewLink"
    ).execute()
    kml_id  = kml_file["id"]
    kml_url = kml_file["webViewLink"]
    set_public_permission(drive_svc, kml_id)

    # File hướng dẫn import My Maps
    instr = (
        "HƯỚNG DẪN IMPORT KML VÀO GOOGLE MY MAPS\n"
        "==========================================\n"
        "1. Mở https://www.google.com/maps/d/\n"
        "2. Nhấn 'Tạo bản đồ mới'\n"
        "3. Nhấn 'Nhập' trong layer đầu tiên\n"
        f"4. Tải file KML: {kml_url}\n"
        f"5. Đặt tên: '{n['short']} – Sửa Máy Tính Bình Dương'\n"
        "6. Chia sẻ → Bất kỳ ai có đường link\n"
        "7. Copy URL My Maps → thêm vào entity_links.txt\n"
    )
    drive_svc.files().create(
        body={"name": "HƯỚNG DẪN Import KML – My Maps.txt", "parents": [folder_id]},
        media_body=MediaInMemoryUpload(instr.encode("utf-8"), mimetype="text/plain"),
        fields="id",
    ).execute()

    print(f"   ✅ KML: {kml_url}")
    return kml_id, kml_url


# ============================================================
# 8. ENTITY LINKS TXT
# ============================================================
def export_entity_links(links, dich_vu, thu_thuat, tin_tuc):
    print("\n📝 [BƯỚC 5] Xuất entity_links.txt...")
    now   = datetime.now().strftime("%d/%m/%Y %H:%M")
    lines = [
        "=" * 65,
        f"  GOOGLE AUTHORITY STACK — {NAP['brand']}",
        f"  Tạo lúc: {now}",
        f"  Website: {NAP['website']}",
        "=" * 65, "",
        "▶ TÀI SẢN GOOGLE ĐỂ ĐI BACKLINK TẦNG 2:", "",
    ]
    for name, url in links.items():
        lines += [f"  [{name}]", f"  {url}", ""]

    lines += [
        "-" * 65,
        "▶ NAP CHUẨN (dùng khi đăng ký directory):", "",
        f"  Tên       : {NAP['brand']}",
        f"  Địa chỉ   : {NAP['address']}",
        f"  Điện thoại: {NAP['phone_d']}",
        f"  Email     : {NAP['email']}",
        f"  Website   : {NAP['website']}",
        "",
        "-" * 65,
        f"▶ TỔNG URLS ĐÃ INDEX ({len(dich_vu)+len(thu_thuat)+len(tin_tuc)} URL):", "",
        f"  Dịch vụ  : {len(dich_vu)} URL",
        f"  Thủ thuật: {len(thu_thuat)} URL",
        f"  Tin tức  : {len(tin_tuc)} URL",
        "",
        "-" * 65,
        "▶ TOP 20 URL DỊCH VỤ (anchor text cho backlink):", "",
    ]
    for x in dich_vu[:20]:
        lines.append(f"  • {x['title']}")
        lines.append(f"    {x['url']}")
    lines += ["", "-" * 65,
              "▶ TOP 20 URL THỦ THUẬT (anchor text cho backlink):", ""]
    for x in thu_thuat[:20]:
        lines.append(f"  • {x['title']}")
        lines.append(f"    {x['url']}")

    output = "\n".join(lines)
    with open("entity_links.txt", "w", encoding="utf-8") as f:
        f.write(output)
    print("   ✅ Đã lưu: entity_links.txt")


# ============================================================
# 9. ERROR HANDLER
# ============================================================
_QUOTA_HINT = """
   ╔══════════════════════════════════════════════════════════╗
   ║  LỖI API — Kiểm tra:                                    ║
   ║  1. Service Account → đổi sang OAuth2 Desktop App       ║
   ║  2. Xóa stack_token.pickle → chạy lại → login browser  ║
   ║  3. Cloud Console → bật Drive/Docs/Sheets API           ║
   ╚══════════════════════════════════════════════════════════╝"""


def _run_step(name, fn):
    try:
        _, url = fn()
        return url
    except Exception as e:
        err = str(e)
        if any(k in err for k in ("storageQuotaExceeded", "does not have permission",
                                   "caller does not have")):
            print(_QUOTA_HINT)
            print(f"   ⏭️  Bỏ qua {name}\n")
            return f"[{name} — xem lỗi bên trên]"
        raise


# ============================================================
# 10. MAIN
# ============================================================
def main():
    print("=" * 65)
    print("  Google Authority Stack Builder v3 — Huỳnh Khang Computer")
    print("=" * 65)

    # Load & phân loại URLs
    print("\n🔍 Đang load site_map.json...")
    dich_vu, thu_thuat, tin_tuc = load_site_data()

    # Auth
    creds = get_credentials()
    drive_svc, docs_svc, sheets_svc = build_services(creds)

    folder_id  = ROOT_FOLDER_ID
    folder_url = f"https://drive.google.com/drive/folders/{folder_id}"
    print(f"\n📁 Drive Folder: {folder_url}")

    # Tạo từng tài sản
    doc_url   = _run_step("Google Doc",     lambda: create_google_doc(
        docs_svc, drive_svc, folder_id, dich_vu, thu_thuat, tin_tuc))
    sheet_url = _run_step("Google Sheets",  lambda: create_google_sheets(
        sheets_svc, drive_svc, folder_id, dich_vu, thu_thuat, tin_tuc))
    kml_url   = _run_step("KML Map",        lambda: create_kml_map(
        drive_svc, folder_id, dich_vu))

    links = {
        "Google Drive Folder": folder_url,
        "Google Doc (Pillar)": doc_url,
        "Google Sheets (3 tab)": sheet_url,
        "KML Map (Local SEO)": kml_url,
    }

    export_entity_links(links, dich_vu, thu_thuat, tin_tuc)

    print("\n" + "=" * 65)
    print("  ✅ HOÀN THÀNH!")
    print()
    print(f"  📁 Drive Folder : {folder_url}")
    print(f"  📄 Google Doc   : {doc_url}")
    print(f"  📊 Google Sheets: {sheet_url}")
    print(f"  🗺️  KML Map      : {kml_url}")
    print()
    print("  Bước tiếp theo:")
    print("  1. Đi backlink tầng 2 lên các forum, Web 2.0 trỏ về các link trên.")
    print("  2. Import KML vào Google My Maps (xem file hướng dẫn trong folder).")
    print("  3. Thêm URL My Maps vào entity_links.txt thủ công.")
    print("=" * 65)


if __name__ == "__main__":
    main()
