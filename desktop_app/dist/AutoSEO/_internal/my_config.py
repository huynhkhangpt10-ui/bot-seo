# my_config.py
import os
from google import genai

# =========================================================
# 🌟 KHU VỰC 1: CẤU HÌNH NÃO BỘ (VERTEX AI) 🌟
# =========================================================
# 💥 ĐÃ SỬA: Chuyển sang đường dẫn tương đối để chạy trên Windows PC
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "vertex-key.json"
PROJECT_ID = "project-46198d54-c335-4c44-bf1" 
LOCATION = "us-central1"

GOOGLE_SEARCH_API_KEY = "AIzaSyDvj90b8ig2WSaANZCer4x-iMBq_9dsACI"
SEARCH_ENGINE_ID = "85fbd87f2b9e1473c"

# Kích hoạt cỗ máy AI
client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

# =========================================================
# 🌍 KHU VỰC 2: CẤU HÌNH WEB CHÍNH (HUYNHKHANG.COM)
# =========================================================
WP_USER = "huynhkhang"
WP_APP_PASS = "XbNR P1cs v3is DEDK xFN9 ywZY"

# CÁC ĐƯỜNG DẪN MẶC ĐỊNH (Không cần sửa)
WP_POSTS_URL = "https://huynhkhang.com/wp-json/wp/v2/posts"
WP_TAGS_URL = WP_POSTS_URL.replace("posts", "tags")
WP_CAT_URL = WP_POSTS_URL.replace("posts", "categories")
WP_MEDIA_URL = WP_POSTS_URL.replace("posts", "media")

# 💥 ĐÃ SỬA: Chuyển sang đường dẫn tương đối để anh dễ di chuyển thư mục
GOOGLE_KEY_PATH = "google-key.json"
ZALO_TOKEN_PATH = "token.json"

# =========================================================
# 🚀 KHU VỰC 3: CẤU HÌNH TRẠM VỆ TINH (TUMBLR & WP CON)
# =========================================================

# 1. Chìa khóa API Tumblr
cons_key = "mS5HkTNvccY2pDhO82mqHtoRVcE4PoPQgoY3nAz3DQ5IQH06RN"
cons_sec = "gRboNg2pdnitN8MPO45b92qivR9Kozas1xeb7UZIpnC0S35G2R"
oa_tok   = "JsdCWxDQMpdhIW18z1V3k43ErRYluPLClnFsopxVV2PTTRzB5J"
oa_sec   = "7qHXKJNy5GkPpXHlEm93GSbRAg554i4usdv6tSOa5QzpUkJOEZ"

# 2. Tài khoản đăng bài WordPress Vệ tinh
WP_VT_USER = "huynhkhangpt02"
WP_VT_PASS = "vfqumrev7jhhytw5"