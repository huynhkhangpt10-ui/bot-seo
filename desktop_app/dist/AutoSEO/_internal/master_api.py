import os
import pickle
import time
import pytumblr
import requests
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import NewPost

# ==========================================
# 1. CẤU HÌNH THÔNG TIN (Dựa trên bản test của anh)
# ==========================================

# --- Cấu hình WordPress ---
WP_USER = "huynhkhangpt02"
WP_PW = "vfqumrev7jhhytw5"
WP_SITES = [
    "https://caiwinbinhduong.wordpress.com/xmlrpc.php",
    "https://suamaytinhtanuyen.wordpress.com/xmlrpc.php"
]

# --- Cấu hình Tumblr ---
TUMBLR_KEYS = {
    'consumer_key': 'mS5HkTNvccY2pDhO82mqHtoRVcE4PoPQgoY3nAz3DQ5IQH06RN',
    'consumer_secret': 'gRboNg2pdnitN8MPO45b92qivR9Kozas1xeb7UZIpnC0S35G2R',
    'oauth_token': 'JsdCWxDQMpdhIW18z1V3k43ErRYluPLClnFsopxVV2PTTRzB5J',
    'oauth_token_secret': '7qHXKJNy5GkPpXHlEm93GSbRAg554i4usdv6tSOa5QzpUkJOEZ',
    'blog_name': 'dichvuhuynhkhang'
}

# --- Cấu hình Blogger ---
BLOGGER_SCOPES = ['https://www.googleapis.com/auth/blogger']
BLOGGER_IDS = [
    {'name': 'Dịch vụ máy tính bình dương', 'id': '5214607832735598692'},
    {'name': 'Thủ thuật máy tính tân uyên', 'id': '4342701550163439217'}
]

# ==========================================
# 2. CÁC HÀM KẾT NỐI API
# ==========================================

def get_blogger_service():
    """Xử lý xác thực Blogger (Sử dụng lại token.pickle đã có)"""
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
            
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', BLOGGER_SCOPES)
            flow.redirect_uri = 'http://localhost'
            auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
            print(f"\n👉 Dán link này vào Chrome:\n{auth_url}")
            res_url = input("\n👉 Dán Link kết quả (localhost) vào đây: ").strip()
            
            if "code=" in res_url:
                from urllib.parse import urlparse, parse_qs
                code = parse_qs(urlparse(res_url).query).get('code', [None])[0]
            else:
                code = res_url
                
            flow.fetch_token(code=code)
            creds = flow.credentials
            
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('blogger', 'v3', credentials=creds)

# ==========================================
# 3. CÁC HÀM ĐĂNG BÀI CHÍNH
# ==========================================

def post_to_wordpress(title, content):
    print("\n🌐 [WORDPRESS] Đang đẩy bài...")
    for url in WP_SITES:
        site_domain = url.split('/')[2]
        try:
            client = Client(url, WP_USER, WP_PW)
            post = WordPressPost()
            post.title = title
            post.content = content
            post.post_status = 'publish'
            client.call(NewPost(post))
            print(f"   ✅ Thành công: {site_domain}")
        except Exception as e:
            print(f"   ❌ Lỗi tại {site_domain}: {e}")

def post_to_tumblr(title, content, tags):
    print("\n📱 [TUMBLR] Đang đẩy bài...")
    try:
        client = pytumblr.TumblrRestClient(
            TUMBLR_KEYS['consumer_key'], TUMBLR_KEYS['consumer_secret'],
            TUMBLR_KEYS['oauth_token'], TUMBLR_KEYS['oauth_token_secret']
        )
        response = client.create_text(
            TUMBLR_KEYS['blog_name'], 
            state="published", 
            title=title, 
            body=content, 
            tags=tags
        )
        if "id" in response:
            print(f"   ✅ Thành công! ID: {response['id']}")
    except Exception as e:
        print(f"   ❌ Lỗi Tumblr: {e}")

def post_to_blogger(title, content, tags):
    print("\n🅱️ [BLOGGER] Đang đẩy bài...")
    try:
        service = get_blogger_service()
        for blog in BLOGGER_IDS:
            post_data = {
                'kind': 'blogger#post',
                'title': title,
                'content': content,
                'labels': tags
            }
            service.posts().insert(blogId=blog['id'], body=post_data).execute()
            print(f"   ✅ Thành công: {blog['name']}")
    except Exception as e:
        print(f"   ❌ Lỗi Blogger: {e}")

# ==========================================
# 4. CHƯƠNG TRÌNH CHẠY THỬ NGHIỆM TỔNG THỂ
# ==========================================

if __name__ == "__main__":
    print("🚀 --- KHỞI ĐỘNG HỆ THỐNG KẾT NỐI ĐA KÊNH KHANG IT ---")
    
    # Giả lập dữ liệu bài viết (Sau này AI sẽ tự viết)
    test_title = "Dịch Vụ Máy Tính Khang IT - Kết Nối Đa Nền Tảng"
    test_content = """
        <h3>Hệ thống Bot SEO của Khang IT đã vận hành hoàn chỉnh</h3>
        <p>Tự động đăng bài lên WordPress, Tumblr và Blogger cùng một lúc.</p>
        <p>Địa chỉ: Tân Uyên, Bình Dương. Chuyên sửa chữa máy tính, Laptop tận nơi.</p>
    """
    test_tags = ["Khang IT", "Sửa Máy Tính", "Tân Uyên", "Bình Dương"]

    # Triển khai đăng bài đồng loạt
    post_to_wordpress(test_title, test_content)
    post_to_tumblr(test_title, test_content, test_tags)
    post_to_blogger(test_title, test_content, test_tags)

    print("\n🎉 --- TẤT CẢ CÁC KÊNH ĐÃ ĐƯỢC THÔNG NÒNG! ---")