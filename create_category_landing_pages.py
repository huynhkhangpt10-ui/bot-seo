"""
Script tạo Landing Page (Hub) cho mỗi danh mục dịch vụ
Các bài viết có category tương ứng sẽ tự động hiển thị trên trang này
"""

import sys
import requests
import time

# Fix encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from my_config import WP_POSTS_URL, WP_USER, WP_APP_PASS

# Tạo base API URL từ WP_POSTS_URL
WP_API_URL = WP_POSTS_URL.rsplit('/', 1)[0]  # https://huynhkhang.com/wp-json/wp/v2

# =========================================================
# CẤU HÌNH DANH MỤC CẦN TẠO LANDING PAGE
# =========================================================

CATEGORIES = [
    {
        "name": "Sửa Máy Tính",
        "slug": "sua-may-tinh",
        "description": "Dịch vụ sửa chữa máy tính tận nơi tại TP.HCM",
        "icon": "💻",
        "services": [
            "Sửa mainboard, nguồn, card màn hình",
            "Khắc phục lỗi không lên nguồn, không hiển thị",
            "Thay thế linh kiện hư hỏng",
            "Vệ sinh, bảo dưỡng định kỳ"
        ],
        "price_range": "150.000₫ - 500.000₫"
    },
    {
        "name": "Sửa Laptop",
        "slug": "sua-laptop",
        "description": "Dịch vụ sửa chữa laptop tận nơi tại TP.HCM",
        "icon": "💼",
        "services": [
            "Sửa laptop không lên nguồn, không sạc pin",
            "Thay màn hình, bàn phím, pin laptop",
            "Vệ sinh tản nhiệt, thay keo tản nhiệt",
            "Nâng cấp RAM, SSD cho laptop"
        ],
        "price_range": "200.000₫ - 800.000₫"
    },
    {
        "name": "Sửa Máy In",
        "slug": "sua-may-in",
        "description": "Dịch vụ sửa chữa máy in tận nơi tại TP.HCM",
        "icon": "🖨️",
        "services": [
            "Sửa máy in không nhận lệnh, kẹt giấy",
            "Thay đầu phun, trống từ, lô sấy",
            "Vệ sinh máy in, bảo dưỡng định kỳ",
            "Nạp mực, reset chip máy in"
        ],
        "price_range": "100.000₫ - 400.000₫"
    },
    {
        "name": "Vệ Sinh Laptop",
        "slug": "ve-sinh-laptop",
        "description": "Dịch vụ vệ sinh laptop chuyên nghiệp tại TP.HCM",
        "icon": "🧹",
        "services": [
            "Vệ sinh tản nhiệt, quạt tản nhiệt",
            "Thay keo tản nhiệt chất lượng cao",
            "Vệ sinh bàn phím, màn hình",
            "Kiểm tra và bảo dưỡng toàn diện"
        ],
        "price_range": "150.000₫ - 300.000₫"
    },
    {
        "name": "Cài Win",
        "slug": "cai-win",
        "description": "Dịch vụ cài đặt Windows tận nơi tại TP.HCM",
        "icon": "🪟",
        "services": [
            "Cài Windows 11, 10, 8.1, 7",
            "Cài driver đầy đủ cho máy",
            "Cài phần mềm cơ bản (Office, Adobe...)",
            "Sao lưu dữ liệu trước khi cài"
        ],
        "price_range": "150.000₫ - 250.000₫"
    }
]

# =========================================================
# HÀM LẤY CATEGORY ID
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
        print(f"   ❌ Lỗi: {e}")
        return None

# =========================================================
# HÀM TẠO NỘI DUNG LANDING PAGE
# =========================================================

def create_landing_page_content(category_info, category_id):
    """Tạo nội dung HTML cho landing page"""

    name = category_info['name']
    icon = category_info['icon']
    description = category_info['description']
    services = category_info['services']
    price_range = category_info['price_range']

    content = f"""
<!-- Hero Section -->
<div class="hero-section" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 80px 20px; text-align: center; color: white; border-radius: 15px; margin-bottom: 50px; box-shadow: 0 10px 40px rgba(0,0,0,0.1);">
    <div style="font-size: 5em; margin-bottom: 20px;">{icon}</div>
    <h1 style="font-size: 3em; margin-bottom: 20px; font-weight: 700;">{name} Tận Nơi Tại TP.HCM</h1>
    <p style="font-size: 1.3em; margin-bottom: 30px; opacity: 0.95;">{description}</p>
    <div style="display: flex; gap: 20px; justify-content: center; flex-wrap: wrap; margin-top: 30px;">
        <a href="tel:0325636239" style="background: #ff6b6b; color: white; padding: 18px 45px; border-radius: 50px; text-decoration: none; font-size: 1.2em; font-weight: bold; box-shadow: 0 5px 15px rgba(255,107,107,0.4); transition: transform 0.2s;">📞 GỌI NGAY: 0325.636.239</a>
        <a href="https://zalo.me/0325636239" style="background: #0068ff; color: white; padding: 18px 45px; border-radius: 50px; text-decoration: none; font-size: 1.2em; font-weight: bold; box-shadow: 0 5px 15px rgba(0,104,255,0.4); transition: transform 0.2s;">💬 CHAT ZALO</a>
    </div>
</div>

<!-- Trust Signals -->
<div class="trust-signals" style="background: #f8f9fa; padding: 50px 20px; border-radius: 15px; margin-bottom: 50px;">
    <h2 style="text-align: center; margin-bottom: 40px; font-size: 2.2em; color: #333;">💎 Tại Sao Chọn Huỳnh Khang Computer?</h2>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 30px;">
        <div style="text-align: center; padding: 30px; background: white; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.08);">
            <div style="font-size: 4em; margin-bottom: 15px;">⚡</div>
            <h3 style="margin-bottom: 10px; color: #667eea;">Nhanh Chóng</h3>
            <p style="color: #666;">Có mặt trong 30-60 phút tại mọi quận/huyện TP.HCM</p>
        </div>
        <div style="text-align: center; padding: 30px; background: white; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.08);">
            <div style="font-size: 4em; margin-bottom: 15px;">💰</div>
            <h3 style="margin-bottom: 10px; color: #667eea;">Giá Minh Bạch</h3>
            <p style="color: #666;">Báo giá trước - Không phát sinh - Cam kết rõ ràng</p>
        </div>
        <div style="text-align: center; padding: 30px; background: white; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.08);">
            <div style="font-size: 4em; margin-bottom: 15px;">🛡️</div>
            <h3 style="margin-bottom: 10px; color: #667eea;">Bảo Hành Dài</h3>
            <p style="color: #666;">Bảo hành 3-12 tháng tùy dịch vụ, hỗ trợ sau bán hàng tốt</p>
        </div>
        <div style="text-align: center; padding: 30px; background: white; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.08);">
            <div style="font-size: 4em; margin-bottom: 15px;">👨‍💻</div>
            <h3 style="margin-bottom: 10px; color: #667eea;">Kỹ Thuật Giỏi</h3>
            <p style="color: #666;">15+ năm kinh nghiệm thực chiến, xử lý mọi sự cố</p>
        </div>
    </div>
</div>

<!-- Services List -->
<div class="services-list" style="margin-bottom: 50px;">
    <h2 style="text-align: center; margin-bottom: 40px; font-size: 2.2em; color: #333;">🔧 Dịch Vụ {name} Chúng Tôi Cung Cấp</h2>
    <div style="background: white; padding: 40px; border-radius: 15px; box-shadow: 0 5px 20px rgba(0,0,0,0.08);">
        <ul style="list-style: none; padding: 0; margin: 0;">
"""

    for service in services:
        content += f"""
            <li style="padding: 20px; border-bottom: 1px solid #eee; display: flex; align-items: center; font-size: 1.1em;">
                <span style="color: #667eea; font-size: 1.5em; margin-right: 15px;">✓</span>
                <span style="color: #333;">{service}</span>
            </li>
"""

    content += f"""
        </ul>
        <div style="margin-top: 30px; padding: 25px; background: linear-gradient(135deg, #fff3cd 0%, #ffe8a1 100%); border-radius: 10px; border-left: 5px solid #ffc107;">
            <h3 style="margin: 0 0 10px 0; color: #856404;">💵 Bảng Giá Tham Khảo</h3>
            <p style="margin: 0; font-size: 1.3em; font-weight: bold; color: #856404;">{price_range}</p>
            <p style="margin: 10px 0 0 0; font-size: 0.95em; color: #856404;">* Giá cuối cùng tùy thuộc vào tình trạng thực tế. Liên hệ để được báo giá chính xác!</p>
        </div>
    </div>
</div>

<!-- Related Posts Section - Tự động query từ WordPress -->
<div class="related-posts" style="margin-bottom: 50px;">
    <h2 style="text-align: center; margin-bottom: 40px; font-size: 2.2em; color: #333;">📚 Kiến Thức & Bài Viết Liên Quan</h2>
    <p style="text-align: center; color: #666; margin-bottom: 30px;">Các bài viết hữu ích về {name.lower()} tại TP.HCM</p>

    <!-- WordPress sẽ tự động hiển thị các bài viết thuộc category này -->
    [blog_posts style="normal" columns="3" category="{category_id}" posts="12" orderby="date" show_date="true" excerpt="true" show_category="false" comments="false" image_height="56.25%"]
</div>

<!-- Service Areas - Tự động query bài viết theo địa phương -->
<div class="service-areas" style="margin-bottom: 50px; background: #f8f9fa; padding: 50px 20px; border-radius: 15px;">
    <h2 style="text-align: center; margin-bottom: 40px; font-size: 2.2em; color: #333;">📍 Khu Vực Phục Vụ</h2>
    <p style="text-align: center; font-size: 1.2em; margin-bottom: 30px; color: #666;">Chọn quận/huyện để xem chi tiết dịch vụ {name.lower()} tại khu vực của bạn:</p>

    <!-- WordPress sẽ tự động query và hiển thị các bài viết theo địa phương -->
    [blog_posts style="vertical" columns="4" category="{category_id}" posts="22" orderby="title" show_date="false" excerpt="false" show_category="false" comments="false" image_height="0" text_align="center"]

    <p style="text-align: center; margin-top: 30px; color: #666; font-style: italic;">Không thấy quận/huyện của bạn? <a href="tel:0325636239" style="color: #667eea; font-weight: bold;">Gọi ngay 0325.636.239</a> để được tư vấn!</p>
</div>

<!-- CTA Section -->
<div class="cta-section" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 60px 20px; border-radius: 15px; text-align: center; color: white; box-shadow: 0 10px 40px rgba(0,0,0,0.15);">
    <h2 style="font-size: 2.5em; margin-bottom: 20px; font-weight: 700;">🚀 Cần {name} Ngay Hôm Nay?</h2>
    <p style="font-size: 1.2em; margin-bottom: 30px; opacity: 0.95;">Liên hệ Huỳnh Khang Computer để được tư vấn và báo giá miễn phí!</p>
    <div style="display: flex; gap: 20px; justify-content: center; flex-wrap: wrap;">
        <a href="tel:0325636239" style="background: #ff6b6b; color: white; padding: 18px 45px; border-radius: 50px; text-decoration: none; font-size: 1.2em; font-weight: bold; box-shadow: 0 5px 15px rgba(255,107,107,0.4);">📞 Gọi: 0325.636.239</a>
        <a href="https://zalo.me/0325636239" style="background: white; color: #667eea; padding: 18px 45px; border-radius: 50px; text-decoration: none; font-size: 1.2em; font-weight: bold; box-shadow: 0 5px 15px rgba(255,255,255,0.3);">💬 Chat Zalo</a>
    </div>
    <p style="margin-top: 30px; font-size: 0.95em; opacity: 0.9;">⏰ Làm việc: Thứ 2 - Chủ Nhật | 8:00 - 20:00</p>
</div>

<!-- Schema Markup -->
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "Service",
  "serviceType": "{name}",
  "provider": {{
    "@type": "LocalBusiness",
    "name": "Huỳnh Khang Computer",
    "telephone": "+84325636239",
    "address": {{
      "@type": "PostalAddress",
      "addressLocality": "TP. Hồ Chí Minh",
      "addressCountry": "VN"
    }}
  }},
  "areaServed": {{
    "@type": "City",
    "name": "TP. Hồ Chí Minh"
  }},
  "description": "{description}",
  "priceRange": "{price_range}"
}}
</script>
"""

    return content

# =========================================================
# HÀM TẠO LANDING PAGE
# =========================================================

def create_landing_page(category_info):
    """Tạo landing page cho category"""

    slug = category_info['slug']
    name = category_info['name']

    print(f"\n🔨 Đang xử lý: {name}")
    print("-" * 70)

    # Lấy category ID
    print(f"   📋 Lấy thông tin category '{slug}'...")
    category = get_category_by_slug(slug)

    if not category:
        print(f"   ❌ Không tìm thấy category '{slug}'. Vui lòng tạo category này trước!")
        return False

    category_id = category['id']
    print(f"   ✅ Category ID: {category_id}")

    # Kiểm tra trang đã tồn tại chưa
    try:
        url = f"{WP_API_URL}/pages"
        params = {"slug": slug, "per_page": 1}
        response = requests.get(url, params=params, auth=(WP_USER, WP_APP_PASS), timeout=30)

        if response.status_code == 200:
            pages = response.json()
            if pages:
                print(f"   ⏭️  Trang landing page đã tồn tại: {pages[0]['link']}")
                return True
    except Exception as e:
        print(f"   ⚠️ Lỗi kiểm tra: {e}")

    # Tạo nội dung
    print(f"   🎨 Đang tạo nội dung landing page...")
    content = create_landing_page_content(category_info, category_id)

    # Tạo trang WordPress
    title = f"{name} Tận Nơi Tại TP.HCM - Huỳnh Khang Computer"

    try:
        data = {
            "title": title,
            "content": content,
            "slug": slug,
            "status": "publish",
            "meta": {
                "description": category_info['description']
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
            print(f"   ✅ Đã tạo landing page: {page_data['link']}")
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
    print("=" * 70)
    print("TẠO LANDING PAGE (HUB) CHO CÁC DANH MỤC DỊCH VỤ")
    print("=" * 70)
    print()
    print("📝 Chức năng:")
    print("   - Tạo 1 trang landing page đẹp cho mỗi danh mục")
    print("   - Tự động hiển thị các bài viết thuộc danh mục đó")
    print("   - Khi viết bài mới, chỉ cần gán đúng category là tự động vào")
    print()

    success_count = 0

    for category_info in CATEGORIES:
        if create_landing_page(category_info):
            success_count += 1
        time.sleep(2)  # Nghỉ giữa các request

    print()
    print("=" * 70)
    print("🎉 HOÀN TẤT!")
    print("=" * 70)
    print()
    print(f"📊 Kết quả: {success_count}/{len(CATEGORIES)} trang đã tạo thành công")
    print()
    print("💡 Cách sử dụng:")
    print("   1. Khi viết bài mới qua bot, chọn đúng category (Sửa Máy Tính, Sửa Laptop...)")
    print("   2. Bài viết sẽ tự động hiển thị trên trang landing page tương ứng")
    print("   3. Không cần làm gì thêm - WordPress tự động xử lý!")
    print()

if __name__ == "__main__":
    main()
