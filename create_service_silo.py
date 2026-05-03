"""
Script tạo cấu trúc URL Silo cho dịch vụ Local SEO
Cấu trúc: Danh mục (Category) làm trang cha → Trang địa phương làm trang con
Ví dụ: /sua-may-tinh/ (cha) → /sua-may-tinh/sua-may-tinh-quan-1/ (con)
"""

import sys
import requests
import time
from datetime import datetime

# Fix encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from my_config import WP_API_URL, WP_USER, WP_APP_PASS, client
from module_prompts import tao_prompt_bai_viet
from module_scenarios import phan_loai_kich_ban
from module_content import sinh_bai_viet

# =========================================================
# CẤU HÌNH DỊCH VỤ VÀ ĐỊA PHƯƠNG
# =========================================================

# Danh sách dịch vụ (sử dụng slug danh mục hiện có)
SERVICES = [
    {
        "name": "Sửa Máy Tính",
        "slug": "sua-may-tinh",
        "category_id": None,  # Sẽ tự động lấy từ API
        "description": "Dịch vụ sửa chữa máy tính tận nơi tại TP.HCM"
    },
    {
        "name": "Sửa Laptop",
        "slug": "sua-laptop",
        "category_id": None,
        "description": "Dịch vụ sửa chữa laptop tận nơi tại TP.HCM"
    },
    {
        "name": "Sửa Máy In",
        "slug": "sua-may-in",
        "category_id": None,
        "description": "Dịch vụ sửa chữa máy in tận nơi tại TP.HCM"
    },
    {
        "name": "Vệ Sinh Laptop",
        "slug": "ve-sinh-laptop",
        "category_id": None,
        "description": "Dịch vụ vệ sinh laptop chuyên nghiệp tại TP.HCM"
    }
]

# Danh sách địa phương TP.HCM (22 quận/huyện)
LOCATIONS = [
    {"name": "Quận 1", "slug": "quan-1"},
    {"name": "Quận 2", "slug": "quan-2"},
    {"name": "Quận 3", "slug": "quan-3"},
    {"name": "Quận 4", "slug": "quan-4"},
    {"name": "Quận 5", "slug": "quan-5"},
    {"name": "Quận 6", "slug": "quan-6"},
    {"name": "Quận 7", "slug": "quan-7"},
    {"name": "Quận 8", "slug": "quan-8"},
    {"name": "Quận 9", "slug": "quan-9"},
    {"name": "Quận 10", "slug": "quan-10"},
    {"name": "Quận 11", "slug": "quan-11"},
    {"name": "Quận 12", "slug": "quan-12"},
    {"name": "Thủ Đức", "slug": "thu-duc"},
    {"name": "Bình Thạnh", "slug": "binh-thanh"},
    {"name": "Tân Bình", "slug": "tan-binh"},
    {"name": "Tân Phú", "slug": "tan-phu"},
    {"name": "Phú Nhuận", "slug": "phu-nhuan"},
    {"name": "Gò Vấp", "slug": "go-vap"},
    {"name": "Bình Tân", "slug": "binh-tan"},
    {"name": "Hóc Môn", "slug": "hoc-mon"},
    {"name": "Củ Chi", "slug": "cu-chi"},
    {"name": "Nhà Bè", "slug": "nha-be"},
]

# =========================================================
# HÀM LẤY CATEGORY ID TỪ SLUG
# =========================================================

def get_category_by_slug(slug):
    """Lấy thông tin category từ slug"""
    try:
        url = f"{WP_API_URL}/categories"
        params = {"slug": slug, "per_page": 1}
        response = requests.get(url, params=params, auth=(WP_USER, WP_APP_PASS), timeout=30)

        if response.status_code == 200:
            categories = response.json()
            if categories:
                return categories[0]
        return None
    except Exception as e:
        print(f"Lỗi khi lấy category {slug}: {e}")
        return None

# =========================================================
# HÀM TẠO TRANG CHA (NẾU CHƯA CÓ)
# =========================================================

def create_or_get_parent_page(service):
    """Tạo hoặc lấy trang cha cho dịch vụ"""

    # Kiểm tra xem trang đã tồn tại chưa
    try:
        url = f"{WP_API_URL}/pages"
        params = {"slug": service['slug'], "per_page": 1}
        response = requests.get(url, params=params, auth=(WP_USER, WP_APP_PASS), timeout=30)

        if response.status_code == 200:
            pages = response.json()
            if pages:
                print(f"✅ Trang cha '{service['name']}' đã tồn tại (ID: {pages[0]['id']})")
                return pages[0]['id'], pages[0]['link']
    except Exception as e:
        print(f"Lỗi khi kiểm tra trang: {e}")

    # Nếu chưa có, tạo mới
    print(f"🔨 Đang tạo trang cha: {service['name']}...")

    # Tạo nội dung cho trang cha
    title = f"{service['name']} Tận Nơi Tại TP.HCM - Huỳnh Khang Computer"

    content = f"""
<div class="hero-section" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 60px 20px; text-align: center; color: white; border-radius: 10px; margin-bottom: 40px;">
    <h1 style="font-size: 2.5em; margin-bottom: 20px;">{service['name']} Tận Nơi Tại TP.HCM</h1>
    <p style="font-size: 1.2em; margin-bottom: 30px;">Dịch vụ chuyên nghiệp - Tận tâm - Uy tín - Bảo hành dài hạn</p>
    <a href="tel:0325636239" style="background: #ff6b6b; color: white; padding: 15px 40px; border-radius: 50px; text-decoration: none; font-size: 1.1em; font-weight: bold;">📞 GỌI NGAY: 0325.636.239</a>
</div>

<div class="trust-signals" style="background: #f8f9fa; padding: 40px 20px; border-radius: 10px; margin-bottom: 40px;">
    <h2 style="text-align: center; margin-bottom: 30px;">💎 Cam Kết Dịch Vụ</h2>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px;">
        <div style="text-align: center; padding: 20px;">
            <div style="font-size: 3em;">⚡</div>
            <h3>Nhanh Chóng</h3>
            <p>Có mặt trong 30-60 phút tại TP.HCM</p>
        </div>
        <div style="text-align: center; padding: 20px;">
            <div style="font-size: 3em;">💰</div>
            <h3>Giá Cả Minh Bạch</h3>
            <p>Báo giá trước - Không phát sinh</p>
        </div>
        <div style="text-align: center; padding: 20px;">
            <div style="font-size: 3em;">🛡️</div>
            <h3>Bảo Hành Dài</h3>
            <p>Bảo hành 3-12 tháng tùy dịch vụ</p>
        </div>
        <div style="text-align: center; padding: 20px;">
            <div style="font-size: 3em;">👨‍💻</div>
            <h3>Kỹ Thuật Giỏi</h3>
            <p>15+ năm kinh nghiệm thực chiến</p>
        </div>
    </div>
</div>

<div class="service-areas" style="margin-bottom: 40px;">
    <h2 style="text-align: center; margin-bottom: 30px;">📍 Khu Vực Phục Vụ</h2>
    <p style="text-align: center; font-size: 1.1em; margin-bottom: 20px;">Huỳnh Khang Computer phục vụ tận nơi tại tất cả các quận/huyện thuộc TP.HCM:</p>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 30px;">
        <!-- Danh sách địa phương sẽ được chèn tự động -->
    </div>
</div>

<div class="cta-section" style="background: #fff3cd; padding: 40px 20px; border-radius: 10px; text-align: center; border-left: 5px solid #ffc107;">
    <h2 style="margin-bottom: 20px;">🚀 Cần Hỗ Trợ Ngay?</h2>
    <p style="font-size: 1.1em; margin-bottom: 20px;">Liên hệ Huỳnh Khang Computer để được tư vấn và báo giá miễn phí!</p>
    <div style="display: flex; gap: 20px; justify-content: center; flex-wrap: wrap;">
        <a href="tel:0325636239" style="background: #28a745; color: white; padding: 15px 30px; border-radius: 5px; text-decoration: none; font-weight: bold;">📞 Gọi: 0325.636.239</a>
        <a href="https://zalo.me/0325636239" style="background: #0068ff; color: white; padding: 15px 30px; border-radius: 5px; text-decoration: none; font-weight: bold;">💬 Chat Zalo</a>
    </div>
</div>
"""

    try:
        data = {
            "title": title,
            "content": content,
            "slug": service['slug'],
            "status": "publish",
            "meta": {
                "description": service['description']
            }
        }

        response = requests.post(
            f"{WP_API_URL}/pages",
            json=data,
            auth=(WP_USER, WP_APP_PASS),
            timeout=60
        )

        if response.status_code == 201:
            page_data = response.json()
            print(f"✅ Đã tạo trang cha: {page_data['link']}")
            return page_data['id'], page_data['link']
        else:
            print(f"❌ Lỗi tạo trang cha: {response.status_code} - {response.text}")
            return None, None

    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return None, None

# =========================================================
# HÀM TẠO NỘI DUNG TRANG CON BẰNG AI
# =========================================================

def generate_child_page_content(service_name, location_name, parent_url):
    """Tạo nội dung trang con bằng AI với prompt SEO 2026"""

    tu_khoa = f"{service_name} {location_name} tận nơi"
    nam_hien_tai = datetime.now().year

    # Phân loại kịch bản
    config_kich_ban = phan_loai_kich_ban(tu_khoa, nam_hien_tai, "khách hàng", location_name)

    # Tạo outline đơn giản
    outline = f"""
[TITLE] {service_name} {location_name} Tận Nơi - Nhanh Chóng - Uy Tín
[META] Dịch vụ {service_name.lower()} tận nơi tại {location_name}, TP.HCM. Kỹ thuật viên 15+ năm kinh nghiệm. Cam kết nhanh 30-60 phút. Gọi ngay 0325.636.239!

## Tại sao nên chọn dịch vụ {service_name.lower()} tại {location_name}?

## Quy trình {service_name.lower()} chuyên nghiệp

## Bảng giá dịch vụ {service_name.lower()} tại {location_name}

## Cam kết của Huỳnh Khang Computer

## Câu hỏi thường gặp
"""

    # Link instruction - chèn link về trang cha
    link_instruction = f"""
[LINK DỊCH VỤ CHÍNH (BẮT BUỘC CHÈN Ở CUỐI BÀI)]:
Xem thêm: <a href="{parent_url}">{service_name} tại các quận khác tại TP.HCM</a>
"""

    def cap_nhat_trang_thai(msg):
        print(f"   {msg}")

    # Gọi hàm sinh bài viết
    ok, content = sinh_bai_viet(
        tk_auto=tu_khoa,
        tieu_de_seo_auto=f"{service_name} {location_name} Tận Nơi - Huỳnh Khang Computer",
        short_slug_auto=f"{service_name.lower().replace(' ', '-')}-{location_name.lower().replace(' ', '-')}",
        link_ins_auto=link_instruction,
        outline_auto=outline,
        nam_hien_tai=nam_hien_tai,
        khach_hang_mau=f"khách hàng tại {location_name}",
        dia_diem_rd=location_name,
        lenh_tim_kiem_ai="",
        cap_nhat_trang_thai_func=cap_nhat_trang_thai
    )

    if ok:
        return content
    else:
        print(f"   ⚠️ Lỗi AI: {content}")
        return None

# =========================================================
# HÀM TẠO TRANG CON
# =========================================================

def create_child_page(service, location, parent_id, parent_url):
    """Tạo trang con cho địa phương cụ thể"""

    child_slug = f"{service['slug']}-{location['slug']}"

    # Kiểm tra xem trang đã tồn tại chưa
    try:
        url = f"{WP_API_URL}/pages"
        params = {"slug": child_slug, "per_page": 1}
        response = requests.get(url, params=params, auth=(WP_USER, WP_APP_PASS), timeout=30)

        if response.status_code == 200:
            pages = response.json()
            if pages:
                print(f"   ⏭️  Trang '{location['name']}' đã tồn tại, bỏ qua")
                return True
    except Exception as e:
        print(f"   ⚠️ Lỗi kiểm tra: {e}")

    print(f"   🎨 Đang tạo nội dung AI cho {location['name']}...")

    # Tạo nội dung bằng AI
    content = generate_child_page_content(service['name'], location['name'], parent_url)

    if not content:
        print(f"   ❌ Không thể tạo nội dung cho {location['name']}")
        return False

    # Tạo trang WordPress
    title = f"{service['name']} {location['name']} Tận Nơi - Huỳnh Khang Computer"

    try:
        data = {
            "title": title,
            "content": content,
            "slug": child_slug,
            "parent": parent_id,  # ⭐ QUAN TRỌNG: Gán parent
            "status": "publish",
            "meta": {
                "description": f"Dịch vụ {service['name'].lower()} tận nơi tại {location['name']}, TP.HCM. Nhanh chóng - Uy tín - Bảo hành dài hạn. Gọi ngay 0325.636.239!"
            }
        }

        response = requests.post(
            f"{WP_API_URL}/pages",
            json=data,
            auth=(WP_USER, WP_APP_PASS),
            timeout=120
        )

        if response.status_code == 201:
            page_data = response.json()
            print(f"   ✅ Đã tạo: {page_data['link']}")
            return True
        else:
            print(f"   ❌ Lỗi: {response.status_code} - {response.text[:200]}")
            return False

    except Exception as e:
        print(f"   ❌ Lỗi: {e}")
        return False

# =========================================================
# HÀM CHÍNH
# =========================================================

def main():
    print("="*70)
    print("TẠO CẤU TRÚC URL SILO CHO DỊCH VỤ LOCAL SEO")
    print("="*70)
    print()

    # Lấy category ID cho các dịch vụ
    print("📋 Bước 1: Lấy thông tin danh mục hiện có...")
    for service in SERVICES:
        category = get_category_by_slug(service['slug'])
        if category:
            service['category_id'] = category['id']
            print(f"   ✅ {service['name']}: Category ID = {category['id']}")
        else:
            print(f"   ⚠️ {service['name']}: Không tìm thấy category '{service['slug']}'")
    print()

    # Tạo trang cha và trang con
    for service in SERVICES:
        print(f"🔨 Đang xử lý dịch vụ: {service['name']}")
        print("-"*70)

        # Tạo hoặc lấy trang cha
        parent_id, parent_url = create_or_get_parent_page(service)

        if not parent_id:
            print(f"❌ Không thể tạo trang cha cho {service['name']}, bỏ qua dịch vụ này")
            print()
            continue

        # Tạo các trang con
        print(f"\n📍 Đang tạo trang con cho {len(LOCATIONS)} địa phương...")
        success_count = 0

        for i, location in enumerate(LOCATIONS, 1):
            print(f"\n   [{i}/{len(LOCATIONS)}] {location['name']}:")

            if create_child_page(service, location, parent_id, parent_url):
                success_count += 1

            # Nghỉ giữa các request để tránh quá tải
            if i < len(LOCATIONS):
                time.sleep(3)

        print(f"\n✅ Hoàn thành {service['name']}: {success_count}/{len(LOCATIONS)} trang")
        print("="*70)
        print()

    print("="*70)
    print("🎉 HOÀN TẤT TẠO CẤU TRÚC URL SILO!")
    print("="*70)
    print()
    print("📊 Tổng kết:")
    print(f"   - Số dịch vụ: {len(SERVICES)}")
    print(f"   - Số địa phương: {len(LOCATIONS)}")
    print(f"   - Tổng số trang dự kiến: {len(SERVICES) * (1 + len(LOCATIONS))}")
    print()

if __name__ == "__main__":
    main()
