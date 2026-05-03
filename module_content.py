import re
import time
from google.genai import types
from my_config import client

# GỌI 2 FILE VỪA TẠO VÀO ĐÂY ĐỂ SỬ DỤNG
from module_scenarios import phan_loai_kich_ban
from module_prompts import tao_prompt_dan_y, tao_prompt_bai_viet

def sinh_dan_y(tk_auto, tieu_de_excel, lenh_tim_kiem_ai, cap_nhat_trang_thai_func):
    
    cap_nhat_trang_thai_func("🧠 Đang đọc tài liệu gốc và lên dàn ý...")
    
    # 💥 Gọi hàm và truyền thẳng cái lệnh tìm kiếm vào để nó TỰ ĐỘNG BẬT BỘ LỌC
    prompt_outline_auto = tao_prompt_dan_y(tk_auto, tieu_de_excel, lenh_tim_kiem_ai)
    
    text_out_auto = ""
    last_error = "Lý do không xác định"
    
    for lan_thu in range(3):
        try:
            res_outline = client.models.generate_content(
                model="gemini-2.5-pro", 
                contents=prompt_outline_auto,
                config=types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())])
            )
            
            # Kiểm tra xem AI có bị khóa mõm vì lý do an toàn không
            if not res_outline.candidates:
                last_error = "Bị bộ lọc An Toàn (Safety) của Google chặn vì nghi ngờ chứa từ khóa nhạy cảm/crack."
                continue
                
            text_out_auto = res_outline.text
            if text_out_auto:
                # ==========================================================
                # 💥 BẮT AI KHAI BÁO LINK ĐÃ ĐỌC (LÀM GỌN LINK BẰNG MARKDOWN)
                # ==========================================================
                try:
                    nguon_doc = []
                    if hasattr(res_outline.candidates[0], 'grounding_metadata') and res_outline.candidates[0].grounding_metadata:
                        meta = res_outline.candidates[0].grounding_metadata
                        if hasattr(meta, 'grounding_chunks'):
                            for chunk in meta.grounding_chunks:
                                if hasattr(chunk, 'web') and chunk.web and hasattr(chunk.web, 'uri'):
                                    uri = chunk.web.uri
                                    # Cố gắng lấy tiêu đề bài báo, nếu không có thì để rỗng
                                    title = getattr(chunk.web, 'title', '')
                                    # Chống trùng lặp link
                                    if not any(item['uri'] == uri for item in nguon_doc):
                                        nguon_doc.append({'uri': uri, 'title': title})
                    if nguon_doc:
                        links_str = ""
                        try:
                            from urllib.parse import urlparse as _urlparse
                        except Exception:
                            _urlparse = None
                        for i, item in enumerate(nguon_doc):
                            ten_hien_thi = item['title'] if item['title'] else f"Link nguồn {i+1}"
                            if _urlparse:
                                site = _urlparse(item['uri']).netloc.replace('www.', '')
                            else:
                                site = item['uri'][:40]
                            links_str += f"\n👉 {ten_hien_thi} ({site})"

                        cap_nhat_trang_thai_func(f"🌐 [KIỂM DUYỆT SỰ THẬT] AI ĐÃ ĐỌC CÁC BÀI SAU ĐỂ LÊN DÀN Ý:{links_str}")
                except Exception as e:
                    pass
                # ==========================================================
                break 
            else:
                last_error = "API Google nhả kết quả nhưng trống rỗng (Thường do Google Search không tìm thấy dữ liệu)."
                
        except Exception as e:
            last_error = str(e)
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                cap_nhat_trang_thai_func(f"⚠️ Google quá tải. Đang nghỉ 15s (lần {lan_thu + 1}/3)...")
                time.sleep(15) 
            else:
                return False, f"Lỗi kỹ thuật từ AI: {last_error}", "", "", ""
    
    if not text_out_auto: 
        return False, f"Hủy viết bài do lỗi sinh Dàn ý: {last_error}", "", "", ""

    tieu_de_seo_auto = tieu_de_excel if tieu_de_excel else tk_auto
    meta_seo_auto = f"Bài viết chi tiết về {tk_auto} chuẩn SEO."
    tu_khoa_phu_auto = ""

    # 💥 BƯỚC 1: DỌN SẠCH RÁC MARKDOWN MÀ AI HAY NHÉT VÀO
    text_clean = text_out_auto.replace('```markdown', '').replace('```html', '').replace('```', '')
    text_clean = text_clean.replace('\\[', '[').replace('\\]', ']')
    # Ép các thẻ bị in đậm về dạng chuẩn
    text_clean = re.sub(r'\*\*\[(.*?)\]\*\*', r'[\1]', text_clean)

    # 💥 BƯỚC 2: BÓC TÁCH TIÊU ĐỀ (VỚI CƠ CHẾ CỨU HỘ)
    title_match = re.search(r'\[TITLE\](.*?)\[/TITLE\]', text_clean, re.IGNORECASE | re.DOTALL)
    if title_match:
        tieu_de_seo_auto = title_match.group(1).strip()
    else:
        # 🚑 CỨU HỘ: Nếu AI lờ đi thẻ [TITLE] mà tự viết dạng "# Tiêu đề" hoặc "**Tiêu đề:**"
        cuu_ho_title = re.search(r'(?:\*\*Tiêu đề:?\*\*\s*|#\s+)(.*?\n)', text_clean, re.IGNORECASE)
        if cuu_ho_title:
            tieu_de_seo_auto = cuu_ho_title.group(1).strip()

    # Dọn dẹp ký tự thừa khỏi tiêu đề và xóa dòng tiêu đề ra khỏi dàn ý
    tieu_de_seo_auto = tieu_de_seo_auto.replace('**', '').replace('"', '').replace("'", "")
    text_out_auto = re.sub(r'\[TITLE\].*?\[/TITLE\]', '', text_out_auto, flags=re.IGNORECASE | re.DOTALL)
    text_out_auto = re.sub(r'(?:\*\*Tiêu đề:?\*\*\s*|#\s+).*?\n', '', text_out_auto, count=1, flags=re.IGNORECASE)

    # 💥 BƯỚC 3: BÓC TÁCH META SEO (VỚI CƠ CHẾ CỨU HỘ)
    meta_match = re.search(r'\[META\](.*?)\[/META\]', text_clean, re.IGNORECASE | re.DOTALL)
    if meta_match:
        meta_seo_auto = meta_match.group(1).strip()
    else:
        # 🚑 CỨU HỘ Meta
        cuu_ho_meta = re.search(r'(?:\*\*Meta:?\*\*\s*|\*\*Meta description:?\*\*\s*)(.*?\n)', text_clean, re.IGNORECASE)
        if cuu_ho_meta:
            meta_seo_auto = cuu_ho_meta.group(1).strip()
            
    meta_seo_auto = meta_seo_auto.replace('**', '').replace('"', '').replace("'", "")
    text_out_auto = re.sub(r'\[META\].*?\[/META\]', '', text_out_auto, flags=re.IGNORECASE | re.DOTALL)
    text_out_auto = re.sub(r'(?:\*\*Meta:?\*\*\s*|\*\*Meta description:?\*\*\s*).*?\n', '', text_out_auto, count=1, flags=re.IGNORECASE)

    # 💥 BƯỚC 4: BÓC TÁCH TỪ KHÓA PHỤ
    kw_match = re.search(r'\[KEYWORDS\](.*?)\[/KEYWORDS\]', text_clean, re.IGNORECASE | re.DOTALL)
    if kw_match:
        tu_khoa_phu_auto = kw_match.group(1).strip().replace('**', '')
        text_out_auto = re.sub(r'\[KEYWORDS\].*?\[/KEYWORDS\]', '', text_out_auto, flags=re.IGNORECASE | re.DOTALL)

    # Trả về outline đã được cạo sạch các thẻ cấu hình
    outline_auto = text_out_auto.strip()
    return True, outline_auto, tieu_de_seo_auto, meta_seo_auto, tu_khoa_phu_auto


def sinh_bai_viet(tk_auto, tieu_de_seo_auto, short_slug_auto, link_ins_auto, outline_auto, nam_hien_tai, khach_hang_rd, dia_diem_rd, lenh_tim_kiem_ai, cap_nhat_trang_thai_func, link_tai_phan_mem="", is_phan_mem=False, is_phan_mem_vip=False):
    
    cap_nhat_trang_thai_func("✍️ Đang thu thập dữ liệu và múa phím viết bài...")
    
    # 1. Lấy toàn bộ logic Kịch bản/Báo giá từ file module_scenarios
    config_kich_ban = phan_loai_kich_ban(tk_auto, nam_hien_tai, khach_hang_rd, dia_diem_rd)

    # 2. Lấy câu lệnh viết bài từ file module_prompts
    prompt_viet_bai_auto = tao_prompt_bai_viet(tk_auto, short_slug_auto, link_ins_auto, outline_auto, nam_hien_tai, config_kich_ban, lenh_tim_kiem_ai, link_tai_phan_mem, is_phan_mem, is_phan_mem_vip)
    
    # 3. Gửi cho Gemini xử lý kèm lệnh HẠ BỘ LỌC AN TOÀN (VÀ CƠ CHẾ VƯỢT LỖI 429)
    bai_viet_raw = ""
    last_error = ""
    
    for lan_thu in range(3):
        try:
            cau_hinh_an_toan = types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                safety_settings=[
                    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_ONLY_HIGH"),
                    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_ONLY_HIGH"),
                    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_ONLY_HIGH"),
                    types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_ONLY_HIGH"),
                ]
            )

            res_bai_auto = client.models.generate_content(
                model="gemini-2.5-pro", 
                contents=prompt_viet_bai_auto,
                config=cau_hinh_an_toan
            )
            
            # Bắt lỗi vòng gửi xe (Bị khoá mõm do chính sách Google)
            if not res_bai_auto.candidates:
                return False, "Bị Google chặn ngang vì nghi ngờ chứa nội dung nhạy cảm."
                
            # 💥 ĐÃ SỬA LỖI Ở ĐÂY: Trực tiếp lấy bài viết, vứt bỏ lệnh bắt bẻ "STOP"
            try:
                bai_viet_raw = res_bai_auto.text
                
                # ==========================================================
                # 💥 BẮT AI KHAI BÁO LINK ĐÃ ĐỌC (LÀM GỌN LINK BẰNG MARKDOWN)
                # ==========================================================
                try:
                    nguon_doc = []
                    if hasattr(res_bai_auto.candidates[0], 'grounding_metadata') and res_bai_auto.candidates[0].grounding_metadata:
                        meta = res_bai_auto.candidates[0].grounding_metadata
                        if hasattr(meta, 'grounding_chunks'):
                            for chunk in meta.grounding_chunks:
                                if hasattr(chunk, 'web') and chunk.web and hasattr(chunk.web, 'uri'):
                                    uri = chunk.web.uri
                                    title = getattr(chunk.web, 'title', '')
                                    if not any(item['uri'] == uri for item in nguon_doc):
                                        nguon_doc.append({'uri': uri, 'title': title})
                    if nguon_doc:
                        links_str = ""
                        try:
                            from urllib.parse import urlparse as _urlparse
                        except Exception:
                            _urlparse = None
                        for i, item in enumerate(nguon_doc):
                            ten_hien_thi = item['title'] if item['title'] else f"Link nguồn {i+1}"
                            if _urlparse:
                                site = _urlparse(item['uri']).netloc.replace('www.', '')
                            else:
                                site = item['uri'][:40]
                            links_str += f"\n👉 {ten_hien_thi} ({site})"

                        cap_nhat_trang_thai_func(f"🌐 [NGUỒN THAM KHẢO] AI đã dựa vào các bài này để viết Nội Dung:{links_str}")
                except Exception as e:
                    pass
                # ==========================================================
                
            except Exception:
                pass
            
            # Nếu có nội dung thành công thì thoát vòng lặp ngay lập tức
            if bai_viet_raw:
                break 
            else:
                ly_do_dung = res_bai_auto.candidates[0].finish_reason
                last_error = f"AI nộp giấy trắng (Mã lỗi: {ly_do_dung})."
                
        except Exception as e:
            last_error = str(e)
            # NẾU ĐỤNG LỖI QUÁ TẢI (429), CHO BOT NGHỈ NGƠI ĐỂ HỒI TOKEN
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e) or "Quota" in str(e):
                thoi_gian_nghi = 60 * (lan_thu + 1) # Lần 1 nghỉ 60s, lần 2 nghỉ 120s
                cap_nhat_trang_thai_func(f"⚠️ Hết hạn mức Token API. Bot tự động uống cafe {thoi_gian_nghi} giây để Google nhả Quota (Lần thử {lan_thu + 1}/3)...")
                import time
                time.sleep(thoi_gian_nghi)
            else:
                # Nếu là lỗi khác thì báo luôn
                return False, f"Lỗi nền tảng AI: {last_error}"
                
    if not bai_viet_raw: 
        return False, f"Đã thử 3 lần vẫn thất bại do: {last_error}"
         
    # Dọn dẹp rác định dạng
    bai_viet_auto = bai_viet_raw.replace('```html', '').replace('```markdown', '').replace('```', '').strip()
    bai_viet_auto = re.sub(r'^(#+)\s+\d{1,2}(?:\.\d{1,2})*\.?\s+(.*)$', r'\1 \2', bai_viet_auto, flags=re.MULTILINE)

    # =========================================================
    # 🛡️ BẢO VỆ: XÓA CÁC HỘP TẢI XUỐNG TỰ SINH (KHÔNG ĐƯỢC PHÉP)
    # =========================================================
    # Nếu có link_tai_phan_mem, AI chỉ được chèn nút đơn giản (inline <a>)
    # Phát hiện và xóa các <div> phức tạp với tiêu đề "Tải", "Download"
    if is_phan_mem and not is_phan_mem_vip and link_tai_phan_mem:
        # Pattern: <div...> có chứa "Tải" hoặc "Download" trong <h2>/<h3>
        pattern_hop_tai = r'<div[^>]*>[\s\S]*?<h[23][^>]*>.*?(?:Tải|Download|Link tải).*?</h[23]>[\s\S]*?</div>'
        so_hop_bi_xoa = len(re.findall(pattern_hop_tai, bai_viet_auto, re.IGNORECASE))
        if so_hop_bi_xoa > 0:
            bai_viet_auto = re.sub(pattern_hop_tai, '', bai_viet_auto, flags=re.IGNORECASE)
            cap_nhat_trang_thai_func(f"🛡️ Đã tự động xóa {so_hop_bi_xoa} hộp tải xuống tự sinh không được phép")

    # =========================================================
    # 💥 BƯỚC CHỐT HẠ: CHÈN CẢNH BÁO CRACK VÀO CUỐI BÀI VIẾT
    # =========================================================
    html_canh_bao = config_kich_ban.get('html_canh_bao_crack', '')
    if html_canh_bao:
        bai_viet_auto = bai_viet_auto + "\n\n" + html_canh_bao

    return True, bai_viet_auto