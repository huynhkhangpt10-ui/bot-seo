import pytumblr

# ==========================================
# BỘ TỨ CHÌA KHÓA TUMBLR - LONG ĐÃ ĐIỀN CHUẨN
# ==========================================
consumer_key = 'mS5HkTNvccY2pDhO82mqHtoRVcE4PoPQgoY3nAz3DQ5IQH06RN'
consumer_secret = 'gRboNg2pdnitN8MPO45b92qivR9Kozas1xeb7UZIpnC0S35G2R'
oauth_token = 'JsdCWxDQMpdhIW18z1V3k43ErRYluPLClnFsopxVV2PTTRzB5J'
oauth_token_secret = '7qHXKJNy5GkPpXHlEm93GSbRAg554i4usdv6tSOa5QzpUkJOEZ'

# Tên Blog lấy từ Screenshot của anh
blog_name = 'dichvuhuynhkhang' 

def post_tumblr_final():
    print(f"🚀 Đang bắn bài 'oanh tạc' lên Tumblr: {blog_name}...")
    
    try:
        # Khởi tạo kết nối
        client = pytumblr.TumblrRestClient(
            consumer_key,
            consumer_secret,
            oauth_token,
            oauth_token_secret
        )

        # Nội dung bài viết mang đậm thương hiệu Khang IT
        response = client.create_text(
            blog_name, 
            state="published", 
            title="Dịch Vụ Cài Win & Sửa Máy Tính Tân Uyên - Khang IT",
            body="""
                <h2>Hệ thống vệ tinh Tumblr đã chính thức thông nòng!</h2>
                <p>Chào anh Khang! Đây là bài viết tự động từ Bot Python trên VPS Linux.</p>
                <p>Địa chỉ: Tân Uyên, Bình Dương. Chuyên cài Win, sửa Laptop tận nơi, uy tín.</p>
            """,
            tags=["Cài Win", "Sửa Máy Tính", "Tân Uyên", "Bình Dương", "Khang IT"]
        )

        if "id" in response:
            print("✅ QUÁ TUYỆT VỜI! Bài đã lên Tumblr thành công rồi anh ơi!")
            print(f"👉 Mã ID bài viết: {response['id']}")
            print(f"👉 Anh kiểm tra tại: https://{blog_name}.tumblr.com")
        else:
            print(f"❌ CÓ LỖI RỒI: {response}")

    except Exception as e:
        print(f"❌ LỖI KẾT NỐI TUMBLR: {e}")

if __name__ == "__main__":
    post_tumblr_final()
