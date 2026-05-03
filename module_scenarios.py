import re
import random


def phan_loai_kich_ban(tk_auto, nam_hien_tai, khach_hang_rd, dia_diem_rd):
    tk_lower = str(tk_auto).lower()

    # ==========================================
    # # ==========================================
    # 1. BỘ LỌC ĐA TẦNG
    # ==========================================
    kw_hardware = [
        "không lên hình",
        "kêu tít",
        "thay màn",
        "mực",
        "máy in",
        "sập nguồn",
        "chết",
        "mainboard",
        "bàn phím",
        "chuột",
        "ổ cứng",
        "ssd",
        "hdd",
        "ram",
        "vệ sinh",
        "không lên",
        "hư",
        "bảo trì",
        "pin",
        "sạc",
        "bản lề",
        "nóng",
        "quạt",
        "nâng cấp",
        "card",
        "vga",
        "màn hình xanh",
        "chập chờn",
        "sửa máy tính",
        "sửa laptop",
        "sửa pc",
    ]
    kw_premium = [
        "autocad",
        "3ds max",
        "revit",
        "inventor",
        "maya",
        "autodesk",
        "adobe",
        "photoshop",
        "illustrator",
        "premiere",
        "after effects",
        "audition",
        "lightroom",
        "incopy",
        "bridge",
        "indesign",
        "corel",
        "coreldraw",
        "office",
        "windows",
        "win 10",
        "win 11",
        "excel",
        "word",
        "powerpoint",
        "vray",
        "sketchup",
        "bản quyền",
        "camtasia",
        "lumion",
        "enscape",
        "corona",
        "diệt virus",
        "kaspersky",
        "crack",
        "active",
        "kích hoạt",
        "mở khóa",
        "mua key",
        "bán key",
        "key win",
        "key office",
    ]
    kw_free = [
        "unikey",
        "evkey",
        "vietkey",
        "zalo",
        "chrome",
        "cốc cốc",
        "pdf",
        "obs",
        "idm",
        "winrar",
        "zoom",
        "teamviewer",
        "ultraviewer",
        "tải",
        "download",
        "cài đặt phần mềm",
        "font",
        "driver",
        "telegram",
        "viber",
        "capcut",
        "trình duyệt",
        "cài win",
    ]
    kw_error = [
        "lỗi",
        "không được",
        "bắt",
        "khởi động",
        "reset",
        "fix",
        "stopped working",
        "mã lỗi",
        "không gõ được",
        "không mở được",
        "treo",
        "đơ",
        "giật",
        "lag",
        "chậm",
        "mất kết nối",
        "not responding",
        "virus",
        "mất dữ liệu",
        "chấm than vàng",
        "màn hình đen",
    ]

    # Bổ sung thêm "kinh nghiệm", "làm sao"
    kw_tip = [
        "cách",
        "mẹo",
        "thủ thuật",
        "hướng dẫn",
        "ẩn",
        "hiện",
        "tắt",
        "bật",
        "phím tắt",
        "chia ổ",
        "chỉnh",
        "tối ưu",
        "tăng tốc",
        "khôi phục",
        "lấy lại",
        "xóa",
        "gỡ",
        "phân vùng",
        "format",
        "dọn rác",
        "kinh nghiệm",
        "làm sao",
    ]

    # Bổ sung hàng loạt từ khóa Tư vấn / Review
    kw_news = [
        "tin tức",
        "top",
        "hiện nay",
        "khám phá",
        "siêu máy tính",
        "review",
        "đánh giá",
        "so sánh",
        "kiến thức",
        "tìm hiểu",
        "tổng hợp",
        "là gì",
        "tại sao",
        "có nên",
        "tốt không",
        "vs",
        "điện toán",
        "công nghệ",
        "các loại",
        "phân loại",
        "chọn mua",
        "tư vấn",
        "nên mua",
    ]
    kw_do_hoa = [
        "autocad",
        "3ds max",
        "revit",
        "inventor",
        "maya",
        "autodesk",
        "adobe",
        "photoshop",
        "illustrator",
        "premiere",
        "after effects",
        "audition",
        "lightroom",
        "incopy",
        "bridge",
        "indesign",
        "corel",
        "coreldraw",
    ]

    is_hardware = any(x in tk_lower for x in kw_hardware)
    is_premium = any(x in tk_lower for x in kw_premium)
    is_error = any(x in tk_lower for x in kw_error)
    is_free = any(x in tk_lower for x in kw_free)
    is_tip = any(x in tk_lower for x in kw_tip)
    is_news = any(x in tk_lower for x in kw_news)
    is_do_hoa = any(x in tk_lower for x in kw_do_hoa)

    # Ưu tiên phân loại: news/tip > error > free > premium > hardware
    if is_news or is_tip:
        is_hardware = False
        is_premium = False
        is_error = False

    if is_error:
        is_premium = False
        is_hardware = False

    if is_free:
        is_hardware = False

    is_qa = (
        any(
            x in tk_lower
            for x in [
                "giá",
                "bao nhiêu",
                "là gì",
                "tại sao",
                "có nên",
                "bảng giá",
                "mua ở đâu",
                "tốt không",
            ]
        )
        or "?" in tk_auto
    )

    nam_pb_match = re.search(r"\d{4}", tk_auto)
    nam_pb = int(nam_pb_match.group(0)) if nam_pb_match else 0

    # ==========================================
    # 2. XỬ LÝ HTML CẢNH BÁO CRACK (CHỈ DÀNH CHO ĐỒ HỌA)
    # ==========================================
    html_canh_bao_crack = ""
    kw_can_canh_bao_ban_quyen = kw_do_hoa + [
        "office",
        "windows",
        "win 10",
        "win 11",
        "key win",
        "key office",
        "crack",
        "active",
        "kích hoạt",
        "mở khóa",
        "mua key",
        "bán key",
    ]
    if is_do_hoa or any(x in tk_lower for x in kw_can_canh_bao_ban_quyen):
        html_canh_bao_crack = """
<div style="border: 1px dashed #d32f2f; padding: 15px; margin: 25px 0; background-color: #fff5f5; border-radius: 5px;">
<strong style="color: #d32f2f; font-size: 18px;">⚠️ LỜI KHUYÊN TỪ KỸ THUẬT VIÊN:</strong>
<ul style="margin-top: 10px; margin-bottom: 0;">
<li>Nhiều người dùng tải nhầm các bản cài đặt trôi nổi trên mạng bị cài cắm mã độc (Ransomware), dẫn đến nguy cơ mã hóa dữ liệu hoặc rò rỉ thông tin quan trọng.</li>
<li>Việc sử dụng công cụ "bẻ khóa" (Crack/Keygen) thường gây lỗi văng phần mềm, xung đột hệ thống và làm máy chậm, giật lag.</li>
<li>Để đảm bảo an toàn cho thiết bị và tiến độ công việc, <strong>Huỳnh Khang Computer không hỗ trợ cài đặt các phiên bản Crack.</strong></li>
<li>Nếu cần giải pháp ổn định hơn, hãy ưu tiên bản quyền chính hãng hoặc gói phù hợp nhu cầu để dùng lâu dài, update thuận tiện và ít phát sinh lỗi.</li>
</ul>
</div>
"""

    # ==========================================
    # 3. BẢNG GIÁ GỐC
    # ==========================================
    bang_gia_goc = f"""
    [BẢNG GIÁ DỊCH VỤ THAM KHẢO TẠI HUỲNH KHANG COMPUTER - NĂM {nam_hien_tai}]
    - Cài Hệ điều hành Windows (XP/7/8.1/10/11) cho PC & Laptop: Khoảng 150.000đ - 250.000đ
    - Cài đặt lại MacOS hoặc Cài Win 10/11 cho Macbook: Mức giá hiện tại 350.000đ / máy
    - Vệ sinh + tra keo tản nhiệt: 150.000đ - 250.000đ
    - Sửa Mainboard Laptop không lên nguồn: Dao động từ 480.000đ - 870.000đ
    - Nạp mực máy in: 120.000đ - 250.000đ
    - Phí kiểm tra tại nhà: 100.000đ.
    """

    vai_tro_ai = ""
    luat_zalo_cta = ""
    dinh_huong_mo_bai = ""
    loi_khuyen_chuyen_mon = ""
    gia_pm_chi_tiet = ""
    luat_schema = ""
    muc_tieu_do_dai = "1500-2000"
    luat_qa_strict = "- BÀI VIẾT HỎI ĐÁP (Q&A): Hãy trả lời TRỰC DIỆN." if is_qa else ""

    # 💥 BIẾN ĐIỀU KHIỂN ALERT BOX MẶC ĐỊNH DÀNH CHO CÁC BÀI LỖI / THỦ THUẬT
    luat_alert_box = """
    [PHẦN 6: ALERT BOX TỔNG KẾT BỆNH (CUỐI BÀI)]
    Cuối bài, BẮT BUỘC bọc kinh nghiệm thực chiến vào khối sau. KHÔNG dùng Markdown (*, **) bên trong khối này, CHỈ DÙNG thẻ HTML (<b>, <br>, <ul>, <li>).
    <div style="border: 2px dashed #d32f2f; padding: 20px; margin: 30px 0; background-color: #fff5f5; border-radius: 10px; line-height: 1.6;">
    <strong style="color: #d32f2f; font-size: 20px; display: block; margin-bottom: 15px;">💡 Mẹo từ Kỹ thuật viên Huỳnh Khang:</strong>
    <ul style="margin: 0; padding-left: 20px; color: #333;">
        <li style="margin-bottom: 10px;"><b>Phân tích bệnh:</b> [AI viết 1 dòng ngắn về nguyên nhân cốt lõi]</li>
        <li style="margin-bottom: 10px;"><b>Giải pháp nhanh:</b> [Các bước khắc phục, dùng <br> xuống dòng nếu cần]</li>
        <li style="margin-bottom: 0;"><b>Lưu ý an toàn:</b> [Lời khuyên về dữ liệu hoặc bản quyền]</li>
    </ul>
    <p style="margin-top: 15px; font-style: italic; color: #d32f2f; font-size: 14px;">* Lưu ý: Nếu làm theo các bước trên vẫn không được, hãy liên hệ Zalo 0325.636.239 để Khang hỗ trợ trực tiếp.</p>
    </div>
    """

    # 💥 LUẬT BÀI VIẾT LIÊN QUAN (ÁP DỤNG CHO TẤT CẢ BÀI)
    luat_related_posts = """
    [PHẦN 8: HỘP BÀI VIẾT LIÊN QUAN]
    🔴 LỆNH CẤM TUYỆT ĐỐI:
    - CHỈ tạo hộp bài viết liên quan KHI VÀ CHỈ KHI hệ thống đã cung cấp link trong [LINK DÀNH CHO HỘP BÀI LIÊN QUAN]
    - Nếu [LINK DÀNH CHO HỘP BÀI LIÊN QUAN] là TRỐNG hoặc không có, TUYỆT ĐỐI KHÔNG TẠO HỘP NÀY
    - KHÔNG TỰ BỊA LINK, KHÔNG TỰ TẠO URL, KHÔNG ĐOÁN TIÊU ĐỀ BÀI VIẾT
    - Hộp này CHỈ được tạo khi có link thực từ hệ thống

    Format hộp (CHỈ dùng khi có link từ hệ thống):
    <div style="border: 1px solid #e0e0e0; padding: 20px; margin: 30px 0; background-color: #f9f9f9; border-radius: 8px;">
    <h3 style="margin-top: 0; color: #1976d2;">📚 Bài viết liên quan</h3>
    <ul style="line-height: 1.8;">
        [Chỉ chèn các link đã được cung cấp trong [LINK DÀNH CHO HỘP BÀI LIÊN QUAN]]
    </ul>
    </div>
    """

    # 💥 LUẬT EXTERNAL LINKS (ÁP DỤNG CHO TẤT CẢ BÀI)
    luat_external_links = """
    [PHẦN 9: EXTERNAL LINKS - BẮT BUỘC]
    Trong nội dung bài viết, BẮT BUỘC chèn ĐÚNG 1 link external có authority cao:
    - Ưu tiên link đến trang chủ hãng lớn liên quan (Microsoft, Adobe, Autodesk, Intel, AMD, NVIDIA, Dell, HP, Lenovo, Apple, v.v.)
    - Nếu không có hãng lớn phù hợp, link đến Wikipedia về chủ đề/thực thể chính trong bài
    - CHỈ LINK ĐẾN ROOT DOMAIN (trang chủ), KHÔNG link đến sub-path cụ thể để tránh 404
    - Format BẮT BUỘC: <a href="[URL]" target="_blank" rel="noopener">[Anchor Text]</a>
    - KHÔNG dùng rel="nofollow" - link hãng lớn là DOFOLLOW
    - Đặt link tự nhiên trong ngữ cảnh, không gượng ép
    - CHỈ 1 LINK DUY NHẤT, không nhiều hơn

    Ví dụ ĐÚNG:
    - "Theo <a href="https://www.microsoft.com" target="_blank" rel="noopener">Microsoft</a>, Windows 11 yêu cầu..."
    - "Chip mới từ <a href="https://www.intel.com" target="_blank" rel="noopener">Intel</a> mang lại hiệu năng..."
    - "Về mặt kỹ thuật, <a href="https://vi.wikipedia.org/wiki/SSD" target="_blank" rel="noopener">ổ cứng SSD</a> hoạt động..."

    Ví dụ SAI (tránh):
    - Link có rel="nofollow" (SAI - phải là dofollow)
    - Link đến sub-path: https://www.microsoft.com/vi-vn/windows (có thể 404)
    - Nhiều hơn 1 link external trong bài
    """

    # ==========================================
    # 4. PHÂN NHÁNH KỊCH BẢN
    # ==========================================
    if is_hardware:
        vai_tro_ai = "Bạn là Huỳnh Khang - Kỹ thuật viên phần cứng với hơn 15 năm kinh nghiệm, đã xử lý hàng nghìn ca sửa máy tính tận nơi tại TP.HCM và khu vực lân cận."
        dinh_huong_mo_bai = f"Vào đề bằng một tình huống điển hình mà khách hàng ở {dia_diem_rd} thường gặp khi máy gặp sự cố tương tự. Phân tích đúng 'nỗi đau' như: máy chết không làm việc được, sợ mất dữ liệu."
        loi_khuyen_chuyen_mon = (
            "Khoanh vùng các nguyên nhân vật lý. Khuyên khách KHÔNG tự tháo lắp."
        )
        luat_zalo_cta = '5. CTA: BẮT BUỘC cuối mở bài chèn: "Cần hỗ trợ tận nơi, nhắn <a href="tel:+84325636239" target="_blank" rel="nofollow noopener">Zalo 0325.636.239</a> — Không sửa được không lấy tiền."'
        luat_schema = """
    [PHẦN 10: SCHEMA MARKUP JSON-LD - BẮT BUỘC CHO RICH RESULT 2026]
    Cuối bài (sau hộp bài viết liên quan), chèn đúng đoạn script này:
    <script type="application/ld+json">
    {"@context":"https://schema.org","@type":"HowTo","name":"[TIÊU ĐỀ CHÍNH XÁC CỦA BÀI]","description":"[META DESCRIPTION]","step":[{"@type":"HowToStep","name":"[Tên Bước 1]","text":"[Mô tả bước 1]"},{"@type":"HowToStep","name":"[Tên Bước 2]","text":"[Mô tả bước 2]"},{"@type":"HowToStep","name":"[Tên Bước 3]","text":"[Mô tả bước 3]"}],"author":{"@type":"Person","name":"Huỳnh Khang","url":"https://huynhkhang.com/about/"}}
    </script>
    🔴 LỆNH: Điền thông tin thực từ nội dung vào []. Tối thiểu 3 bước. KHÔNG để placeholder. TUYỆT ĐỐI KHÔNG SỬ DỤNG DẤU NGOẶC KÉP ("). Nếu cần nhấn mạnh hoặc trích dẫn, CHỈ ĐƯỢC DÙNG DẤU NGOẶC ĐƠN ('). Dấu ngoặc kép sẽ làm vỡ cấu trúc JSON!"""
        muc_tieu_do_dai = "1500-2000"

    elif is_error:
        vai_tro_ai = "Bạn là Huỳnh Khang - Chuyên gia sửa lỗi phần mềm và hệ thống máy tính với 8+ năm kinh nghiệm."
        dinh_huong_mo_bai = "Vào đề bằng sự thấu hiểu nỗi ức chế khi đang chạy deadline mà máy hoặc phần mềm báo lỗi. Không dọa nạt quá mức. Không kể chuyện đi sửa tận nhà."
        loi_khuyen_chuyen_mon = "Đi thẳng vào nguyên nhân, dấu hiệu nhận biết và cách sửa chi tiết từng bước. Ưu tiên giải pháp dễ làm trước, rõ ràng, ít rủi ro."

        # 💥 LOGIC ULTRAVIEWER CHỈ DÀNH CHO PHẦN MỀM (RANDOM HÓA TRÁNH SPAM SEO)
        kw_phan_mem_hang = [
            "autodesk",
            "adobe",
            "corel",
            "sketchup",
            "autocad",
            "3ds max",
            "revit",
            "maya",
            "photoshop",
            "illustrator",
            "premiere",
            "after effects",
            "lightroom",
            "office",
            "excel",
            "word",
        ]

        # Đặt biến link Zalo ra ngoài cho code gọn, dễ chỉnh sửa sau này
        zalo_link = '<a href="tel:+84325636239" target="_blank" rel="nofollow noopener">Zalo 0325.636.239</a>'

        if any(x in tk_lower for x in kw_phan_mem_hang):
            list_cta_phan_mem = [
                f'5. CTA: Cuối mở bài: "Làm theo vẫn không được, ném ID UltraViewer qua {zalo_link} — Khang xử lý nhanh gọn cho kịp tiến độ."',
                f'5. CTA: Cuối mở bài: "Đọc hướng dẫn thấy lằng nhằng quá thì cứ gửi ID UltraViewer vào {zalo_link}, Khang vào click vài phát là xong."',
                f'5. CTA: Cuối mở bài: "Anh em nào cài mãi vẫn văng lỗi, cứ quăng UltraViewer qua {zalo_link} nhé. Khang hỗ trợ xử lý dứt điểm luôn."',
                f'5. CTA: Cuối mở bài: "Fix lỗi phần mềm đôi khi hơi rắc rối, bí quá cứ nhắn {zalo_link} kèm UltraViewer, Khang sẽ vào xem giúp ạ."',
                f'5. CTA: Cuối mở bài: "Nếu đang cần xong việc gấp mà máy cứ báo lỗi, gửi ngay UltraViewer qua {zalo_link} để Khang nhảy vào hỗ trợ kịp thời."',
                f'5. CTA: Cuối mở bài: "Lỡ thao tác sai ở đâu thì đừng cố mò thêm dễ lỗi nặng hơn, cứ mở UltraViewer lên rồi nhắn {zalo_link}, Khang cứu nét ngay."',
                f'5. CTA: Cuối mở bài: "Trường hợp lỗi ẩn sâu do Win hoặc xung đột hệ thống, anh chị nhắn {zalo_link} cho Khang Ultra vào kiểm tra cho lẹ."',
                f'5. CTA: Cuối mở bài: "Thay vì tốn cả buổi mò mẫm bực mình, anh chị cứ nhắn {zalo_link}, Khang remote qua Ultra cài chuẩn luôn cho nhàn."',
                f'5. CTA: Cuối mở bài: "Phần mềm cứ báo lỗi hoài không cho xài? Chụp ngay màn hình gửi {zalo_link} kèm ID Ultra, Khang bắt bệnh và xử lý liền."',
                f'5. CTA: Cuối mở bài: "Sửa lỗi này nhiều khi đụng tới Registry khá nguy hiểm, ai không rành cứ nhắn {zalo_link} để Khang dùng UltraViewer hỗ trợ cho an toàn."',
                f'5. CTA: Cuối mở bài: "Xóa đi cài lại vẫn chứng nào tật nấy? Nhắn luôn ID Ultra vào {zalo_link}, Khang check lỗi hệ thống và fix trong 1 nốt nhạc."',
                f'5. CTA: Cuối mở bài: "Nếu không có thời gian vọc vạch sửa lỗi, anh chị nhắn thẳng ID UltraViewer sang {zalo_link} để Khang fix trực tiếp trên máy nhé."',
            ]
            luat_zalo_cta = random.choice(list_cta_phan_mem)

        else:
            list_cta_he_thong = [
                f'5. CTA: Cuối mở bài: "Nếu máy dính màn hình xanh hoặc sập nguồn, anh chị đừng tự tháo máy. Cứ gọi ngay {zalo_link}, Khang tư vấn phương án xử lý."',
                f'5. CTA: Cuối mở bài: "Lỗi phần cứng thì không thể UltraViewer được. Anh chị gọi trực tiếp hoặc nhắn {zalo_link} để Khang bắt bệnh chuẩn xác nhé."',
                f'5. CTA: Cuối mở bài: "Máy cứ reset liên tục hoặc đen thui màn hình, anh chị cầm điện thoại bấm luôn {zalo_link} cho Khang để được hỗ trợ nhanh nhất."',
                f'5. CTA: Cuối mở bài: "Nếu máy bị màn hình xanh, không khởi động được hoặc làm theo hướng dẫn không thành công, anh chị hãy gọi điện hoặc nhắn tin trực tiếp {zalo_link} để Khang hỗ trợ tư vấn và kiểm tra cụ thể."',
                f'5. CTA: Cuối mở bài: "Thao tác phần mềm không ăn thua, nghi do ổ cứng hoặc RAM thì anh em liên hệ {zalo_link}, Khang hướng dẫn cách kiểm tra phần cứng."',
                f'5. CTA: Cuối mở bài: "Vọc vạch một hồi mà máy tịt ngòi không lên hình luôn thì alo ngay {zalo_link} nhé, Khang hỗ trợ anh em tận tình."',
                f'5. CTA: Cuối mở bài: "Bệnh này có khả năng cao linh kiện đã xuống cấp. Cần bắt bệnh chính xác, anh chị cứ nhắn tình trạng qua {zalo_link} để Khang xem giúp."',
                f'5. CTA: Cuối mở bài: "Nếu không rành về tháo ráp máy, tuyệt đối đừng cố. Hãy gọi {zalo_link}, Khang tư vấn miễn phí trước khi anh chị quyết định mang đi sửa."',
                f'5. CTA: Cuối mở bài: "Đụng tới màn hình xanh thì muôn vàn nguyên nhân vật lý. Khách hàng nào bí quá cứ ới Khang qua {zalo_link} để tìm hướng giải quyết an toàn."',
                f'5. CTA: Cuối mở bài: "Sửa không được mà máy lại phát ra tiếng kêu tít tít lạ, anh chị nhắn ngay {zalo_link}. Nhớ quay lại cái video lỗi gửi Khang xem cho chuẩn bệnh."',
                f'5. CTA: Cuối mở bài: "Lỗi này hay chập chờn, để lâu dễ kéo theo hư hỏng mainboard. Anh chị gọi liền {zalo_link}, Khang tư vấn xem phần cứng có cứu được không."',
                f'5. CTA: Cuối mở bài: "Cứ dính tới màn hình xanh mã lạ hoặc chết nguồn đột ngột, gọi {zalo_link} cho lẹ. Khang sẽ chỉ anh em cách xử lý an toàn cho dữ liệu."',
            ]
            luat_zalo_cta = random.choice(list_cta_he_thong)

        luat_schema = """
    [PHẦN 10: SCHEMA MARKUP JSON-LD - BẮT BUỘC CHO RICH RESULT 2026]
    Cuối bài (sau hộp bài viết liên quan), chèn:
    <script type="application/ld+json">
    {"@context":"https://schema.org","@type":"TechArticle","headline":"[TIÊU ĐỀ BÀI]","description":"[META DESCRIPTION]","author":{"@type":"Person","name":"Huỳnh Khang","url":"https://huynhkhang.com/about/"},"datePublished":"[YYYY-MM-DD]","articleBody":"[Tóm tắt ngắn gọn nội dung bài viết]"}
    </script>
    🔴 LỆNH: Điền thông tin thực. KHÔNG để placeholder. TUYỆT ĐỐI KHÔNG SỬ DỤNG DẤU NGOẶC KÉP ("). Nếu cần nhấn mạnh hoặc trích dẫn, CHỈ ĐƯỢC DÙNG DẤU NGOẶC ĐƠN ('). Dấu ngoặc kép sẽ làm vỡ cấu trúc JSON!"""
        muc_tieu_do_dai = "1200-1500"

    elif is_premium or any(x in tk_lower for x in ["office", "windows"]):
        vai_tro_ai = "Bạn là Huỳnh Khang - Đơn vị tư vấn bản quyền phần mềm và hỗ trợ cài đặt 8+ năm tại TP.HCM, chuyên Autodesk, Adobe, Microsoft và các bộ công cụ làm việc phổ biến."
        dinh_huong_mo_bai = f"Vào đề bằng tầm quan trọng của việc dùng phần mềm ổn định, đúng nguồn và ít lỗi vặt để làm việc kịp tiến độ, gắn với một tình huống điển hình của khách hàng ở {dia_diem_rd}."
        luat_zalo_cta = '5. CTA: Chèn <a href="tel:+84325636239" target="_blank" rel="nofollow noopener">Zalo 0325.636.239</a> với lời mời dạng "hỗ trợ ạ", "trợ giúp", TUYỆT ĐỐI KHÔNG dùng từ "miễn phí", "cho", "tặng".'
        luat_schema = """
    [PHẦN 10: SCHEMA MARKUP JSON-LD - BẮT BUỘC CHO RICH RESULT 2026]
    Cuối bài (sau hộp bài viết liên quan), chèn:
    <script type="application/ld+json">
    {"@context":"https://schema.org","@type":"Service","serviceType":"Dịch vụ phần mềm","provider":{"@type":"LocalBusiness","name":"Huỳnh Khang Computer","url":"https://huynhkhang.com"},"description":"[MÔ TẢ DỊCH VỤ]","offers":{"@type":"Offer","priceCurrency":"VND","price":"[GIÁ]"}}
    </script>
    🔴 LỆNH: Điền thông tin thực về dịch vụ phần mềm. KHÔNG để placeholder. TUYỆT ĐỐI KHÔNG SỬ DỤNG DẤU NGOẶC KÉP ("). Nếu cần nhấn mạnh hoặc trích dẫn, CHỈ ĐƯỢC DÙNG DẤU NGOẶC ĐƠN ('). Dấu ngoặc kép sẽ làm vỡ cấu trúc JSON!"""
        muc_tieu_do_dai = "1200-1800"
        if any(x in tk_lower for x in ["autodesk", "autocad"]):
            gia_pm_chi_tiet = "- Giá bản quyền Autodesk Edu: Từ 470.000đ/Năm."
            loi_khuyen_chuyen_mon = "Chỉ cài Autodesk 2018 trở lên. Tư vấn gói Edu."
        elif any(x in tk_lower for x in ["adobe"]):
            gia_pm_chi_tiet = "- Giá Adobe Full App: Khoảng 190.000đ/Tháng."
            loi_khuyen_chuyen_mon = "Nhắc khách Adobe cần Win 10 22H2."
        elif any(x in tk_lower for x in ["windows", "office", "excel", "word"]):
            gia_pm_chi_tiet = "- Giá Key Win/Office: Khoảng 270.000đ."
            loi_khuyen_chuyen_mon = "Tư vấn Key bản quyền chính hãng vĩnh viễn."

    elif is_free:
        vai_tro_ai = "Bạn là Huỳnh Khang - Chuyên gia IT 8+ năm, chuyên hướng dẫn tải phần mềm đúng nguồn và ưu tiên an toàn cho người dùng phổ thông lẫn dân văn phòng."
        dinh_huong_mo_bai = "Vào đề bằng thực trạng nhiều người tải nhầm link rác chứa virus làm chậm máy, đánh cắp thông tin."
        loi_khuyen_chuyen_mon = "Hướng dẫn tải đúng trang chủ, cảnh báo lừa đảo."
        luat_zalo_cta = '5. CTA: KHÔNG BÁN HÀNG. Để lại <a href="tel:+84325636239" target="_blank" rel="nofollow noopener">Zalo 0325.636.239</a> nếu cần hỗ trợ tải và cài đặt qua UltraViewer.'
        luat_schema = """
    [PHẦN 10: SCHEMA MARKUP JSON-LD - BẮT BUỘC CHO RICH RESULT 2026]
    Cuối bài (sau hộp bài viết liên quan), chèn:
    <script type="application/ld+json">
    {"@context":"https://schema.org","@type":"HowTo","name":"[TIÊU ĐỀ BÀI]","description":"[META DESCRIPTION]","step":[{"@type":"HowToStep","name":"[Bước 1]","text":"[Mô tả]"},{"@type":"HowToStep","name":"[Bước 2]","text":"[Mô tả]"},{"@type":"HowToStep","name":"[Bước 3]","text":"[Mô tả]"}],"author":{"@type":"Person","name":"Huỳnh Khang","url":"https://huynhkhang.com/about/"}}
    </script>
    🔴 Điền thông tin thực. KHÔNG để placeholder. TUYỆT ĐỐI KHÔNG SỬ DỤNG DẤU NGOẶC KÉP ("). Nếu cần nhấn mạnh hoặc trích dẫn, CHỈ ĐƯỢC DÙNG DẤU NGOẶC ĐƠN ('). Dấu ngoặc kép sẽ làm vỡ cấu trúc JSON!"""
        muc_tieu_do_dai = "1200-1800"

    elif is_tip:
        vai_tro_ai = "Bạn là Huỳnh Khang - Chuyên gia IT 8+ năm, chuyên chia sẻ mẹo và thủ thuật máy tính thực tế, dễ áp dụng cho người dùng văn phòng và người dùng phổ thông."
        dinh_huong_mo_bai = "Vào đề nhanh bằng tình huống quen thuộc của người dùng cần thực hiện thao tác này. KHÔNG kể chuyện đi sửa máy."
        loi_khuyen_chuyen_mon = "Hướng dẫn từng bước click rõ ràng, dùng ngôn ngữ bình dân ('Nhấn chuột phải', 'Chọn Settings'). Ưu tiên mô tả vị trí nút bấm cụ thể."
        luat_zalo_cta = "5. CTA: 🔴 LỆNH CẤM: TUYỆT ĐỐI KHÔNG CHÈN SỐ ĐIỆN THOẠI HAY ZALO VÀO MỞ BÀI. Đây là bài chia sẻ kiến thức."
        luat_alert_box = """
        [PHẦN 6: TỔNG KẾT BÀI VIẾT]
        Viết một đoạn tổng kết ngắn gọn về các bước đã hướng dẫn. 🔴 LỆNH CẤM: TUYỆT ĐỐI KHÔNG tạo khối Alert Box "Mẹo từ Kỹ thuật viên", "Phân tích bệnh" hay để lại số Zalo, vì đây là bài hướng dẫn thủ thuật miễn phí, không phải dịch vụ sửa chữa.
        """
        luat_schema = """
    [PHẦN 10: SCHEMA MARKUP JSON-LD - BẮT BUỘC CHO RICH RESULT 2026]
    Cuối bài (sau hộp bài viết liên quan), chèn:
    <script type="application/ld+json">
    {"@context":"https://schema.org","@type":"HowTo","name":"[TIÊU ĐỀ BÀI]","description":"[META DESCRIPTION]","step":[{"@type":"HowToStep","name":"[Bước 1]","text":"[Mô tả]"},{"@type":"HowToStep","name":"[Bước 2]","text":"[Mô tả]"},{"@type":"HowToStep","name":"[Bước 3]","text":"[Mô tả]"}],"author":{"@type":"Person","name":"Huỳnh Khang","url":"https://huynhkhang.com/about/"}}
    </script>
    🔴 Điền thông tin thực. KHÔNG để placeholder. TUYỆT ĐỐI KHÔNG SỬ DỤNG DẤU NGOẶC KÉP ("). Nếu cần nhấn mạnh hoặc trích dẫn, CHỈ ĐƯỢC DÙNG DẤU NGOẶC ĐƠN ('). Dấu ngoặc kép sẽ làm vỡ cấu trúc JSON!"""
        muc_tieu_do_dai = "1200-1800"

    # 💥 NHÁNH TIN TỨC: TẮT HOÀN TOÀN CÁC LỆNH SỬA CHỮA VÀ BẢNG BỆNH
    elif is_news:
        vai_tro_ai = "Bạn là Huỳnh Khang - Chuyên gia công nghệ 8+ năm, đam mê cập nhật và phân tích tin tức IT theo góc nhìn thực tế, dễ hiểu và có ích cho người đọc phổ thông lẫn dân kỹ thuật."
        dinh_huong_mo_bai = "Vào đề một cách lôi cuốn, khơi gợi sự tò mò của người đọc về chủ đề bài viết. Trình bày khách quan, chuyên nghiệp."
        loi_khuyen_chuyen_mon = "Phân tích đa chiều, đưa ra góc nhìn chuyên sâu, tổng hợp thông tin và giải thích dễ hiểu nhất cho độc giả."
        luat_zalo_cta = "5. CTA: 🔴 LỆNH CẤM: TUYỆT ĐỐI KHÔNG CHÈN SỐ ĐIỆN THOẠI HAY ULTRAVIEWER VÀO MỞ BÀI."
        luat_alert_box = """
        [PHẦN 6: TỔNG KẾT BÀI VIẾT]
        Viết một đoạn tổng kết ngắn gọn. 🔴 LỆNH CẤM: TUYỆT ĐỐI KHÔNG tạo khối Alert Box "Mẹo từ Kỹ thuật viên", "Phân tích bệnh" hay để lại số Zalo, vì đây là bài viết chia sẻ kiến thức, không phải bài sửa chữa máy tính.
        """
        luat_schema = """
    [PHẦN 10: SCHEMA MARKUP JSON-LD - BẮT BUỘC CHO RICH RESULT 2026]
    Cuối bài (sau hộp bài viết liên quan), chèn:
    <script type="application/ld+json">
    {"@context":"https://schema.org","@type":"Article","headline":"[TIÊU ĐỀ BÀI]","description":"[META DESCRIPTION]","author":{"@type":"Person","name":"Huỳnh Khang","url":"https://huynhkhang.com/about/"},"datePublished":"[YYYY-MM-DD]","articleBody":"[Tóm tắt ngắn gọn nội dung bài viết]"}
    </script>
    🔴 Copy chính xác thông tin từ bài viết. KHÔNG để placeholder. TUYỆT ĐỐI KHÔNG SỬ DỤNG DẤU NGOẶC KÉP ("). Nếu cần nhấn mạnh hoặc trích dẫn, CHỈ ĐƯỢC DÙNG DẤU NGOẶC ĐƠN ('). Dấu ngoặc kép sẽ làm vỡ cấu trúc JSON!"""
        muc_tieu_do_dai = "2000-2500"

    else:
        vai_tro_ai = "Bạn là Huỳnh Khang - Chuyên gia IT 8+ năm, thấu hiểu mọi rắc rối vặt vãnh của dân văn phòng và người dùng máy tính hàng ngày."
        dinh_huong_mo_bai = "💥 BẮT BUỘC VÀO ĐỀ TỰ NHIÊN: Đánh trúng 'nỗi đau' thực tế của dân văn phòng. KHÔNG bịa chuyện đi sửa chữa lấy tiền."
        loi_khuyen_chuyen_mon = "HƯỚNG DẪN: Dùng ngôn ngữ cực bình dân ('Nhấn chuột phải', 'Chọn Settings')."
        luat_zalo_cta = '5. CTA: KHÔNG THU TIỀN. Cuối mở bài: "Thao tác mãi không được, nhắn <a href="tel:+84325636239" target="_blank" rel="nofollow noopener">Zalo 0325.636.239</a> — Khang UltraViewer hỗ trợ ạ."'
        luat_schema = ""
        muc_tieu_do_dai = "1200-1500"

    bang_gia_huynh_khang = bang_gia_goc + "\n" + gia_pm_chi_tiet

    return {
        "vai_tro_ai": vai_tro_ai,
        "dinh_huong_mo_bai": dinh_huong_mo_bai,
        "loi_khuyen_chuyen_mon": loi_khuyen_chuyen_mon,
        "luat_zalo_cta": luat_zalo_cta,
        "luat_qa_strict": luat_qa_strict,
        "bang_gia_huynh_khang": bang_gia_huynh_khang,
        "html_canh_bao_crack": html_canh_bao_crack,
        "luat_alert_box": luat_alert_box,
        "luat_related_posts": luat_related_posts,
        "luat_external_links": luat_external_links,
        "luat_schema": luat_schema,
        "muc_tieu_do_dai": muc_tieu_do_dai,
    }
