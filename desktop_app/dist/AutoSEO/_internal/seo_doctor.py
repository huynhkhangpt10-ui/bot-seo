import pandas as pd
import requests
import re
import gc # Thư viện dọn rác, giải phóng RAM cho VPS
import streamlit as st
from bs4 import BeautifulSoup
from google.oauth2 import service_account
from googleapiclient.discovery import build
from my_config import *
from datetime import datetime, timedelta
import google.auth.transport.requests

def ket_noi_gsc():
    scopes = ['https://www.googleapis.com/auth/webmasters.readonly']
    try:
        credentials = service_account.Credentials.from_service_account_file(GOOGLE_KEY_PATH, scopes=scopes)
        return build('webmasters', 'v3', credentials=credentials)
    except Exception as e:
        st.error(f"Lỗi kết nối GSC: {e}")
        return None

def fetch_gsc_data(service, site_url, days_start=30, days_end=3):
    start_date = (datetime.now() - timedelta(days=days_start)).strftime('%Y-%m-%d')
    end_date = (datetime.now() - timedelta(days=days_end)).strftime('%Y-%m-%d')
    request = {'startDate': start_date, 'endDate': end_date, 'dimensions': ['query', 'page'], 'rowLimit': 5000}
    try:
        res = service.searchanalytics().query(siteUrl=site_url, body=request).execute()
        if 'rows' in res:
            df = pd.DataFrame([{'Từ khóa': r['keys'][0], 'URL': r['keys'][1], 'Clicks': r['clicks'], 
                                 'Impressions': r['impressions'], 'Position': round(r['position'], 1)} for r in res['rows']])
            df_clean = df[~df['URL'].str.contains('#')].copy() # Lọc rác jump link
            
            # Xả RAM
            del df
            gc.collect() 
            
            return df_clean
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Lỗi GSC: {e}")
        return pd.DataFrame()

# --- CÁC HÀM CHẨN ĐOÁN (Audit) ---
def audit_organic_only(df):
    if df.empty: return df
    cac_tu_cam = ['huynhkhang', 'huynh khang', 'huỳnh khang']
    mask = df['Từ khóa'].str.lower().apply(lambda x: any(tu in x for tu in cac_tu_cam))
    df_result = df[~mask].reset_index(drop=True)
    gc.collect() # Xả RAM
    return df_result

def audit_cannibalization(df):
    """NÚT: Check Ăn thịt từ khóa"""
    if df.empty: return df
    
    cac_tu_cam = ['huynhkhang', 'huynh khang', 'huỳnh khang', 'site:', 'huynhkhanh', 'huynh khanh']
    mask = df['Từ khóa'].str.lower().apply(lambda x: any(tu in x for tu in cac_tu_cam))
    df_sach = df[~mask].reset_index(drop=True) 
    
    if df_sach.empty: return pd.DataFrame()
    
    grouped = df_sach.groupby('Từ khóa').agg({'URL': 'nunique', 'Clicks': 'sum'}).reset_index()
    cannibal_kws = grouped[grouped['URL'] > 1].sort_values('URL', ascending=False)
    
    results = []
    for kw in cannibal_kws['Từ khóa']:
        urls = df_sach[df_sach['Từ khóa'] == kw]['URL'].unique().tolist()
        urls_that_su = [u for u in urls if '/category/' not in u and '/tag/' not in u and u != 'https://huynhkhang.com/']
        
        if len(urls_that_su) > 1:
            results.append({
                'Từ khóa': kw, 
                'Số URL tranh chấp': len(urls_that_su), 
                'Danh sách bài': " | ".join(urls_that_su)
            })
            
    # Xả bộ nhớ sau khi tính toán xong
    del df_sach, grouped, cannibal_kws
    gc.collect()
            
    return pd.DataFrame(results)

def audit_onpage_full(df):
    if df.empty: return pd.DataFrame()
    urls = df['URL'].unique()[:15]
    results = []
    
    # 🟢 VƯỢT TƯỜNG LỬA CLOUDFLARE: Định danh Bot
    headers = {'User-Agent': 'HuynhKhang-SEODoctor-Bot/1.0'}
    
    for url in urls:
        try:
            r = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            content = soup.find('main') or soup.find('article') or soup.body
            text = content.get_text(separator=' ')
            words = len(re.findall(r'\w+', text))
            title_tag = soup.title.string if soup.title else ""
            h2_tags = [h.get_text().strip() for h in soup.find_all('h2')]
            h2_long = [h for h in h2_tags if len(h) > 70]
            has_faq = any(x in text.lower() for x in ["hỏi đáp", "faq", "câu hỏi thường gặp"])
            results.append({'URL': url, 'Số chữ': words, 'Độ dài Title': f"{len(title_tag)} ký tự", 'H2 lỗi': len(h2_long), 'Mục FAQ': "✅ Có" if has_faq else "❌ Thiếu"})
        except: continue
        
    gc.collect()
    return pd.DataFrame(results)

def audit_content_decay(service, site_url):
    df_now = fetch_gsc_data(service, site_url, 30, 3)
    df_prev = fetch_gsc_data(service, site_url, 60, 31)
    if df_now.empty or df_prev.empty: return pd.DataFrame()
    
    merged = pd.merge(df_now, df_prev, on=['Từ khóa', 'URL'], suffixes=('_nay', '_truoc'))
    merged['Giảm %'] = ((merged['Clicks_nay'] - merged['Clicks_truoc']) / merged['Clicks_truoc']) * 100
    df_result = merged[merged['Giảm %'] <= -20].sort_values('Giảm %')[['Từ khóa', 'URL', 'Clicks_truoc', 'Clicks_nay', 'Giảm %']].copy()
    
    del df_now, df_prev, merged
    gc.collect()
    
    return df_result

def audit_zombie_pages(service, site_url):
    df_90 = fetch_gsc_data(service, site_url, 90, 3)
    if df_90.empty: return pd.DataFrame()
    
    zombie = df_90.groupby('URL')['Clicks'].sum().reset_index()
    df_result = zombie[zombie['Clicks'] == 0].copy()
    
    del df_90, zombie
    gc.collect()
    
    return df_result

# --- PHÒNG PHẪU THUẬT (Surgery) ---
def tim_post_id_tu_url(url):
    """Lấy Post ID của bài viết từ URL thông qua slug"""
    slug = url.strip('/').split('/')[-1]
    
    # 🟢 VƯỢT TƯỜNG LỬA CLOUDFLARE
    headers = {'User-Agent': 'HuynhKhang-SEODoctor-Bot/1.0'}
    
    res = requests.get(f"{WP_POSTS_URL}?slug={slug}", headers=headers, auth=(WP_USER, WP_APP_PASS))
    if res.status_code == 200 and res.json():
        return res.json()[0]['id'], res.json()[0]['content']['rendered']
    return None, None

def ke_don_seo_ai(row_data, loai_benh, selected_url):
    """AI chẩn đoán tập trung vào đúng 1 URL đang nằm trên bàn mổ"""
    from my_modules import client
    from datetime import datetime 
    
    nam_hien_tai = datetime.now().year 
    
    thong_tin_benh = ""
    for col, val in row_data.items():
        if col != "👉 Chọn":
            thong_tin_benh += f"- {col}: {val}\n"
            
    luat_san_pham = """
    🔴 THÔNG TIN BẢN QUYỀN SẢN PHẨM (BẮT BUỘC PHẢI VIẾT ĐÚNG SỰ THẬT, KHÔNG BỊA ĐẶT):
    - Phần mềm Autodesk: Cung cấp bản quyền EDU (Education). Tuyệt đối KHÔNG viết là bản thương mại (Commercial).
    - Phần mềm Adobe: Cấp quyền (add) email cá nhân vào gói Team. MỖI TÀI KHOẢN CHỈ ĐƯỢC 1 THIẾT BỊ. (Tuyệt đối KHÔNG quảng cáo đây là gói quản lý doanh nghiệp chia sẻ tài nguyên).
    - Phần mềm CorelDRAW: Cung cấp Key bản quyền add trực tiếp.
    """
            
    prompt = f"""
    Bạn là một Chuyên gia SEO Kỹ thuật thực chiến của HuynhKhang.com. 
    🔴 LƯU Ý THỜI GIAN: Năm hiện tại đang là {nam_hien_tai}. KHÔNG dùng năm cũ.
    {luat_san_pham}
    
    Bỏ qua các câu chào hỏi rườm rà.
    1. LOẠI LỖI CHUNG: {loai_benh}
    2. URL ĐANG NẰM TRÊN BÀN MỔ: {selected_url}
    3. DỮ LIỆU CỦA CA BỆNH NÀY:
    {thong_tin_benh}
    
    NHIỆM VỤ CỦA BẠN:
    Đưa ra Phác đồ điều trị CHI TIẾT. Nếu là "Lỗi On-page": Gợi ý 2-3 H2 mới. Viết sẵn 3 câu hỏi FAQ kèm câu trả lời (TRONG FAQ PHẢI LỒNG GHÉP KHÉO LÉO THÔNG TIN BẢN QUYỀN).
    Viết ngắn gọn theo từng gạch đầu dòng.
    """
    
    try:
        response = client.models.generate_content(model="gemini-2.5-pro", contents=prompt)
        return response.text
    except Exception as e:
        return f"Lỗi AI: {e}"

def phau_thuat_nang_cap_bai_viet(url, benh_ly, phac_do_dieu_tri):
    """AI tự động vào sửa bài trên Web DỰA THEO PHÁC ĐỒ VÀ LUẬT SẢN PHẨM"""
    post_id, old_html = tim_post_id_tu_url(url)
    if not post_id: return False, "Không tìm thấy Post ID để sửa."

    from my_modules import client
    from datetime import datetime
    nam_hien_tai = datetime.now().year

    luat_san_pham = """
    🔴 THÔNG TIN BẢN QUYỀN SẢN PHẨM (BẮT BUỘC PHẢI VIẾT ĐÚNG SỰ THẬT, KHÔNG BỊA ĐẶT):
    - Phần mềm Autodesk: Cung cấp bản quyền EDU (Education). Tuyệt đối KHÔNG viết là bản thương mại (Commercial).
    - Phần mềm Adobe: Cấp quyền (add) email cá nhân vào gói Team. MỖI TÀI KHOẢN CHỈ ĐƯỢC 1 THIẾT BỊ. (Tuyệt đối KHÔNG quảng cáo đây là gói quản lý doanh nghiệp chia sẻ tài nguyên).
    - Phần mềm CorelDRAW: Cung cấp Key bản quyền add trực tiếp.
    """

    prompt = f"""
    Bạn là Huỳnh Khang - Chuyên gia IT & SEO. Hãy phẫu thuật sửa bài viết này DỰA TRÊN PHÁC ĐỒ ĐIỀU TRỊ.
    🔴 LƯU Ý THỜI GIAN: Năm hiện tại là {nam_hien_tai}.
    {luat_san_pham}
    Bệnh lý tổng quan: {benh_ly}.
    --- PHÁC ĐỒ ĐIỀU TRỊ ---
    {phac_do_dieu_tri}
    --- NỘI DUNG HTML CŨ ---
    {old_html}
    --- YÊU CẦU ---
    Giữ nguyên định dạng HTML cơ bản và toàn bộ link nội bộ cũ. TRẢ VỀ DUY NHẤT MÃ HTML SẠCH.
    """
    try:
        res_ai = client.models.generate_content(model="gemini-2.5-pro", contents=prompt)
        new_html = res_ai.text.replace('```html', '').replace('```', '').strip()
        
        headers = {'User-Agent': 'HuynhKhang-SEODoctor-Bot/1.0'}
        update = requests.post(f"{WP_POSTS_URL}/{post_id}", headers=headers, auth=(WP_USER, WP_APP_PASS), json={"content": new_html})
        return update.status_code == 200, "Cập nhật thành công!"
    except Exception as e: return False, str(e)
    
# =====================================================================
# 💎 MODULE: KHAI THÁC TỪ KHÓA TIỀM NĂNG (VÉT MÁNG GSC)
# =====================================================================

BLACKLIST_SEO = [
    "huỳnh khang", "huynh khang", "khang it", "khangit",
    "phong vũ", "phong vu", "thế giới di động", "thegioididong", "tgdd", 
    "fpt", "điện máy xanh", "dien may xanh", "hacom", "gearvn", 
    "nguyễn kim", "nguyen kim", "cellphones", "hoàng hà", "hoang ha", "huỳnh khánh", "huynh khanh", "huynhkhang", "huynhkhanh"
]

def loc_tu_khoa_ong_ke(keyword):
    kw_lower = keyword.lower()
    if any(bad_word in kw_lower for bad_word in BLACKLIST_SEO): return False
    if len(keyword.split()) < 3: return False
    return True

def fetch_and_push_to_sheets(service, site_url, worksheet, current_keywords):
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    end_date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
    
    request = {'startDate': start_date, 'endDate': end_date, 'dimensions': ['query'], 'rowLimit': 15000} # Đẩy limit lên lấy nhiều từ khóa hơn
    
    try:
        res = service.searchanalytics().query(siteUrl=site_url, body=request).execute()
        rows = res.get('rows', [])
        
        new_kws = []
        if rows:
            for r in rows:
                query = r['keys'][0]
                impressions = r['impressions']
                clicks = r['clicks']
                
                if impressions > 50 and clicks < 5:
                    if loc_tu_khoa_ong_ke(query) and query.lower() not in [k.lower() for k in current_keywords]:
                        new_kws.append([query, "", query.title()])
            
            if new_kws:
                worksheet.append_rows(new_kws)
                gc.collect() # Xả RAM
                return len(new_kws)
                
        gc.collect()
        return 0
    except Exception as e:
        st.error(f"Lỗi khi vét máng GSC: {e}")
        return 0
    
# --- KHU VỰC CHỨC NĂNG KIỂM TRA VÀ ÉP INDEX ---
def lay_token_gsc_indexing():
    try:
        scopes = ['https://www.googleapis.com/auth/webmasters.readonly', 'https://www.googleapis.com/auth/indexing']
        creds = service_account.Credentials.from_service_account_file(GOOGLE_KEY_PATH, scopes=scopes)
        request = google.auth.transport.requests.Request()
        creds.refresh(request)
        return creds.token
    except Exception as e:
        return None

def check_url_index(site_url, url_check):
    token = lay_token_gsc_indexing()
    if not token: return False, "Lỗi: Không lấy được Token xác thực từ Google Cloud."
    
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    data = {"inspectionUrl": url_check, "siteUrl": site_url, "languageCode": "vi-VN"}
    
    try:
        res = requests.post('https://searchconsole.googleapis.com/v1/urlInspection/index:inspect', headers=headers, json=data)
        kq = res.json()
        if 'inspectionResult' in kq:
            trang_thai = kq['inspectionResult']['indexStatusResult']['coverageState']
            
            # 🟢 TỐI ƯU LOGIC BẮT VERDICT
            verdict = kq['inspectionResult']['indexStatusResult'].get('verdict', '')
            
            if verdict == 'PASS':
                return True, f"✅ Đã Index: {trang_thai}"
            else:
                return False, f"⚠️ Chưa Index (Hoặc lỗi): {trang_thai}"
                
        return False, str(kq)
    except Exception as e:
        return False, str(e)

def ep_index_url(url_ep):
    token = lay_token_gsc_indexing()
    if not token: return False, "Lỗi: Không lấy được Token."
    
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    data = {"url": url_ep, "type": "URL_UPDATED"}
    
    try:
        res = requests.post('https://indexing.googleapis.com/v3/urlNotifications:publish', headers=headers, json=data)
        kq = res.json()
        if 'urlNotificationMetadata' in kq:
            return True, f"🚀 Ép Index Thành Công! Google Bot đã nhận lệnh tới bú link: {url_ep}"
        elif 'error' in kq:
            return False, kq['error'].get('message', 'Lỗi không xác định từ Google')
        return False, str(kq)
    except Exception as e:
        return False, str(e)