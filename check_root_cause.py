import os
import pickle
from googleapiclient.discovery import build

def diagnose():
    print("==================================================")
    print("🔍 ĐANG ĐIỀU TRA NGUYÊN NHÂN LỖI 403 TỪ GOOGLE...")
    print("==================================================")
    
    if not os.path.exists('token.pickle'):
        print("❌ Không tìm thấy token.pickle. Chìa khóa chưa được tạo.")
        return

    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)

    # 1. KIỂM TRA QUYỀN (SCOPES)
    print(f"\n1️⃣ KIỂM TRA QUYỀN TRONG CHÌA KHÓA:")
    if 'https://www.googleapis.com/auth/blogger' in creds.scopes:
        print("   ✅ CHUẨN: Đã có quyền quản lý Blogger cao nhất.")
    else:
        print("   ❌ SAI: Chìa khóa này KHÔNG CÓ quyền quản lý (Anh chưa tích ô vuông lúc xác thực).")
        print(f"   (Quyền hiện tại đang có: {creds.scopes})")

    try:
        service = build('blogger', 'v3', credentials=creds)

        # 2. KIỂM TRA ĐỊNH DANH
        user_info = service.users().get(userId='self').execute()
        print(f"\n2️⃣ GOOGLE ĐANG NHẬN DIỆN BOT LÀ TÀI KHOẢN NÀO?")
        print(f"   👉 Tên hiển thị: {user_info.get('displayName')}")
        print(f"   👉 Link Profile: {user_info.get('url')}")

        # 3. TRÍCH XUẤT TẬN GỐC DANH SÁCH BLOG
        print(f"\n3️⃣ NHỮNG BLOG MÀ GOOGLE 'CHO PHÉP' TÀI KHOẢN NÀY ĐĂNG BÀI:")
        blogs = service.blogs().listByUser(userId='self').execute()

        target_id_1 = '5214607832735598692' # Bình Dương
        target_id_2 = '4342701550163439217' # Tân Uyên
        found_1, found_2 = False, False

        if 'items' in blogs:
            for blog in blogs['items']:
                print(f"   - Tên: {blog['name']}")
                print(f"     ID:  {blog['id']}")
                if blog['id'] == target_id_1: found_1 = True
                if blog['id'] == target_id_2: found_2 = True
        else:
            print("   ❌ TRỐNG TRƠN: Tài khoản này KHÔNG ĐƯỢC Google cấp quyền ở bất kỳ Blog nào!")

        # KẾT LUẬN CỦA "BÁC SĨ"
        print("\n==================================================")
        print("💡 KẾT LUẬN CHÍNH XÁC TỪ MÁY CHỦ GOOGLE:")
        if not found_1:
            print(f"❌ Google KHÔNG CÔNG NHẬN tài khoản này có quyền can thiệp vào trang 'Bình Dương' (ID: {target_id_1})")
        if not found_2:
            print(f"❌ Google KHÔNG CÔNG NHẬN tài khoản này có quyền can thiệp vào trang 'Tân Uyên' (ID: {target_id_2})")
            
        if found_1 and found_2:
            print("✅ Tài khoản chuẩn, quyền chuẩn. LỖI KHÔNG PHẢI DO TÀI KHOẢN HAY CODE!")
            print("👉 THỦ PHẠM: Do cái Project trên Google Cloud của anh chưa bật nút 'Blogger API v3'.")
        print("==================================================")

    except Exception as e:
        print(f"\n❌ LỖI KẾT NỐI API: {e}")

if __name__ == "__main__":
    diagnose()