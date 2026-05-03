"""
make_icon.py — Chuyển logo_hk.png thành icon.ico nhiều kích thước
Chạy: python make_icon.py
"""
import os
import sys

try:
    from PIL import Image
except ImportError:
    print("Cài Pillow: pip install pillow")
    sys.exit(1)

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)

# Tìm file logo
LOGO_PATH = os.path.join(PROJECT_DIR, "logo_hk.png")
ICON_PATH = os.path.join(SCRIPT_DIR, "icon.ico")

if not os.path.exists(LOGO_PATH):
    print(f"Không tìm thấy {LOGO_PATH}")
    sys.exit(1)

# Mở ảnh và tạo .ico với đầy đủ kích thước (giống icon app chuyên nghiệp)
img = Image.open(LOGO_PATH).convert("RGBA")

sizes = [(16,16), (24,24), (32,32), (48,48), (64,64), (128,128), (256,256)]
imgs  = [img.resize(s, Image.LANCZOS) for s in sizes]

imgs[0].save(
    ICON_PATH,
    format="ICO",
    sizes=sizes,
    append_images=imgs[1:],
)

print(f"OK: {ICON_PATH}")
