import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow

# 🔥 LỆNH VƯỢT RÀO BẢO MẬT HTTP CỦA GOOGLE (Sửa lỗi insecure_transport)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Tự động tìm file chứa mã bí mật của Google
secret_file = 'client_secrets.json' if os.path.exists('client_secrets.json') else 'credentials.json'

if not os.path.exists(secret_file):
    print(f"❌ LỖI: Không tìm thấy file {secret_file}! Sếp kiểm tra lại xem file API của Google sếp đặt tên là gì nhé.")
    exit()

flow = InstalledAppFlow.from_client_secrets_file(secret_file, ['https://www.googleapis.com/auth/blogger'])
flow.redirect_uri = 'http://localhost:8080/'
auth_url, _ = flow.authorization_url(prompt='consent')

print("\n" + "="*70)
print("BƯỚC 1: COPY ĐƯỜNG LINK BÊN DƯỚI VÀ DÁN VÀO TRÌNH DUYỆT (CHROME) TRÊN MÁY TÍNH CỦA SẾP:")
print("\n" + auth_url + "\n")
print("="*70 + "\n")

print("BƯỚC 2: Đăng nhập Gmail chứa trang Blogger và bấm CHO PHÉP (Allow).")
print("🔥 LƯU Ý CỰC QUAN TRỌNG: Sau khi bấm Cho phép, trình duyệt sẽ xoay một lúc rồi báo lỗi 'Không thể truy cập trang web / Localhost refused to connect'.")
print("=> KỆ NÓ! Đó là bình thường! Sếp hãy COPY TOÀN BỘ CÁI ĐƯỜNG LINK BỊ LỖI ĐÓ TRÊN THANH ĐỊA CHỈ TRÌNH DUYỆT.\n")

redirect_response = input("BƯỚC 3: DÁN CÁI ĐƯỜNG LINK LỖI VỪA COPY VÀO ĐÂY VÀ BẤM ENTER: \n=> ")

try:
    flow.fetch_token(authorization_response=redirect_response.strip())
    with open('token.pickle', 'wb') as token:
        pickle.dump(flow.credentials, token)
    print("\n🎉 THÀNH CÔNG RỰC RỠ! ĐÃ TẠO LẠI CHÌA KHÓA TOKEN.PICKLE! Sếp vào lại Cỗ máy bấm Kích hoạt là chạy phà phà!")
except Exception as e:
    print(f"\n❌ Lỗi: {e}")