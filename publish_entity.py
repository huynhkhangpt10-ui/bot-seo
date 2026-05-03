import sys
import re

sys.stdout.reconfigure(encoding="utf-8")

from master_api import post_to_blogger, post_to_wordpress, post_to_tumblr

# ── 1. Đọc file bài viết entity ──────────────────────────────────────────────
with open("entity_article.html", "r", encoding="utf-8") as f:
    raw = f.read()

# ── 2. Tách tiêu đề từ tag [TITLE]...[/TITLE] ────────────────────────────────
title_match = re.search(r'\[TITLE\](.*?)\[/TITLE\]', raw, re.IGNORECASE | re.DOTALL)
title = title_match.group(1).strip() if title_match else "Dịch Vụ Tận Nơi Huỳnh Khang"

# ── 3. Dọn nội dung: bỏ [TITLE] tag, comments, schema <script> ───────────────
content = re.sub(r'\[TITLE\].*?\[/TITLE\]', '', raw, flags=re.IGNORECASE | re.DOTALL)
content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
content = content.strip()

TAGS = [
    "Dịch Vụ Huỳnh Khang",
    "Sửa Máy Tính Bình Dương",
    "Sửa Laptop Tân Uyên",
    "Phần Mềm Bản Quyền",
    "Entity SEO 2026",
]

print(f"📋 Tiêu đề  : {title}")
print(f"📄 Nội dung : {len(content):,} ký tự\n")
print("=" * 55)

# ── 4. Đăng lên 5 vệ tinh ────────────────────────────────────────────────────
post_to_blogger(title, content, TAGS)   # Blogger Bình Dương + Tân Uyên
post_to_wordpress(title, content)       # WP caiwinbinhduong + suamaytinhtanuyen
post_to_tumblr(title, content, TAGS)    # Tumblr dichvuhuynhkhang

print("\n" + "=" * 55)
print("🎉 Hoàn thành! Bài entity đã đăng lên cả 5 vệ tinh.")
