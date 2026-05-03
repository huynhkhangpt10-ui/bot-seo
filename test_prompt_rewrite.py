"""
Script test pipeline prompt moi - khong dang web
Chay: python test_prompt_rewrite.py
"""

import sys
from datetime import datetime
from module_content import sinh_dan_y, sinh_bai_viet
from module_scenarios import phan_loai_kich_ban


def test_pipeline(tu_khoa_test):
    log_file = f"test_log_{tu_khoa_test.replace(' ', '_')[:30]}.txt"

    def log(msg):
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
        try:
            print(msg)
        except:
            pass

    log(f"\n{'='*60}")
    log(f"TEST: {tu_khoa_test}")
    log(f"{'='*60}\n")

    def cap_nhat_trang_thai(msg):
        log(f"[STATUS] {msg}")

    # Sinh outline
    log("\n--- SINH OUTLINE ---")
    lenh_tim_kiem = f"Tim kiem Google: {tu_khoa_test}"

    ok_outline, outline_auto, tieu_de_seo, meta_seo, tu_khoa_phu = sinh_dan_y(
        tu_khoa_test, "", lenh_tim_kiem, cap_nhat_trang_thai
    )

    if not ok_outline:
        log(f"\nLOI OUTLINE: {outline_auto}")
        return False

    log(f"\nOUTLINE OK")
    log(f"Tieu de: {tieu_de_seo}")
    log(f"Meta: {meta_seo}")

    # Sinh bai viet
    log("\n--- SINH BAI VIET ---")

    short_slug = tu_khoa_test.lower().replace(" ", "-")
    link_ins = "[LINK DANH CHO HOP BAI LIEN QUAN]: TRONG!\n"
    nam_hien_tai = datetime.now().year

    config_kich_ban = phan_loai_kich_ban(
        tu_khoa_test, nam_hien_tai, "khach hang", "Quan 1"
    )

    ok_bai, bai_viet = sinh_bai_viet(
        tu_khoa_test, tieu_de_seo, short_slug, link_ins, outline_auto,
        nam_hien_tai, "khach hang", "Quan 1", lenh_tim_kiem,
        cap_nhat_trang_thai
    )

    if not ok_bai:
        log(f"\nLOI BAI VIET: {bai_viet}")
        return False

    log(f"\nBAI VIET OK - {len(bai_viet)} ky tu")

    # Kiem tra
    log("\n--- KIEM TRA ---")
    checks = {
        "Markdown ##": "##" in bai_viet,
        "TL;DR box": "<div" in bai_viet,
        "FAQ": "hoi" in bai_viet.lower(),
        "Schema": "<script" in bai_viet,
        "Khong LSI": "LSI" not in bai_viet,
        "Khong AEO": "AEO" not in bai_viet,
        "Khong Tan Uyen": "Tan Uyen" not in bai_viet,
        "Co TP.HCM": any(x in bai_viet for x in ["Quan", "Thu Duc"])
    }

    for name, result in checks.items():
        log(f"{'OK' if result else 'FAIL'} {name}")

    # Luu output
    output_file = f"test_output_{tu_khoa_test.replace(' ', '_')[:30]}.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"<!-- {tu_khoa_test} -->\n")
        f.write(f"<h1>{tieu_de_seo}</h1>\n")
        f.write(f"<p><em>{meta_seo}</em></p>\n\n")
        f.write(bai_viet)

    log(f"\nLuu: {output_file}")
    log(f"Log: {log_file}")

    return True


if __name__ == "__main__":
    print("TEST PIPELINE")

    if len(sys.argv) > 1:
        tu_khoa = " ".join(sys.argv[1:])
    else:
        tu_khoa = "loi photoshop khong mo duoc"

    try:
        test_pipeline(tu_khoa)
        print("\nHOAN TAT")
    except Exception as e:
        print(f"\nLOI: {e}")
        import traceback
        traceback.print_exc()
