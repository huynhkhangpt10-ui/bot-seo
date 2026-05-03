import os
import pickle
from googleapiclient.discovery import build

def check_identity():
    if not os.path.exists('token.pickle'):
        print("❌ Chưa có file token.pickle. Anh cần chạy test_blogger.py trước.")
        return

    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
    
    try:
        service = build('blogger', 'v3', credentials=creds)
        # Lấy thông tin người dùng hiện tại
        user_info = service.users().get(userId='self').execute()
        print(f"\n✅ CON BOT ĐANG SỬ DỤNG TÀI KHOẢN: {user_info.get('displayName')}")
        print(f"👉 Link cá nhân: {user_info.get('url')}")
        
        # Liệt kê danh sách Blog mà tài khoản này có quyền Quản trị
        print("\n📂 CÁC BLOG MÀ TÀI KHOẢN NÀY CÓ QUYỀN ĐĂNG BÀI:")
        blogs = service.blogs().listByUser(userId='self').execute()
        if 'items' in blogs:
            for blog in blogs['items']:
                print(f"- {blog['name']} (ID: {blog['id']})")
        else:
            print("❌ TÀI KHOẢN NÀY KHÔNG CÓ QUYỀN ADMIN Ở BẤT KỲ BLOG NÀO!")
            
    except Exception as e:
        print(f"❌ LỖI: {e}")

if __name__ == "__main__":
    check_identity()