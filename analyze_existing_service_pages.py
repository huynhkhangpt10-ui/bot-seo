"""
Script phân tích các trang dịch vụ hiện có trên huynhkhang.com
Mục tiêu: Hiểu cấu trúc để tạo thêm trang mới hoặc cải thiện
"""

import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# Fix encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def analyze_service_page(url):
    """Phân tích cấu trúc một trang dịch vụ"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        analysis = {
            'url': url,
            'title': soup.find('h1').get_text(strip=True) if soup.find('h1') else 'N/A',
            'meta_description': '',
            'sections': [],
            'cta_buttons': [],
            'related_posts': [],
            'schema': []
        }

        # Meta description
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc:
            analysis['meta_description'] = meta_desc.get('content', '')

        # Sections (H2)
        for h2 in soup.find_all('h2'):
            analysis['sections'].append(h2.get_text(strip=True))

        # CTA buttons
        for link in soup.find_all('a'):
            text = link.get_text(strip=True).lower()
            if any(x in text for x in ['gọi', 'liên hệ', 'zalo', 'hotline', 'đặt lịch']):
                analysis['cta_buttons'].append({
                    'text': link.get_text(strip=True),
                    'href': link.get('href', '')
                })

        # Related posts
        for article in soup.find_all(['article', 'div'], class_=lambda x: x and ('post' in x or 'article' in x)):
            title_elem = article.find(['h3', 'h4', 'a'])
            if title_elem:
                analysis['related_posts'].append(title_elem.get_text(strip=True))

        # Schema markup
        for script in soup.find_all('script', type='application/ld+json'):
            analysis['schema'].append(script.string[:200] if script.string else '')

        return analysis

    except Exception as e:
        return {'error': str(e), 'url': url}

def main():
    print("="*70)
    print("PHÂN TÍCH CẤU TRÚC TRANG DỊCH VỤ HIỆN CÓ")
    print("="*70)
    print()

    # Danh sách trang dịch vụ đã có
    service_pages = [
        "https://huynhkhang.com/sua-may-tinh/sua-may-tinh-quan-1-tan-noi/",
        "https://huynhkhang.com/sua-may-tinh/sua-may-tinh-quan-2-tan-noi/",
        "https://huynhkhang.com/sua-may-tinh/sua-may-tinh-quan-binh-thanh-tan-noi/",
        "https://huynhkhang.com/sua-may-tinh/sua-may-tinh-thu-duc-tan-noi/",
    ]

    for url in service_pages:
        print(f"🔍 Đang phân tích: {url}")
        result = analyze_service_page(url)

        if 'error' in result:
            print(f"   ❌ Lỗi: {result['error']}")
            continue

        print(f"\n📄 Tiêu đề: {result['title']}")
        print(f"📝 Meta: {result['meta_description'][:100]}...")

        print(f"\n📌 Các section chính ({len(result['sections'])} sections):")
        for i, section in enumerate(result['sections'][:5], 1):
            print(f"   {i}. {section}")

        print(f"\n🎯 CTA Buttons ({len(result['cta_buttons'])} buttons):")
        for cta in result['cta_buttons'][:3]:
            print(f"   - {cta['text']} → {cta['href']}")

        print(f"\n📚 Bài viết liên quan ({len(result['related_posts'])} bài):")
        for post in result['related_posts'][:3]:
            print(f"   - {post}")

        print(f"\n🔖 Schema markup: {'Có' if result['schema'] else 'Không'}")

        print("\n" + "-"*70 + "\n")

    print("="*70)
    print("💡 KẾT LUẬN")
    print("="*70)
    print()
    print("Dựa trên phân tích, tôi sẽ:")
    print("1. Tạo template tương tự cho các quận/huyện còn thiếu")
    print("2. Đảm bảo có đầy đủ: Hero, Giá, Dịch vụ, Bài liên quan, CTA, Schema")
    print("3. Tự động query bài viết liên quan từ WordPress API")
    print()

if __name__ == "__main__":
    main()
