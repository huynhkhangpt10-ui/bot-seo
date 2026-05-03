import io
import os
import sys
import requests
import time
import unicodedata
import re
import random
from PIL import Image
import streamlit as st

# Fix encoding cho Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

# CHÚ Ý: KHAI BÁO KEY Ở ĐÂY TỪ MY_CONFIG
from my_config import client, WP_MEDIA_URL, WP_USER, WP_APP_PASS
from my_config import GOOGLE_SEARCH_API_KEY, SEARCH_ENGINE_ID

# =========================================================
# 🔍 CÔNG CỤ THÁM MÃ: ÉP GOOGLE SEARCH RA ẢNH (BỎ GIỚI HẠN)
# =========================================================
def tim_anh_mau_thuc_te(tu_khoa):
    """Sử dụng Google Custom Search - Ép tìm kiếm diện rộng"""
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'q': tu_khoa,
        'cx': SEARCH_ENGINE_ID,
        'key': GOOGLE_SEARCH_API_KEY,
        'searchType': 'image', 
        'num': 3, 
        'safe': 'off', # Tắt bộ lọc an toàn để lấy nhiều ảnh hơn
        'cr': 'countryVN', # 💥 MẸO ĐỂ ÉP GOOGLE TRẢ KẾT QUẢ DÙ CSE BỊ GIỚI HẠN
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        data = res.json()
        
        if 'error' in data:
            print(f"❌ LỖI API SEARCH GOOGLE: {data['error']['message']}")
            return []
            
        links = [item['link'] for item in data.get('items', [])]
        return links
    except Exception as e:
        print(f"⚠️ Lỗi Search Google: {e}")
        return []

# =========================================================
# 🧠 BỘ NÃO GIẢI MÃ: GEMINI VISION PHÂN TÍCH ẢNH MẪU
# =========================================================
def gemini_soi_anh_mau(urls_anh, tk_chinh, noi_dung_h2):
    image_parts = []
    
    for url in urls_anh:
        try:
            res_img = requests.get(url, timeout=10)
            if res_img.status_code == 200:
                image_parts.append({'mime_type': 'image/jpeg', 'data': res_img.content})
        except: continue

    prompt_vision = f"""
    Bạn là một chuyên gia Concept Artist.
    Hãy đọc kỹ đoạn văn sau: "{noi_dung_h2[:500]}"
    Từ khóa chính: "{tk_chinh}"
    
    Nhiệm vụ: Sáng tạo 1 câu Prompt 100% TIẾNG ANH duy nhất cho AI vẽ ảnh minh họa.
    
    Yêu cầu BẮT BUỘC CHỐNG LỖI HIỂN THỊ:
    1. DỊCH SANG TIẾNG ANH: TUYỆT ĐỐI KHÔNG đưa nguyên xi cụm từ tiếng Việt "{tk_chinh}" vào prompt. Bạn phải dịch ngữ cảnh sang tiếng Anh. 
    2. CẤM HIỂN THỊ CHỮ: Bắt buộc sử dụng cụm từ: "ABSOLUTELY NO TEXT, NO LETTERS, NO WORDS, NO TYPOGRAPHY" vào cuối prompt. 
    3. XỬ LÝ MÀN HÌNH: Nếu vẽ thiết bị có màn hình (máy tính, bảng biểu, dashboard), BẮT BUỘC miêu tả nội dung hiển thị là: "abstract data visualization, blurred charts, glowing graphs without any readable text" (biểu đồ trừu tượng, làm mờ chữ).
    4. Sáng tạo các góc máy nghệ thuật (Macro shot, over-the-shoulder, cinematic lighting).
    
    Chỉ trả về chuỗi Prompt tiếng Anh, không giải thích thêm.
    """
    
    try:
        contents_payload = [prompt_vision]
        if image_parts:
            contents_payload.extend(image_parts)
            
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=contents_payload
        )
        return response.text.strip()
    except Exception as e:
        return None

# =========================================================
# 🎯 HÀM LỌC TỪ KHÓA TÌM KIẾM (RÚT GỌN TỪ KHÓA DÀI)
# =========================================================
def rut_gon_tu_khoa_search(tk_chinh, tk_h2=""):
    """Gọt bớt chữ thừa. Trả về đúng tên phần mềm + UI"""
    tk_lower_chinh = str(tk_chinh).lower()
    tk_lower_h2 = str(tk_h2).lower()
    
    if "coreldraw" in tk_lower_chinh or "corel" in tk_lower_chinh: return "CorelDRAW UI design"
    if "photoshop" in tk_lower_chinh: return "Adobe Photoshop UI"
    if "illustrator" in tk_lower_chinh: return "Adobe Illustrator UI"
    if "premiere" in tk_lower_chinh: return "Adobe Premiere UI"
    if "autocad" in tk_lower_chinh: return "AutoCAD interface"
    if "3ds max" in tk_lower_chinh: return "3ds Max UI"
    
    nhom_tu_dich_vu = ['sửa', 'lỗi', 'hư', 'không lên', 'máy tính', 'laptop', 'máy in', 'vệ sinh', 'mainboard']
    if any(x in tk_lower_chinh or x in tk_lower_h2 for x in nhom_tu_dich_vu):
        if "laptop" in tk_lower_chinh or "laptop" in tk_lower_h2: return "laptop motherboard repair"
        if "máy in" in tk_lower_chinh or "máy in" in tk_lower_h2: return "printer repair"
        return "computer motherboard repair"
        
    words = str(tk_chinh).strip().split()
    return " ".join(words[:4]) 

# =========================================================
# 🎨 HÀM TẠO PROMPT THÔNG MINH
# =========================================================
def tao_prompt_anh_software_interface(tk_chinh, noi_dung=""):
    nd_clean = re.sub(r'^[\d\.\s]+', '', str(noi_dung)).strip()
    
    query_search = rut_gon_tu_khoa_search(tk_chinh, tk_h2=tk_chinh) 
    urls_mau = tim_anh_mau_thuc_te(query_search)
    
    # Ép gọi AI phân tích để dịch tiếng Việt sang tiếng Anh, kể cả khi không có ảnh mẫu
    prompt_thong_minh = gemini_soi_anh_mau(urls_mau, tk_chinh, nd_clean)
    
    if prompt_thong_minh:
        if "NO TEXT" not in prompt_thong_minh.upper():
             prompt_thong_minh += " ABSOLUTELY NO TEXT, BLURRED UI, NO LETTERS."
        return prompt_thong_minh

    # --- NẾU API GEMINI LỖI, SỬ DỤNG FALLBACK CHUẨN TIẾNG ANH TẬP TRUNG VÀO NGỮ CẢNH ---
    camera_angles = ["Cinematic over-the-shoulder shot", "Medium close-up shot", "Macro shot"]
    angle = random.choice(camera_angles)
    
    if any(x in str(tk_chinh).lower() for x in ['corel', 'đồ họa', 'illustrator']):
        context_rule = "creative designer workspace, digital drawing tablet, vibrant color palettes on screen"
    elif any(x in str(tk_chinh).lower() for x in ['adobe', 'photoshop', 'premiere']):
        context_rule = "video editor workspace, dark theme UI, glowing timelines and abstract media files"
    elif any(x in str(tk_chinh).lower() for x in ['autocad', '3ds max', 'revit']):
        context_rule = "architectural engineering workspace, 3D wireframe models, blueprint projections"
    else:
        context_rule = "modern technology workspace, abstract data visualization on screens, high tech setup"

    return f"{angle} of a {context_rule}. High quality photography, 8k resolution. ABSOLUTELY NO TEXT, NO LETTERS, BLURRED DASHBOARDS."

# =========================================================
# 🔴 HÀM ĐÓNG DẤU VÀ UPLOAD (GIỮ NGUYÊN)
# =========================================================
def tao_slug_anh(s):
    if not isinstance(s, str): return ""
    s = s.replace('đ', 'd').replace('Đ', 'd')
    s = unicodedata.normalize('NFKD', s).encode('ASCII', 'ignore').decode('utf-8')
    s = re.sub(r'[^\w\s-]', '', s).strip().lower()
    s = re.sub(r'[-\s]+', '-', s)
    return s

def dong_dau_logo(image_bytes, logo_path="logo_hk.png"):
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        logo_full_path = os.path.join(base_dir, logo_path)
        anh_goc = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        
        if os.path.exists(logo_full_path):
            logo = Image.open(logo_full_path).convert("RGBA")
            ty_le_logo = 0.20 
            w_logo_moi = int(anh_goc.width * ty_le_logo)
            h_logo_moi = int(logo.height * (w_logo_moi / logo.width))
            logo = logo.resize((w_logo_moi, h_logo_moi), Image.LANCZOS)
            anh_goc.paste(logo, (anh_goc.width - w_logo_moi - 20, anh_goc.height - h_logo_moi - 20), logo)
            logo.close() # 💥 ÉP XẢ RAM CỦA LOGO
            
        output_io = io.BytesIO()
        # 💥 Giảm quality xuống 85 (mắt thường không phân biệt được nhưng giảm 30% tải CPU)
        anh_goc.convert("RGB").save(output_io, format="JPEG", quality=85) 
        anh_goc.close() # 💥 ÉP XẢ RAM CỦA ẢNH GỐC
        return output_io.getvalue()
    except Exception as e: 
        return image_bytes

def ve_va_upload_anh(prompt_tieng_anh, tk_chinh, text_seo, short_slug=""):
    for lan in range(3):
        try:
            result = client.models.generate_images(
                model='imagen-4.0-generate-001', 
                prompt=prompt_tieng_anh,
                config=dict(number_of_images=1, output_mime_type="image/jpeg", aspect_ratio="16:9")
            )
            img_with_logo = dong_dau_logo(result.generated_images[0].image.image_bytes, "logo_hk.png")
            filename = f"huynhkhang-{tao_slug_anh(tk_chinh) if not short_slug else short_slug}-{os.urandom(4).hex()}.jpg" 
            files = {'file': (filename, io.BytesIO(img_with_logo), 'image/jpeg')}
            wp_res = requests.post(WP_MEDIA_URL, auth=(WP_USER, WP_APP_PASS), files=files, data={"title": f"Ảnh {text_seo}"}, timeout=60)
            if wp_res.status_code == 201: return wp_res.json().get('id'), wp_res.json().get('source_url')
        except: time.sleep(5) 
    return None, None