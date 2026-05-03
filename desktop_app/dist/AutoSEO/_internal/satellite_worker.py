import time
import random
import re
import os
import streamlit as st
from my_modules import *
from master_api import *

def thuc_thi_ban_ve_tinh(danh_sach_cho, quota_day, max_satellite_posts, sleep_time, worksheet, df, client_ai):
    """
    Hàm xử lý logic chạy thật cho trạm vệ tinh
    """
    # ==========================================
    # 1. CHUẨN BỊ NGUYÊN LIỆU (Nằm ở ngoài vòng lặp)
    # ==========================================
    random.shuffle(danh_sach_cho)
    so_bai_se_ban = min(len(danh_sach_cho), quota_day)
    
    # Cắt lấy đúng số lượng bài theo Quota
    danh_sach_thuc_thi = danh_sach_cho[:so_bai_se_ban]
    
    danh_sach_5_site = [
        {'name': 'Blogger Bình Dương', 'id': '5214607832735598692', 'type': 'blogger'},
        {'name': 'Blogger Tân Uyên', 'id': '4342701550163439217', 'type': 'blogger'},
        {'name': 'WP Bình Dương', 'url': 'https://caiwinbinhduong.wordpress.com/xmlrpc.php', 'type': 'wp'},
        {'name': 'WP Tân Uyên', 'url': 'https://suamaytinhtanuyen.wordpress.com/xmlrpc.php', 'type': 'wp'},
        {'name': 'Tumblr Khang IT', 'id': 'dichvuhuynhkhang', 'type': 'tumblr'}
    ]

    try:
        progress_bar = st.progress(0)
        status_text = st.empty()
    except:
        progress_bar = None
        status_text = None

    # ==========================================
    # 2. VÒNG LẶP HÀNH ĐỘNG CHÍNH (Thợ bắt đầu làm việc)
    # ==========================================
    for dem, row in enumerate(danh_sach_thuc_thi):
        
        # 🛑 CHÈN CÁI PHANH KHẨN CẤP VÀO ĐÂY (Đầu mỗi quy trình viết 1 bài)
        if os.path.exists("stop_vetinh.txt"):
            try:
                os.remove("stop_vetinh.txt") # Xóa cờ đi để dọn dẹp
            except: pass
            print("🚨 LỆNH DỪNG KHẨN CẤP ĐÃ ĐƯỢC KÍCH HOẠT. KẾT THÚC LUỒNG NGẦM!")
            break # Phá vỡ vòng lặp, bot chính thức dừng hoạt động

        tk_ve_tinh = str(row['Từ khóa']).strip()
        link_web_chinh = str(row.get('Link bài viết', 'https://huynhkhang.com')).strip()
        
        # --- A. GÓC NHÌN CHUYÊN GIA REVIEW ---
        kich_ban = random.choice([
            {"huong": "🌟 Giới thiệu & Tổng quan", "chi_tiet": "Giới thiệu những điểm nổi bật nhất của phần mềm."},
            {"huong": "🧐 Review chi tiết tính năng", "chi_tiet": "Phân tích sâu các tính năng và trải nghiệm người dùng."},
            {"huong": "💡 Giải pháp công nghệ", "chi_tiet": "Cách phần mềm giải quyết các khó khăn cho công việc."},
            {"huong": "🏆 So sánh & Lựa chọn", "chi_tiet": "So sánh với bản cũ hoặc đối thủ để khẳng định giá trị."}
        ])
        
        if status_text:
            try: status_text.info(f"🤖 AI Reviewer đang soạn bài ({dem+1}/{so_bai_se_ban}): '{tk_ve_tinh}'")
            except: pass
        print(f"🤖 Đang soạn bài ({dem+1}/{so_bai_se_ban}): '{tk_ve_tinh}'")

        prompt_ai = f"""
        Bạn là một Chuyên gia Review Công nghệ. Hãy viết bài giới thiệu về: "{tk_ve_tinh}".
        [YÊU CẦU]: Vai diễn Reviewer chuyên nghiệp, văn phong hiện đại. Định dạng HTML (h2, h3, p, ul, li).
        Tiêu đề bọc trong [TITLE]...[/TITLE].
        Backlink: Chèn link về bài gốc tại <a href='{link_web_chinh}'>bài viết này</a>.
        Góc nhìn: {kich_ban['chi_tiet']}
        """
        
        try:
            # 1. GỌI AI VIẾT BÀI
            res = client_ai.models.generate_content(model="gemini-2.5-flash", contents=prompt_ai)
            bai_viet_raw = res.text
            
            title_match = re.search(r'\[TITLE\](.*?)\[/TITLE\]', bai_viet_raw, re.IGNORECASE | re.DOTALL)
            tieu_de_vt = title_match.group(1).strip() if title_match else f"Review {tk_ve_tinh}"
            noi_dung_vt = re.sub(r'\[TITLE\].*?\[/TITLE\]', '', bai_viet_raw, flags=re.IGNORECASE | re.DOTALL).strip()

            # 2. VẼ ẢNH
            if status_text:
                try: status_text.text(f"🎨 Đang vẽ ảnh Reviewer cho: {tieu_de_vt}")
                except: pass
            
            prompt_anh = f"Professional high-tech banner, modern laptop screen with {tk_ve_tinh} software, 4k. ABSOLUTELY NO TEXT, NO LETTERS."
            try:
                _, img_url = ve_va_upload_anh(prompt_anh, tk_ve_tinh, tieu_de_vt)
            except:
                img_url = None
                
            if img_url:
                noi_dung_vt = f'<div style="text-align:center;"><img src="{img_url}" alt="{tieu_de_vt}"></div><br>' + noi_dung_vt

            # ==========================================
            # 🚀 BƯỚC C: ĐĂNG BÀI - XÀO NỘI DUNG RIÊNG CHO MỖI SITE
            # ==========================================
            sites_to_post = random.sample(danh_sach_5_site, 3) 
            links_vua_dang = [] 

            for site in sites_to_post:
                if status_text:
                    try: status_text.warning(f"🚀 Đang 'biến hóa' nội dung sạch cho: {site['name']}...")
                    except: pass
                
                # BỘ LUẬT THÉP ÉP AI KHÔNG ĐƯỢC CHẾ RÁC
                prompt_ai_rieng = f"""
                Bạn là Chuyên gia Review Công nghệ. Viết 1 bài Review hoàn toàn mới về "{tk_ve_tinh}".
                Đích đến: Đăng trên trang {site['name']}.
                Góc nhìn: {kich_ban['chi_tiet']}
                
                [LUẬT LẬP TRÌNH - BẮT BUỘC TUÂN THỦ 100%]:
                1. TUYỆT ĐỐI KHÔNG sinh ra thẻ <style>, KHÔNG viết CSS.
                2. KHÔNG bọc kết quả trong dấu ```html hay bất kỳ markdown nào. Trả về text HTML trần.
                3. BẮT BUỘC bọc Tiêu đề của bài trong đúng thẻ [TITLE] Tiêu đề ở đây [/TITLE]. Không chế ra thẻ khác.
                4. Chỉ dùng các thẻ HTML cơ bản: h2, h3, p, strong, ul, li.
                5. Chèn 1 link dẫn về bài gốc: <a href="{link_web_chinh}">xem tại đây</a>.
                """

                # 🟢 BỘ GIẢM XÓC: VÒNG LẶP CHỐNG LỖI 429 TỪ GOOGLE
                bai_viet_rieng = ""
                for lan_thu in range(3):
                    try:
                        res_rieng = client_ai.models.generate_content(model="gemini-2.5-flash", contents=prompt_ai_rieng)
                        bai_viet_rieng = res_rieng.text
                        break # Nếu AI trả lời mượt mà thì thoát vòng lặp
                    except Exception as e_ai:
                        if "429" in str(e_ai) or "RESOURCE_EXHAUSTED" in str(e_ai):
                            if status_text:
                                try: status_text.error(f"⚠️ Google AI đang nghẽn (Lỗi 429). Cho Bot nghỉ 15s rồi thử lại (Lần {lan_thu + 1}/3)...")
                                except: pass
                            time.sleep(15) # Ngủ 15s chờ Google hồi mana
                        else:
                            if status_text:
                                try: st.error(f"❌ Lỗi AI không xác định tại {site['name']}: {str(e_ai)}")
                                except: pass
                            break
                
                # Nếu thử 3 lần vẫn bị Google đá văng thì bỏ qua site này, đi tiếp site khác
                if not bai_viet_rieng:
                    continue

                try:
                    # 1. DỌN SẠCH RÁC MARKDOWN (Nếu AI vẫn ngoan cố)
                    bai_viet_rieng = bai_viet_rieng.replace('```html', '').replace('```', '').strip()
                    
                    # 2. TÁCH TIÊU ĐỀ AN TOÀN
                    t_match = re.search(r'\[TITLE\](.*?)\[/TITLE\]', bai_viet_rieng, re.IGNORECASE | re.DOTALL)
                    if t_match:
                        tieu_de_rieng = t_match.group(1).strip()
                        noi_dung_rieng = bai_viet_rieng.replace(t_match.group(0), '').strip()
                    else:
                        tieu_de_rieng = f"Review chi tiết {tk_ve_tinh}"
                        noi_dung_rieng = bai_viet_rieng
                        
                    # 3. CHÈN ẢNH VÀO NỘI DUNG (Dùng chung 1 ảnh đã vẽ)
                    if img_url:
                        noi_dung_rieng = f'<div style="text-align:center;"><img src="{img_url}" alt="{tieu_de_rieng}"></div><br>' + noi_dung_rieng

                    # 4. BẮT ĐẦU ĐĂNG BÀI
                    if site['type'] == 'blogger':
                        service_bg = get_blogger_service()
                        res = service_bg.posts().insert(blogId=site['id'], body={'title': tieu_de_rieng, 'content': noi_dung_rieng}).execute()
                        if res.get('url'): links_vua_dang.append(res.get('url'))

                    elif site['type'] == 'wp':
                        from wordpress_xmlrpc import Client, WordPressPost
                        from wordpress_xmlrpc.methods.posts import NewPost
                        client_wp = Client(site['url'], WP_VT_USER, WP_VT_PASS)
                        post = WordPressPost()
                        post.title, post.content, post.post_status = tieu_de_rieng, noi_dung_rieng, 'publish'
                        post_id = client_wp.call(NewPost(post))
                        links_vua_dang.append(f"{site['url'].replace('xmlrpc.php', '')}?p={post_id}")

                    elif site['type'] == 'tumblr':
                        import pytumblr
                        client_tb = pytumblr.TumblrRestClient(cons_key, cons_sec, oa_tok, oa_sec)
                        res_tb = client_tb.create_text(site['id'], state="published", title=tieu_de_rieng, body=noi_dung_rieng)
                        if 'id' in res_tb: links_vua_dang.append(f"https://{site['id']}.tumblr.com/post/{res_tb['id']}")
                
                except Exception as e_site:
                    if status_text:
                        try: st.error(f"❌ Lỗi đăng bài tại {site['name']}: {str(e_site)}")
                        except: pass
                    print(f"❌ Lỗi đăng bài tại {site['name']}: {str(e_site)}")
                
                # 🟢 BỘ GIẢM XÓC SỐ 2: Nghỉ ngơi trước khi viết cho site vệ tinh tiếp theo
                time.sleep(7)

            # 4. CẬP NHẬT SHEET & NHẬT KÝ LINK
            so_cu = int(str(row['Số bài Vệ tinh']).split('/')[0]) if '/' in str(row['Số bài Vệ tinh']) else 0
            so_moi = so_cu + 1
            idx_in_sheet = df[df['Từ khóa'] == tk_ve_tinh].index[0]
            row_num = int(idx_in_sheet) + 2
            
            try:
                worksheet.update_cell(row_num, df.columns.get_loc('Số bài Vệ tinh') + 1, f"{so_moi}/{max_satellite_posts}")

                if 'Link Vệ tinh' in df.columns:
                    chuoi_link = "\n".join(links_vua_dang)
                    noi_dung_cu = str(row.get('Link Vệ tinh', '')).strip()
                    nhat_ky = f"Lần {so_moi}:\n{chuoi_link}"
                    nhat_ky_full = f"{noi_dung_cu}\n---\n{nhat_ky}" if noi_dung_cu and noi_dung_cu != 'nan' else nhat_ky
                    worksheet.update_cell(row_num, df.columns.get_loc('Link Vệ tinh') + 1, nhat_ky_full)
            except Exception as e_sheet:
                print(f"Lỗi ghi Sheet: {e_sheet}")

            try: st.toast(f"✅ Đã bắn xong: {tk_ve_tinh}")
            except: pass
            print(f"✅ Đã bắn xong: {tk_ve_tinh}")

            # ==========================================
            # ☕ BƯỚC E: NGHỈ NGƠI CHỐNG SPAM (QUAN TRỌNG)
            # ==========================================
            if dem < so_bai_se_ban - 1:
                # Tính toán thời gian nghỉ ngẫu nhiên theo thanh slider anh kéo
                wait_sec = random.randint(sleep_time[0]*60, sleep_time[1]*60)
                for s in range(wait_sec, 0, -1):
                    phut = s // 60
                    giay = s % 60
                    if status_text:
                        try: status_text.warning(f"☕ Đã xong bài {tk_ve_tinh}. Nghỉ xả hơi: {phut}p {giay}s...")
                        except: pass
                    # Kiểm tra lại phanh khẩn cấp trong lúc đang ngủ (để sếp không phải đợi nó ngủ xong mới tắt được)
                    if os.path.exists("stop_vetinh.txt"):
                        break 
                    time.sleep(1)

        except Exception as e:
            try: st.error(f"❌ Lỗi hệ thống tại từ khóa {tk_ve_tinh}: {e}")
            except: pass
            print(f"❌ Lỗi hệ thống tại từ khóa {tk_ve_tinh}: {e}")

        if progress_bar:
            try: progress_bar.progress((dem + 1) / so_bai_se_ban)
            except: pass
    
    return True

# --- Hàm Review giữ nguyên ---
def xem_truoc_bai_ve_tinh(keyword, link_web_chinh, client_ai):
    # (Giữ nguyên như code cũ của anh)
    pass