"""
BẢNG ĐIỀU KHIỂN TRUNG TÂM – HUỲNH KHANG IT
Auto-update: khi source App_Quan_Ly.pyw thay đổi, exe tự nhận biết và build lại.
"""
import tkinter as tk
from tkinter import messagebox, ttk
import subprocess, os, sys, json, hashlib, threading, shutil, socket, time
from datetime import datetime

# ── Đường dẫn cốt lõi ─────────────────────────────────────────────────────────
BASE_DIR = r"D:\Bot_SEO"
SOURCE   = os.path.join(BASE_DIR, "App_Quan_Ly.pyw")
IS_EXE   = getattr(sys, "frozen", False)

# ── Lấy đúng python.exe dù chạy từ source hay từ exe đóng gói ────────────────
def _tim_python():
    # Khi đóng gói, sys.executable = App_Quan_Ly.exe → không dùng được
    # Đọc python_path đã lưu trong build_info.json lúc build
    if IS_EXE:
        try:
            info_path = os.path.join(sys._MEIPASS, "build_info.json")
            with open(info_path, "r") as f:
                p = json.load(f).get("python_path", "")
            if p and os.path.exists(p):
                return p
        except Exception:
            pass
        # Fallback: tìm python trong PATH
        found = shutil.which("python") or shutil.which("python3")
        return found or "python"
    # Khi chạy source .pyw: sys.executable là python.exe thật
    return sys.executable

PYTHON = _tim_python()

# ── Đọc build_info.json được nhúng trong exe ─────────────────────────────────
def _bundled_dir():
    return sys._MEIPASS if IS_EXE else os.path.dirname(os.path.abspath(__file__))

def _doc_hash_da_build():
    try:
        with open(os.path.join(_bundled_dir(), "build_info.json"), "r") as f:
            return json.load(f).get("hash", "")
    except Exception:
        return ""

def _tinh_hash_source():
    try:
        with open(SOURCE, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return ""

def co_cap_nhat():
    if not IS_EXE or not os.path.exists(SOURCE):
        return False
    return _tinh_hash_source() != _doc_hash_da_build()

# ── Ghi log lỗi ──────────────────────────────────────────────────────────────
LOG_FILE = os.path.join(BASE_DIR, "error_log.txt")

def _ghi_log_process(ten, proc):
    """Chạy trong thread: đọc stdout+stderr, ghi vào error_log.txt, phát hiện crash."""
    with open(LOG_FILE, "a", encoding="utf-8", errors="replace") as f:
        f.write(f"\n{'='*60}\n[{datetime.now():%Y-%m-%d %H:%M:%S}] {ten} STARTED\n"
                f"Python: {PYTHON}\nCWD: {BASE_DIR}\n{'='*60}\n")
        f.flush()
        # Đọc stdout + stderr cùng lúc
        for line in proc.stdout:
            f.write(line); f.flush()
        ret = proc.wait()
        status = "OK" if ret == 0 else f"CRASH (exit={ret})"
        f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {ten} EXITED — {status}\n")
        f.flush()
        # Nếu crash, cập nhật đèn trạng thái về đỏ
        if ret != 0:
            loai = "bot" if "app.py" in ten else "tool"
            root.after(0, lambda: cap_nhat_den(loai, False))
            root.after(0, lambda: messagebox.showerror(
                "Tiến trình bị crash!",
                f"{ten} đã thoát với mã lỗi {ret}.\n\n"
                f"Xem chi tiết tại:\n{LOG_FILE}"
            ))

# ── Chờ Streamlit sẵn sàng rồi mới mở browser ───────────────────────────────
def _cho_va_mo_browser(port, timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            s = socket.create_connection(("127.0.0.1", port), timeout=0.5)
            s.close()
            os.system(f"start http://localhost:{port}")
            return
        except OSError:
            time.sleep(0.5)
    os.system(f"start http://localhost:{port}")

def mo_browser_sau(port):
    threading.Thread(target=_cho_va_mo_browser, args=(port,), daemon=True).start()

def chay_process(script, port):
    """Chạy streamlit với đầy đủ cờ, bắt stderr vào log."""
    proc = subprocess.Popen(
        [
            PYTHON, "-m", "streamlit", "run", script,
            f"--server.port={port}",
            "--server.headless=true",
        ],
        cwd=BASE_DIR,
        creationflags=subprocess.CREATE_NO_WINDOW,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,   # gộp stderr vào stdout để đọc một luồng
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    ten = f"{script}:{port}"
    threading.Thread(target=_ghi_log_process, args=(ten, proc), daemon=True).start()
    return proc

# ── Bot / Tool actions ────────────────────────────────────────────────────────
def chay_bot_seo():
    try:
        chay_process("app.py", 8501)
        cap_nhat_den("bot", True)
        lbl_bot_status.config(text="● Đang khởi động…", fg="#f59e0b")
        mo_browser_sau(8501)
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể bật Bot SEO:\n\nPython: {PYTHON}\n\nChi tiết: {e}")

def tat_bot_seo():
    os.system('wmic process where "commandline like \'%streamlit run app.py%\'" call terminate >nul 2>&1')
    cap_nhat_den("bot", False)
    messagebox.showinfo("OK", "Đã tắt Bot Viết Bài!")

def chay_tool_tu_khoa():
    try:
        chay_process("tool_dao_tu_khoa.py", 8082)
        cap_nhat_den("tool", True)
        lbl_tool_status.config(text="● Đang khởi động…", fg="#f59e0b")
        mo_browser_sau(8082)
    except Exception as e:
        messagebox.showerror("Lỗi", f"Không thể bật Tool Từ Khóa:\n\nPython: {PYTHON}\n\nChi tiết: {e}")

def tat_tool_tu_khoa():
    os.system('wmic process where "commandline like \'%tool_dao_tu_khoa.py%\'" call terminate >nul 2>&1')
    cap_nhat_den("tool", False)
    messagebox.showinfo("OK", "Đã tắt Tool Đào Từ Khóa!")

def tat_tat_ca():
    os.system('wmic process where "commandline like \'%streamlit%\'" call terminate >nul 2>&1')
    cap_nhat_den("bot", False)
    cap_nhat_den("tool", False)
    messagebox.showinfo("OK", "Đã dọn sạch RAM và tắt toàn bộ hệ thống!")

def cap_nhat_den(loai, dang_chay):
    mau = "#2ecc71" if dang_chay else "#e74c3c"
    chu  = "● Đang chạy" if dang_chay else "● Đã tắt"
    (lbl_bot_status if loai == "bot" else lbl_tool_status).config(text=chu, fg=mau)

# ══════════════════════════════════════════════════════════════════════════════
# TỰ CẬP NHẬT
# ══════════════════════════════════════════════════════════════════════════════
def _chay_build_trong_luong(btn_update, bar, lbl_progress):
    btn_update.config(state="disabled", text="⏳ Đang build…")
    bar.start(12)
    lbl_progress.config(text="Đang compile… (khoảng 30-60 giây)")

    build_bat = os.path.join(BASE_DIR, "build_app.bat")
    ok = False
    try:
        result = subprocess.run(
            ["cmd", "/c", build_bat], cwd=BASE_DIR,
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        ok = (result.returncode == 0)
        if not ok:
            out = (result.stdout + "\n" + result.stderr)[-1500:]
            root.after(0, lambda: messagebox.showerror("Build thất bại", out))
    except Exception as e:
        root.after(0, lambda: messagebox.showerror("Lỗi", str(e)))

    bar.stop()
    if ok:
        new_exe = os.path.join(BASE_DIR, "dist", "App_Quan_Ly.exe")
        if not os.path.exists(new_exe):
            root.after(0, lambda: messagebox.showerror("Lỗi", "Không tìm thấy dist\\App_Quan_Ly.exe"))
            root.after(0, lambda: btn_update.config(state="normal", text="🔄 Thử lại"))
            return
        current_exe = sys.executable
        updater = os.path.join(BASE_DIR, "_do_update.bat")
        with open(updater, "w", encoding="ascii") as f:
            f.write(f'@echo off\nping -n 3 127.0.0.1 > nul\ncopy /y "{new_exe}" "{current_exe}"\nstart "" "{current_exe}"\ndel "%~f0"\n')
        root.after(0, lambda: _xac_nhan_va_khoi_dong_lai(updater))
    else:
        root.after(0, lambda: btn_update.config(state="normal", text="🔄 Thử lại"))

def _xac_nhan_va_khoi_dong_lai(updater):
    if messagebox.askyesno("Cập nhật thành công!", "Build hoàn tất!\nÁp dụng và khởi động lại ngay?"):
        subprocess.Popen(["cmd", "/c", updater], creationflags=subprocess.CREATE_NO_WINDOW)
        root.destroy()

def bat_dau_cap_nhat(btn_update, bar, lbl_progress):
    threading.Thread(target=_chay_build_trong_luong,
                     args=(btn_update, bar, lbl_progress), daemon=True).start()

# ══════════════════════════════════════════════════════════════════════════════
# GIAO DIỆN
# ══════════════════════════════════════════════════════════════════════════════
BG       = "#f0f2f5"
CARD_BG  = "#ffffff"
FONT_H   = ("Segoe UI", 13, "bold")
FONT_BTN = ("Segoe UI", 10, "bold")
FONT_CAP = ("Segoe UI",  8, "italic")
BTN_ON   = dict(bg="#d1fae5", fg="#065f46", activebackground="#a7f3d0")
BTN_OFF  = dict(bg="#fee2e2", fg="#991b1b", activebackground="#fecaca")
BTN_RED  = dict(bg="#dc2626", fg="white",   activebackground="#b91c1c")
BTN_BLUE = dict(bg="#dbeafe", fg="#1e40af", activebackground="#bfdbfe")
BTN_YLW  = dict(bg="#fef3c7", fg="#92400e", activebackground="#fde68a")

H = 460 if co_cap_nhat() else 410
root = tk.Tk()
root.title("Tram Dieu Khien – Huynh Khang IT")
root.geometry(f"450x{H}")
root.resizable(False, False)
root.configure(bg=BG)

# Tiêu đề
tk.Label(root, text="⚙️  BẢNG ĐIỀU KHIỂN TRUNG TÂM",
         font=FONT_H, bg=BG, fg="#1e293b").pack(pady=(16, 2))
mode_txt = "🛠 Dev mode" if not IS_EXE else f"📦 Exe  |  Python: ...{PYTHON[-30:]}"
tk.Label(root, text=mode_txt, font=("Segoe UI", 7), bg=BG, fg="#94a3b8").pack()
tk.Frame(root, height=1, bg="#cbd5e1").pack(fill="x", padx=20, pady=8)

# ── Banner cập nhật ────────────────────────────────────────────────────────────
if co_cap_nhat():
    banner = tk.Frame(root, bg="#fef9c3",
                      highlightbackground="#f59e0b", highlightthickness=1)
    banner.pack(fill="x", padx=20, pady=(0, 6), ipady=6)
    tk.Label(banner, text="🔄  Phát hiện code mới – có bản cập nhật!",
             font=("Segoe UI", 9, "bold"), bg="#fef9c3", fg="#92400e").pack(
             side="left", padx=10)
    lbl_progress = tk.Label(banner, text="", font=("Segoe UI", 8),
                             bg="#fef9c3", fg="#78350f")
    lbl_progress.pack(side="left", padx=4)
    bar = ttk.Progressbar(root, mode="indeterminate", length=410)
    bar.pack(padx=20, pady=(0, 4))
    btn_update = tk.Button(root, text="🔄 Cập nhật ngay",
                           font=("Segoe UI", 9, "bold"), cursor="hand2", **BTN_YLW)
    btn_update.config(command=lambda: bat_dau_cap_nhat(btn_update, bar, lbl_progress))
    btn_update.pack(pady=(0, 6))
    tk.Frame(root, height=1, bg="#cbd5e1").pack(fill="x", padx=20, pady=(0, 6))

# ── Card: Bot Viết Bài ────────────────────────────────────────────────────────
card1 = tk.Frame(root, bg=CARD_BG, highlightbackground="#e2e8f0", highlightthickness=1)
card1.pack(fill="x", padx=20, pady=5, ipady=8)
tk.Label(card1, text="🤖  Bot Viết Bài (port 8501)",
         font=("Segoe UI", 10, "bold"), bg=CARD_BG, fg="#1e293b").grid(
         row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(6, 2))
lbl_bot_status = tk.Label(card1, text="● Đã tắt",
                           font=("Segoe UI", 8), bg=CARD_BG, fg="#e74c3c")
lbl_bot_status.grid(row=0, column=2, sticky="e", padx=12)
tk.Button(card1, text="▶  Bật", font=FONT_BTN, width=12, cursor="hand2",
          command=chay_bot_seo, **BTN_ON).grid(row=1, column=0, padx=(12,4), pady=4)
tk.Button(card1, text="⏹  Tắt", font=FONT_BTN, width=12, cursor="hand2",
          command=tat_bot_seo, **BTN_OFF).grid(row=1, column=1, padx=4, pady=4)
tk.Button(card1, text="🌐 Mở Web", font=FONT_BTN, width=10, cursor="hand2",
          command=lambda: os.system("start http://localhost:8501"),
          **BTN_BLUE).grid(row=1, column=2, padx=(4,12), pady=4)

# ── Card: Tool Từ Khóa ───────────────────────────────────────────────────────
card2 = tk.Frame(root, bg=CARD_BG, highlightbackground="#e2e8f0", highlightthickness=1)
card2.pack(fill="x", padx=20, pady=5, ipady=8)
tk.Label(card2, text="🔍  Tool Đào Từ Khóa (port 8082)",
         font=("Segoe UI", 10, "bold"), bg=CARD_BG, fg="#1e293b").grid(
         row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(6, 2))
lbl_tool_status = tk.Label(card2, text="● Đã tắt",
                            font=("Segoe UI", 8), bg=CARD_BG, fg="#e74c3c")
lbl_tool_status.grid(row=0, column=2, sticky="e", padx=12)
tk.Button(card2, text="▶  Bật", font=FONT_BTN, width=12, cursor="hand2",
          command=chay_tool_tu_khoa, **BTN_ON).grid(row=1, column=0, padx=(12,4), pady=4)
tk.Button(card2, text="⏹  Tắt", font=FONT_BTN, width=12, cursor="hand2",
          command=tat_tool_tu_khoa, **BTN_OFF).grid(row=1, column=1, padx=4, pady=4)
tk.Button(card2, text="🌐 Mở Web", font=FONT_BTN, width=10, cursor="hand2",
          command=lambda: os.system("start http://localhost:8082"),
          **BTN_BLUE).grid(row=1, column=2, padx=(4,12), pady=4)

# ── Tắt tất cả ───────────────────────────────────────────────────────────────
tk.Frame(root, height=1, bg="#cbd5e1").pack(fill="x", padx=20, pady=(10, 4))
tk.Button(root, text="🛑  TẮT TOÀN BỘ & XẢ RAM",
          font=("Segoe UI", 11, "bold"), width=32, cursor="hand2",
          command=tat_tat_ca, **BTN_RED).pack(pady=6)
tk.Button(root, text="📋 Xem Log Lỗi (error_log.txt)",
          font=("Segoe UI", 8), bg=BG, fg="#64748b", relief="flat", cursor="hand2",
          command=lambda: os.system(f'notepad "{LOG_FILE}"')).pack(pady=(0, 2))
tk.Label(root, text="© 2026 Huynh Khang IT – Binh Duong",
         font=FONT_CAP, bg=BG, fg="#94a3b8").pack(side="bottom", pady=6)

root.mainloop()
