import requests
import base64

# THÔNG TIN CỦA ANH
WP_USERNAME = "huynhkhangpt02"
WP_APP_PASSWORD = "76x5rddbxcuxs6fw"

def check_my_sites():
    # API lấy danh sách các trang web mà tài khoản này quản lý
    url = "https://public-api.wordpress.com/rest/v1.1/me/sites"
    
    auth_string = f"{WP_USERNAME}:{WP_APP_PASSWORD}"
    token = base64.b64encode(auth_string.encode()).decode('utf-8')
    
    headers = {'Authorization': f'Basic {token}'}
    
    print(f"--- ĐANG KIỂM TRA QUYỀN HẠN CỦA USER: {WP_USERNAME} ---")
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            sites = response.json().get('sites', [])
            print(f"✅ Kết nối thành công! Anh có quyền trên {len(sites)} trang web:")
            for s in sites:
                print(f" - Tên: {s['name']} | Domain: {s['URL']} | ID: {s['ID']}")
        else:
            print(f"❌ Lỗi xác thực {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Lỗi kết nối: {e}")

if __name__ == "__main__":
    check_my_sites()
