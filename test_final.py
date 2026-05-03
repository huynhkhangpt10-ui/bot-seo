from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import NewPost

# ==========================================
# DANH SÁCH 2 SITE CỦA ANH KHANG
# ==========================================
WP_SITES = [
    "https://caiwinbinhduong.wordpress.com/xmlrpc.php",
    "https://suamaytinhtanuyen.wordpress.com/xmlrpc.php"
]

USER = "huynhkhangpt02"
PW = "vfqumrev7jhhytw5"

def post_to_all_sites():
    print(f"🚀 Bắt đầu chiến dịch phủ sóng 2 trang vệ tinh...")
    
    for url in WP_SITES:
        site_name = url.split('/')[2] # Lấy cái tên miền để in cho đẹp
        print(f"--- Đang bắn bài vào: {site_name} ---")
        
        try:
            client = Client(url, USER, PW)
            post = WordPressPost()
            post.title = 'Dịch Vụ Máy Tính Tân Uyên - Khang IT Phủ Sóng'
            post.content = f'''
                <h3>Dịch vụ kỹ thuật tận nơi tại Tân Uyên, Bình Dương</h3>
                <p>Chào mừng quý khách! Đây là bài viết tự động từ hệ thống Bot của Khang IT.</p>
                <p>Địa chỉ: Tân Uyên, Bình Dương. Chuyên cài Win, sửa Laptop nhanh chóng.</p>
            '''
            post.post_status = 'publish'
            
            post_id = client.call(NewPost(post))
            if post_id:
                print(f"✅ THÀNH CÔNG! Đã lên bài trên {site_name} (ID: {post_id})")
                
        except Exception as e:
            print(f"❌ LỖI tại {site_name}: {e}")

if __name__ == "__main__":
    post_to_all_sites()