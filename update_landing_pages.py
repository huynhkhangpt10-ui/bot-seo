"""
Script cập nhật nội dung các landing page đã tồn tại
Chỉ cập nhật phần "Khu Vực Phục Vụ" để tự động query bài viết
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

# Tạo base API URL
WP_API_URL = WP_POSTS_URL.rsplit('/', 1)[0]

# Danh sách các trang cần cập nhật
PAGES_TO_UPDATE = [
    {"slug": "sua-may-tinh", "name": "Sửa Máy Tính"},
    {"slug": "sua-laptop", "name": "Sửa Laptop"},
    {"slug": "sua-may-in", "name": "Sửa Máy In"},
    {"slug": "ve-sinh-laptop", "name": "Vệ Sinh Laptop"},
    {"slug": "cai-win", "name": "Cài Win"},
]

def get_page_by_slug(slug):
    """Lấy thông tin trang từ slug"""
    try:
        url = f"{WP_API_URL}/pages"
        params = {"slug": slug, "per_page": 1}
        response = requests.get(url, params=params, auth=(WP_USER, WP_APP_PASS), timeout=30)

        if response.status_code == 200:
            pages = response.json()
            if pages:
                return pages[0]
        return None
    except Exception as e:
        print(f"   ❌ Lỗi: {e}")
        return None

def get_category_by_slug(slug):
    """Lấy category ID từ slug"""
    try:
        url = f"{WP_API_URL}/categories"
        params = {"slug": slug, "per_page": 1}
        response = requests.get(url, params=params, auth=(WP_USER, WP_APP_PASS), timeout=30)

        if response.status_code == 200:
            categories = response.json()
            if categories:
                return categories[0]['id']
        return None
    except Exception as e:
        print(f"   ❌ Lỗi: {e}")
        return None

def update_page_content(page_id, page_slug, page_name):
    """Cập nhật nội dung trang"""

    # Lấy category ID
    category_id = get_category_by_slug(page_slug)
    if not category_id:
        print(f"   ⚠️ Không tìm thấy category '{page_slug}'")
        return False

    print(f"   ✅ Category ID: {category_id}")

    # Lấy nội dung hiện tại
    page = get_page_by_slug(page_slug)
    if not page:
        print(f"   ❌ Không tìm thấy trang")
        return False

    current_content = page['content']['rendered']

    # Tìm và thay thế phần "Khu Vực Phục Vụ"
    import re

    # Pattern để tìm phần service-areas cũ
    pattern = r'<!-- Service Areas.*?</div>\s*</div>'

    # Nội dung mới cho phần "Khu Vực Phục Vụ"
    new_service_areas = f'''<!-- Service Areas - Tự động query bài viết theo địa phương -->
<div class="service-areas" style="margin-bottom: 50px; background: #f8f9fa; padding: 50px 20px; border-radius: 15px;">
    <h2 style="text-align: center; margin-bottom: 40px; font-size: 2.2em; color: #333;">📍 Khu Vực Phục Vụ</h2>
    <p style="text-align: center; font-size: 1.2em; margin-bottom: 30px; color: #666;">Chọn quận/huyện để xem chi tiết dịch vụ {page_name.lower()} tại khu vực của bạn:</p>

    <!-- WordPress sẽ tự động query và hiển thị các bài viết theo địa phương -->
    [blog_posts style="vertical" columns="4" category="{category_id}" posts="22" orderby="title" show_date="false" excerpt="false" show_category="false" comments="false" image_height="0" text_align="center"]

    <p style="text-align: center; margin-top: 30px; color: #666; font-style: italic;">Không thấy quận/huyện của bạn? <a href="tel:0325636239" style="color: #667eea; font-weight: bold;">Gọi ngay 0325.636.239</a> để được tư vấn!</p>
</div>'''

    # Thay thế
    new_content = re.sub(pattern, new_service_areas, current_content, flags=re.DOTALL)

    if new_content == current_content:
        print(f"   ⚠️ Không tìm thấy phần 'Service Areas' để cập nhật")
        return False

    # Cập nhật trang
    try:
        data = {"content": new_content}
        response = requests.post(
            f"{WP_API_URL}/pages/{page_id}",
            json=data,
            auth=(WP_USER, WP_APP_PASS),
            timeout=120
        )

        if response.status_code == 200:
            print(f"   ✅ Đã cập nhật thành công!")
            return True
        else:
            print(f"   ❌ Lỗi cập nhật: {response.status_code}")
            return False

    except Exception as e:
        print(f"   ❌ Lỗi: {e}")
        return False

def main():
    print("="*70)
    print("CẬP NHẬT LANDING PAGES - PHẦN KHU VỰC PHỤC VỤ")
    print("="*70)
    print()

    success_count = 0

    for page_info in PAGES_TO_UPDATE:
        slug = page_info['slug']
        name = page_info['name']

        print(f"🔨 Đang cập nhật: {name}")
        print("-"*70)

        # Lấy thông tin trang
        page = get_page_by_slug(slug)
        if not page:
            print(f"   ❌ Không tìm thấy trang '{slug}'")
            print()
            continue

        page_id = page['id']
        print(f"   📄 Page ID: {page_id}")

        # Cập nhật nội dung
        if update_page_content(page_id, slug, name):
            success_count += 1

        print()
        time.sleep(2)

    print("="*70)
    print("🎉 HOÀN TẤT!")
    print("="*70)
    print()
    print(f"📊 Kết quả: {success_count}/{len(PAGES_TO_UPDATE)} trang đã cập nhật")
    print()

if __name__ == "__main__":
    main()
