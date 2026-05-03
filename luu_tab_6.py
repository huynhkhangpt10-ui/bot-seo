# ----------------- TAB 6: CÀO WEB SANG PDF (PLAYWRIGHT) -----------------
with tab6:
    st.subheader("🕷️ Cào Dữ Liệu Động & Tự Động Bơm RAG")
    st.caption(
        "Cơ chế Chuẩn: Khóa chân tại trang chủ quét sạch Menu -> Đi in PDF tuần tự (Không cào lan man)."
    )

    urls_input = st.text_area(
        "🔗 Nhập URL gốc (Nhập 1 link tổng quan, Bot sẽ tự mò các link con):",
        height=100,
        placeholder="https://help.autodesk.com/view/ACD/2027/ENU/",
    )

    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        gioi_han_link = st.number_input(
            "🛑 Giới hạn số bài tối đa (Chống treo máy VPS):",
            min_value=10,
            max_value=10000,
            value=2000,
        )
    with col_opt2:
        tu_dong_nap = st.checkbox(
            "🧠 Cào xong tự động BƠM KIẾN THỨC vào Tab 5 (RAG)", value=True
        )

    output_folder = st.text_input(
        "📁 Thư mục lưu file (Mặc định cho RAG):", value="./Nguon_Tai_Lieu_Tho"
    )

    if st.button("🚀 BẮT ĐẦU TÀN SÁT & CÀO DỮ LIỆU", type="primary"):
        if urls_input:
            urls_ban_dau = [u.strip() for u in urls_input.split("\n") if u.strip()]
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

            progress_bar = st.progress(0)
            ket_qua_tra_ve = []

            # 💥 LUỒNG NGẦM XỬ LÝ PLAYWRIGHT
            def tien_trinh_cao_web(
                danh_sach_url_goc, thu_muc_luu, result_list, max_links, nap_rag
            ):
                try:
                    import asyncio
                    import urllib.parse
                    import re
                    import requests

                    if sys.platform == "win32":
                        asyncio.set_event_loop_policy(
                            asyncio.WindowsProactorEventLoopPolicy()
                        )

                    from playwright.sync_api import sync_playwright

                    with sync_playwright() as p:
                        browser = p.chromium.launch(
                            headless=True, args=["--disable-web-security"]
                        )
                        context = browser.new_context(
                            viewport={"width": 1280, "height": 1024}
                        )
                        page = context.new_page()

                        danh_sach_caw = danh_sach_url_goc.copy()
                        da_thay = set(danh_sach_url_goc)

                        # ==========================================================
                        # PHA 1: CHỐT CHẶN TẠI TRANG CHỦ - QUÉT & MỞ MENU
                        # ==========================================================
                        for url_goc in danh_sach_url_goc:
                            parsed_url = urllib.parse.urlparse(url_goc)
                            base_path = url_goc.split("?")[0]
                            if not base_path.endswith("/"):
                                base_path += "/"

                            result_list.append(
                                {
                                    "type": "info",
                                    "msg": f"📍 PHA 1: Khóa chân tại {base_path} để móc ruột Menu...",
                                }
                            )
                            link_moi_gom_duoc = []

                            # Vòi hút API ngầm thần tốc
                            toc_url = base_path + "toc.json"
                            try:
                                res = requests.get(toc_url, timeout=10)
                                if res.status_code == 200:
                                    links = re.findall(
                                        r'"href"\s*:\s*"(.*?)"', res.text
                                    )
                                    for l in links:
                                        full_link = urllib.parse.urljoin(base_path, l)
                                        link_moi_gom_duoc.append(full_link)
                            except:
                                pass

                            # Máy nghe lén cục bộ (Sniffer)
                            def bat_goi_tin_cuc_bo(response):
                                if response.request.resource_type in [
                                    "xhr",
                                    "fetch",
                                    "document",
                                    "script",
                                ]:
                                    try:
                                        text_data = response.text()
                                        guids = re.findall(
                                            r"guid=([A-Za-z0-9\-_]+)", text_data
                                        )
                                        for g in guids:
                                            link_moi_gom_duoc.append(
                                                f"{base_path}?guid={g}"
                                            )
                                    except:
                                        pass

                            page.on("response", bat_goi_tin_cuc_bo)

                            # Load trang chủ
                            page.goto(url_goc, wait_until="networkidle", timeout=60000)
                            time.sleep(3)

                            page.remove_listener("response", bat_goi_tin_cuc_bo)

                            result_list.append(
                                {
                                    "type": "info",
                                    "msg": f"🔨 Đang đập nát giao diện để mở toàn bộ menu ẩn (Chờ ~15s)...",
                                }
                            )

                            # Vòng lặp đập Menu (Khóa luồng đứng chờ menu xổ ra)
                            try:
                                for vong in range(25):
                                    expanders = page.query_selector_all(
                                        '.jstree-closed > i, [aria-expanded="false"], .tree-expander, .icon-plus, .fa-plus, li.closed > span, .toc-expander, li[data-expanded="false"]'
                                    )
                                    clicked = 0
                                    for el in expanders:
                                        try:
                                            if el.is_visible():
                                                el.click()
                                                clicked += 1
                                        except:
                                            pass

                                    if clicked == 0:
                                        break
                                    time.sleep(1)  # Bắt buộc chờ 1 giây cho menu bung
                            except Exception as e:
                                pass

                            time.sleep(3)  # Nghỉ chốt 3s

                            # Cào TẤT CẢ thẻ <a> đang hiển thị trên trang chủ
                            try:
                                dom_links = page.evaluate(f"""
                                    Array.from(document.querySelectorAll('a'))
                                         .map(a => a.href)
                                         .filter(href => href && href.startsWith('{base_path}'))
                                """)
                                for l in dom_links:
                                    link_moi_gom_duoc.append(l)
                            except:
                                pass

                            # Cú hack lấy mảng TOC từ JS (nếu có)
                            try:
                                js_links = page.evaluate("""
                                    let links = [];
                                    if(window.TOC !== undefined) {
                                        JSON.stringify(window.TOC, (key, value) => {
                                            if(typeof value === 'string' && value.includes('guid=')) links.push(value);
                                            return value;
                                        });
                                    }
                                    links;
                                """)
                                for l in js_links:
                                    if l.startswith("http"):
                                        link_moi_gom_duoc.append(l)
                                    else:
                                        link_moi_gom_duoc.append(
                                            f"{base_path}?guid="
                                            + re.search(
                                                r"guid=([A-Za-z0-9\-_]+)", l
                                            ).group(1)
                                            if re.search(r"guid=([A-Za-z0-9\-_]+)", l)
                                            else ""
                                        )
                            except:
                                pass

                            # Chốt sổ link, loại bỏ trùng lặp và giới hạn số lượng
                            for l in link_moi_gom_duoc:
                                if not l:
                                    continue
                                clean_link = l.split("#")[0]
                                if clean_link not in da_thay and "guid=" in clean_link:
                                    if len(danh_sach_caw) >= max_links:
                                        break  # Đạt giới hạn thì ngừng thêm
                                    da_thay.add(clean_link)
                                    danh_sach_caw.append(clean_link)

                            result_list.append(
                                {
                                    "type": "success",
                                    "msg": f"🎯 PHA 1 Xong! Đã chốt danh sách {len(danh_sach_caw)} bài viết để đi in.",
                                }
                            )

                        # ==========================================================
                        # PHA 2: ĐI IN PDF (KHÔNG QUÉT THÊM BẤT CỨ LINK NÀO NỮA)
                        # ==========================================================
                        thanh_cong = 0
                        tong_so_link = len(danh_sach_caw)

                        for idx, url_dang_cao in enumerate(danh_sach_caw):
                            try:
                                result_list.append(
                                    {
                                        "type": "info",
                                        "msg": f"[{idx+1}/{tong_so_link}] Đang in PDF: {url_dang_cao}",
                                    }
                                )

                                # Chỉ vô mở web (bịt mắt không nghe lén gói tin hay quét thẻ <a> nữa)
                                page.goto(
                                    url_dang_cao,
                                    wait_until="networkidle",
                                    timeout=60000,
                                )
                                time.sleep(1.5)

                                # Dọn dẹp DOM cho PDF trắng sạch
                                page.evaluate("""
                                    var xoa_rac = ['header', 'footer', '#left-nav-container', '.left-nav', 'nav', 'iframe', '.video-player', '.cookie-banner', '#feedback-widget', '.feedback-container', '.bottom-nav'];
                                    xoa_rac.forEach(sel => {
                                        document.querySelectorAll(sel).forEach(el => el.remove());
                                    });
                                    var main = document.querySelector('#main-container') || document.querySelector('.main-content') || document.body;
                                    if(main) { main.style.width = '100%'; main.style.padding = '0'; main.style.margin = '0'; }
                                """)
                                time.sleep(1)

                                safe_name = (
                                    f"tailieu_cao_{idx+1}_{int(time.time())}.pdf"
                                )
                                file_path = os.path.join(thu_muc_luu, safe_name)

                                page.pdf(
                                    path=file_path,
                                    format="A4",
                                    print_background=True,
                                    margin={
                                        "top": "1cm",
                                        "bottom": "1cm",
                                        "left": "1cm",
                                        "right": "1cm",
                                    },
                                )

                                thanh_cong += 1
                                result_list.append(
                                    {
                                        "type": "success",
                                        "msg": f"✅ Đã lưu PDF thành công.",
                                    }
                                )

                            except Exception as e:
                                result_list.append(
                                    {"type": "error", "msg": f"❌ Bỏ qua link do lỗi."}
                                )

                            result_list.append(
                                {"type": "progress", "value": (idx + 1) / tong_so_link}
                            )
                            time.sleep(0.5)

                        browser.close()

                        if nap_rag and thanh_cong > 0:
                            result_list.append(
                                {
                                    "type": "info",
                                    "msg": "🧠 Đang khởi động máy bơm kiến thức vào não AI...",
                                }
                            )
                            import nap_tai_lieu

                            nap_tai_lieu.nap_vao_kho()
                            result_list.append(
                                {
                                    "type": "success",
                                    "msg": "🚀 Bơm RAG hoàn tất! AI đã tiếp thu kiến thức mới.",
                                }
                            )

                        result_list.append(
                            {
                                "type": "done",
                                "thanh_cong": thanh_cong,
                                "tong": tong_so_link,
                            }
                        )

                except Exception as ex:
                    result_list.append({"type": "fatal", "msg": str(ex)})

            import threading

            thread_cao = threading.Thread(
                target=tien_trinh_cao_web,
                args=(
                    urls_ban_dau,
                    output_folder,
                    ket_qua_tra_ve,
                    gioi_han_link,
                    tu_dong_nap,
                ),
            )
            thread_cao.start()

            with st.spinner("Bot đang càn quét hệ thống, sếp pha ly cà phê đợi nhé..."):
                while thread_cao.is_alive() or len(ket_qua_tra_ve) > 0:
                    if len(ket_qua_tra_ve) > 0:
                        tin_hieu = ket_qua_tra_ve.pop(0)

                        if tin_hieu["type"] == "info":
                            st.write(tin_hieu["msg"])
                        elif tin_hieu["type"] == "success":
                            st.success(tin_hieu["msg"])
                        elif tin_hieu["type"] == "error":
                            st.error(tin_hieu["msg"])
                        elif tin_hieu["type"] == "progress":
                            progress_bar.progress(min(tin_hieu["value"], 1.0))
                        elif tin_hieu["type"] == "warning":
                            st.warning(tin_hieu["msg"])
                        elif tin_hieu["type"] == "done":
                            st.balloons()
                            st.success(
                                f"🎉 Chiến dịch tàn sát hoàn tất! Đã rút cạn {tin_hieu['thanh_cong']}/{tin_hieu['tong']} bài viết."
                            )
                        elif tin_hieu["type"] == "fatal":
                            st.error(f"❌ Lỗi hệ thống: {tin_hieu['msg']}")

                    time.sleep(0.1)

        else:
            st.warning("⚠️ Sếp dán link gốc vào ô đi đã!")
