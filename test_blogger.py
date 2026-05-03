import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/blogger']
BLOGS = [
    {'name': 'Dịch vụ máy tính bình dương', 'id': '5214607832735598692'},
    {'name': 'Thủ thuật máy tính tân uyên', 'id': '4342701550163439217'}
]

def get_blogger_service():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
            
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('client_secrets.json', SCOPES)
            flow.redirect_uri = 'http://localhost'
            auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
            
            print(f"\n👉 1. Dán link này vào Chrome:")
            print(f"{auth_url}")
            print(f"⚠️ 2. ĐĂNG NHẬP BẰNG GMAIL MỚI VÀ TÍCH Ô QUYỀN BLOGGER!")
            
            res_url = input("\n👉 3. Dán Link kết quả vào đây: ").strip()
            
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

def post_to_all_blogs():
    try:
        service = get_blogger_service()
        for blog in BLOGS:
            print(f"🚀 Đang bắn bài vào: {blog['name']}...")
            post_data = {
                'kind': 'blogger#post',
                'title': f'Bot Khang IT V2 - Đã Thông Nòng {blog["name"]}',
                'content': 'Hệ thống Bot SEO tự động đã vượt qua chốt chặn Google Cloud thành công!',
                'labels': ['Bot SEO']
            }
            request = service.posts().insert(blogId=blog['id'], body=post_data)
            request.execute()
            print(f"✅ THÀNH CÔNG RỰC RỠ!")
    except Exception as e:
        print(f"❌ LỖI RỒI: {e}")

if __name__ == "__main__":
    post_to_all_blogs()