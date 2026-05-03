"""
Script phân tích sitemap huynhkhang.com để khảo sát dịch vụ
Mục tiêu: Gom nhóm bài viết theo Topic Cluster cho Local SEO
"""

import sys
import requests
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
import re
from collections import defaultdict

# Fix encoding cho Windows console
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def fetch_sitemap(url):
    """Lấy nội dung sitemap"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"Lỗi khi tải sitemap: {e}")
        return None

def parse_sitemap_index(content):
    """Parse sitemap index để lấy danh sách sitemap con"""
    root = ET.fromstring(content)
    namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

    sitemaps = []
    for sitemap in root.findall('.//ns:sitemap', namespace):
        loc = sitemap.find('ns:loc', namespace)
        if loc is not None:
            sitemaps.append(loc.text)

    return sitemaps

def parse_sitemap_urls(content):
    """Parse sitemap để lấy danh sách URL"""
    root = ET.fromstring(content)
    namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

    urls = []
    for url in root.findall('.//ns:url', namespace):
        loc = url.find('ns:loc', namespace)
        if loc is not None:
            urls.append(loc.text)

    return urls

def classify_service(url, title=""):
    """Phân loại URL vào nhóm dịch vụ"""
    url_lower = url.lower()
    title_lower = title.lower()
    text = url_lower + " " + title_lower

    # Định nghĩa các nhóm dịch vụ chính
    services = {
        "Sửa máy tính / Laptop": [
            "sua may tinh", "sua laptop", "sua mainboard", "sua main",
            "sua chua may tinh", "khong len", "khong bat", "khong hien thi",
            "bi loi", "bi hu", "khong nhan", "mat nguon", "tat nguon"
        ],
        "Cài đặt phần mềm": [
            "cai win", "cai windows", "cai dat", "ghost", "cai office",
            "cai adobe", "cai photoshop", "cai autocad", "cai corel",
            "cai premiere", "cai illustrator", "active", "crack"
        ],
        "Nâng cấp phần cứng": [
            "nang cap", "thay ram", "thay ssd", "thay o cung", "thay card",
            "thay man hinh", "thay ban phim", "thay pin", "upgrade"
        ],
        "Vệ sinh máy tính": [
            "ve sinh", "lam sach", "tan nhiet", "quat", "keo tan nhiet",
            "bui", "cleaning"
        ],
        "Sửa máy in": [
            "may in", "printer", "sua may in", "loi may in"
        ],
        "Phần mềm Adobe": [
            "adobe", "photoshop", "illustrator", "premiere", "after effects",
            "lightroom", "indesign", "acrobat"
        ],
        "Phần mềm Autodesk": [
            "autocad", "3ds max", "revit", "inventor", "autodesk", "maya"
        ],
        "Phần mềm CorelDRAW": [
            "corel", "coreldraw"
        ],
        "Windows & Office": [
            "windows", "win 10", "win 11", "office", "word", "excel", "powerpoint"
        ],
        "Lỗi phần mềm": [
            "loi", "error", "khong mo duoc", "khong chay", "bi treo",
            "khong hoat dong", "khong the", "that bai"
        ],
        "Thủ thuật / Tips": [
            "cach", "huong dan", "meo", "thu thuat", "tips", "tricks"
        ],
        "Bản quyền / License": [
            "ban quyen", "license", "gia", "mua", "key", "serial"
        ]
    }

    matched_services = []
    for service_name, keywords in services.items():
        for keyword in keywords:
            if keyword in text:
                matched_services.append(service_name)
                break

    return matched_services if matched_services else ["Khác"]

def main():
    print("="*70)
    print("PHÂN TÍCH SITEMAP - KHẢO SÁT DỊCH VỤ HUỲNH KHANG COMPUTER")
    print("="*70)
    print()

    base_url = "https://huynhkhang.com"
    sitemap_url = f"{base_url}/sitemap_index.xml"

    print(f"🔍 Đang tải sitemap từ: {sitemap_url}")
    content = fetch_sitemap(sitemap_url)

    if not content:
        print("❌ Không thể tải sitemap. Thử sitemap.xml...")
        sitemap_url = f"{base_url}/sitemap.xml"
        content = fetch_sitemap(sitemap_url)

        if not content:
            print("❌ Không thể tải được sitemap nào!")
            return

    # Parse sitemap index
    print("📄 Đang phân tích sitemap index...")
    try:
        sitemap_list = parse_sitemap_index(content)
        if sitemap_list:
            print(f"✅ Tìm thấy {len(sitemap_list)} sitemap con")
        else:
            # Nếu không phải sitemap index, parse trực tiếp
            sitemap_list = [sitemap_url]
    except:
        sitemap_list = [sitemap_url]

    # Thu thập tất cả URL
    all_urls = []
    for sitemap in sitemap_list:
        print(f"   📥 Đang tải: {sitemap}")
        sub_content = fetch_sitemap(sitemap)
        if sub_content:
            urls = parse_sitemap_urls(sub_content)
            all_urls.extend(urls)

    print(f"\n✅ Tổng cộng thu thập được: {len(all_urls)} URL")
    print()

    # Phân loại URL theo dịch vụ
    print("🔬 Đang phân tích và gom nhóm theo Topic Cluster...")
    print()

    service_clusters = defaultdict(list)

    for url in all_urls:
        # Bỏ qua các URL không phải bài viết
        if any(x in url for x in ['/page/', '/category/', '/tag/', '/author/', '/wp-', '/feed']):
            continue

        services = classify_service(url)
        for service in services:
            service_clusters[service].append(url)

    # In báo cáo
    print("="*70)
    print("📊 BÁO CÁO PHÂN LOẠI DỊCH VỤ (TOPIC CLUSTERS)")
    print("="*70)
    print()

    # Sắp xếp theo số lượng bài viết
    sorted_services = sorted(service_clusters.items(), key=lambda x: len(x[1]), reverse=True)

    total_articles = sum(len(urls) for _, urls in sorted_services)

    for service_name, urls in sorted_services:
        count = len(urls)
        percentage = (count / total_articles * 100) if total_articles > 0 else 0

        print(f"📌 {service_name}")
        print(f"   Số bài viết: {count} ({percentage:.1f}%)")
        print(f"   Mẫu URL:")

        # Hiển thị 3 URL mẫu
        for url in urls[:3]:
            path = urlparse(url).path
            print(f"   - {path}")

        if count > 3:
            print(f"   ... và {count - 3} bài khác")
        print()

    print("="*70)
    print("💡 GỢI Ý TRANG DỊCH VỤ NÊN TẠO")
    print("="*70)
    print()

    # Gợi ý các trang dịch vụ chính
    priority_services = [
        ("Sửa máy tính / Laptop", "/dich-vu/sua-may-tinh-laptop-tai-tphcm/"),
        ("Cài đặt phần mềm", "/dich-vu/cai-dat-phan-mem-tai-tphcm/"),
        ("Nâng cấp phần cứng", "/dich-vu/nang-cap-may-tinh-tai-tphcm/"),
        ("Vệ sinh máy tính", "/dich-vu/ve-sinh-may-tinh-laptop-tai-tphcm/"),
        ("Sửa máy in", "/dich-vu/sua-may-in-tai-tphcm/"),
    ]

    for service_name, suggested_url in priority_services:
        count = len(service_clusters.get(service_name, []))
        print(f"✅ {service_name}")
        print(f"   URL đề xuất: {suggested_url}")
        print(f"   Số bài liên quan: {count}")
        print()

    print("="*70)
    print("✅ HOÀN TẤT PHÂN TÍCH!")
    print("="*70)
    print()
    print("📝 Bước tiếp theo:")
    print("   1. Xem lại danh sách dịch vụ trên")
    print("   2. Xác nhận các trang dịch vụ cần tạo")
    print("   3. Tiến hành code HTML/CSS cho từng trang")
    print()

if __name__ == "__main__":
    main()
