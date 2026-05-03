import json
import requests

try:
    with open("token.json", "r", encoding="utf-8") as f:
        data = json.load(f)
        token = data.get("access_token")
        
    print("1. Đã đọc được file token.json!")
    
    # Thử gọi API lấy thông tin OA để xem token có hợp lệ không
    url = "https://openapi.zalo.me/v2.0/oa/getoa"
    headers = {"access_token": token}
    res = requests.get(url, headers=headers).json()
    
    if res.get("error") == 0:
        print(f"✅ XUẤT SẮC! Token hợp lệ. Tên Zalo OA của sếp là: {res['data']['name']}")
    else:
        print(f"❌ LỖI TỪ ZALO: {res.get('message')} (Mã lỗi: {res.get('error')})")
        if res.get('error') == -216:
            print("👉 Bệnh này là: Token đã hết hạn, sếp cần tạo lại token mới.")
            
except Exception as e:
    print(f"❌ Lỗi do file JSON: {e}")