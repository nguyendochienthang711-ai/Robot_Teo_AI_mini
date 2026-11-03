# Tổng hợp Hệ thống Công cụ (Tools / Skills) cho Robot AI Trợ lý "Tèo"

Tài liệu này liệt kê toàn bộ các công cụ (Function Calling / FastMCP Tools) dành cho robot **Tèo** (kết hợp giữa phần cứng ESP32-S3 thân trên kiểu WALL-E + **Đế 3 bánh xe đa hướng Omni LeKiwi** và máy chủ Laptop HP Victus 15). Danh sách bao gồm cả các công cụ đã có trong kế hoạch gốc lẫn các **công cụ mở rộng mới** giúp Tèo thực sự trở thành một "thư ký bàn làm việc" đắc lực.

---

## 💡 Nguyên tắc vàng khi thiết kế Tool cho Tèo (Tiết kiệm Token & Giữ Cache)

Để không vượt quá giới hạn **10–15 công cụ** gửi kèm trong mỗi lượt gọi LLM (giúp `deepseek-flash` gọi hàm chuẩn xác và giữ nguyên Prompt Cache), bạn không nên tách mỗi hành động nhỏ thành 1 tool riêng lẻ. Thay vào đó, hãy dùng **Kỹ thuật Gộp hàm (Consolidated Tool)**:
* **Ví dụ:** Thay vì viết 4 hàm `them_todo`, `xem_todo`, `xoa_todo`, `sua_todo`, chỉ cần viết **1 hàm duy nhất** là `quan_ly_cong_viec(thao_tac="them" | "xem" | "xoa", noi_dung="...")`.
* Nhờ cách gộp này, toàn bộ **28 tính năng** dưới đây có thể gói gọn vào đúng **12–14 Tool Schema** cốt lõi.

---

## Nhóm 1: Thư ký Cá nhân, Quản lý Thời gian & Sức khỏe (5 Tools)

Đây là nhóm công cụ dùng hằng ngày nhiều nhất khi bạn ngồi học tập và làm việc trước chiếc HP Victus 15.

| STT | Tên Tool gợi ý | Nguồn | Tác dụng & Tình huống sử dụng thực tế | Phân loại an toàn |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **`quan_ly_cong_viec`** *(Todo & Nhắc việc)* | Đã triển khai (`tools.py`) | Thêm việc mới, đánh dấu hoàn thành, xóa hoặc đọc danh sách các việc cần làm trong ngày. <br>*Ví dụ:* "Tèo ơi ghi chú giúp anh 3 giờ chiều nay nộp báo cáo AI nhé." | Chỉ đọc / Ghi file JSON nội bộ (An toàn) |
| 2 | **`so_tay_ghi_chu_nhanh`** *(Quick Brain-Dump / Idea Note)* | Có trong kế hoạch (Mở rộng) | Lưu nhanh một ý tưởng chợt nảy ra, một câu trích dẫn hoặc mật khẩu/đường link vào file Markdown (hoặc thư mục Obsidian/Notion trên laptop) kèm nhãn thời gian mà không cần mở trình soạn thảo. <br>*Ví dụ:* "Tèo ơi lưu vào sổ tay ý tưởng: dùng cảm biến chạm dán dưới nắp hộp." | Ghi file văn bản (An toàn) |
| 3 | **`dong_ho_tap_trung_pomodoro`** *(Timer / Báo thức / Pomodoro)* | **Mới bổ sung** | Đặt hẹn giờ đếm ngược (ví dụ 25 phút học bài, 5 phút nghỉ, hoặc "10 phút nữa nhắc anh tắt bếp"). Khi hết giờ, Tèo tự động phát giọng nói thông báo kết hợp trượt ngang vẫy 2 tay và chớp mắt trên màn hình. | Chạy nền bất đồng bộ (An toàn) |
| 4 | **`ban_tin_buoi_sang`** *(Morning Briefing)* | Có trong kế hoạch (Mục 11) | Tự động tổng hợp 4 thông tin trong 1 lần gọi: Thời tiết hiện tại + Số việc cần làm hôm nay trong Todo + Lịch trình trong ngày + 3 tin tức công nghệ nổi bật. Có thể kích hoạt tự động khi cảm biến `HLK-LD2410C` thấy bạn ngồi vào bàn buổi sáng. | Chỉ đọc (An toàn) |
| 5 | **`nhac_nho_suc_khoe_ban_lam_viec`** *(Health & Posture Coach)* | **Mới bổ sung** | Kết hợp đồng hồ hệ thống và cảm biến hiện diện `LD2410C`: Nếu thấy bạn ngồi liên tục trước laptop quá 60–90 phút không rời bàn, Tèo chủ động trượt nhẹ sang nhắc bạn uống nước, chớp mắt giảm mỏi hoặc đứng dậy vươn vai. | Chạy nền (An toàn) |

---

## Nhóm 2: Đọc, Tóm tắt, Dịch thuật & Xử lý Tài liệu (6 Tools)

Nhóm công cụ biến Tèo thành trợ lý xử lý văn bản, tận dụng tối đa giọng đọc **Piper VITS Offline** tốc độ cao (60–120ms) và khả năng đọc tài liệu của `markitdown`.

| STT | Tên Tool gợi ý | Nguồn | Tác dụng & Tình huống sử dụng thực tế | Phân loại an toàn |
| :--- | :--- | :--- | :--- | :--- |
| 6 | **`doc_hoac_tom_tat_tai_lieu`** *(Document Reader & Summarizer)* | Đã triển khai (`doc_reader.py`) | Hỗ trợ 2 chế độ cho file `.pdf`, `.docx`, `.pptx`, `.txt`, `.md`:<br>1. **Tóm tắt:** Trích xuất nội dung và nhờ DeepSeek tóm tắt các ý chính trong 3 câu.<br>2. **Đọc nguyên văn (0 tốn token LLM):** Cắt văn bản thành câu, đẩy thẳng qua Piper TTS đọc to và **tự lưu Bookmark vị trí câu** (hỗ trợ lệnh: *đọc từ đầu, đọc tiếp, đọc lại câu vừa rồi, dừng*). | Chỉ đọc / Chạy nền (An toàn) |
| 7 | **`ke_chuyen_va_doc_sach`** *(Storyteller & Audiobook)* | Có trong kế hoạch (Mục 6.8) | Đọc sách/ebook cá nhân theo chương (nhớ vị trí đang nghe dở) hoặc yêu cầu LLM tự sáng tác một câu chuyện ngắn (truyện cười, truyện cổ tích, truyện khoa học viễn tưởng) rồi đọc truyền cảm bằng các giọng `diemdam` hoặc `tramvang`. | Chỉ đọc (An toàn) |
| 8 | **`tim_kiem_tai_lieu_rag`** *(Local Knowledge Search)* | Có trong kế hoạch (Mục 6.4) | Dùng model embedding `bge-m3` chạy trên CPU tìm kiếm chính xác đoạn thông tin nằm trong hàng trăm file PDF/bài giảng/tài liệu cá nhân trên ổ cứng của bạn. Chỉ gửi đoạn văn bản liên quan lên LLM để trả lời câu hỏi. | Chỉ đọc cục bộ (Bảo mật cao) |
| 9 | **`dich_thuat_da_ngon_ngu`** *(Smart Translator)* | Có trong kế hoạch (Mục 6.9) | Dịch một câu nói trực tiếp, dịch toàn bộ một file tài liệu rồi lưu ra bản mới, hoặc bật **Chế độ Phiên dịch 2 chiều** (tự động chuyển sang `GoogleTTS` giọng bản xứ Anh/Trung/Nhật khi đọc câu dịch). | Chỉ đọc / Ghi bản dịch (An toàn) |
| 10 | **`xu_ly_bo_nho_tam_clipboard`** *(Clipboard Assistant)* | **Mới bổ sung (Rất thực dụng)** | Đọc trực tiếp đoạn văn bản hoặc đoạn code mà bạn vừa bôi đen và bấm **`Ctrl + C`** trên laptop. Bạn chỉ cần bấm `Ctrl + C` một đoạn tiếng Anh dài trên web rồi bảo: *"Tèo ơi dịch và tóm tắt đoạn anh vừa copy với"* hoặc *"Kiểm tra xem đoạn code anh vừa copy bị lỗi gì"*. | Chỉ đọc Clipboard (An toàn) |
| 11 | **`ghi_nho_thong_tin_dai_han`** *(Long-Term Personal Memory)* | **Mới bổ sung** | Lưu lại các thông tin cá nhân, thói quen, sở thích hoặc thông tin quan trọng của bạn vào bộ nhớ dài hạn (`teo_memory.json`). <br>*Ví dụ:* "Tèo nhớ nhé, số phòng học môn AI của anh là P.402 nhà A1". Tuần sau hỏi lại Tèo vẫn nhớ chính xác dù đã tắt máy nhiều lần. | Ghi file JSON nội bộ (An toàn) |

---

## Nhóm 3: Thị giác Máy tính – Nhìn Đời thực & Nhìn Màn hình (3 Tools)

Giúp Tèo có "đôi mắt" vừa nhìn được thế giới bên ngoài qua Camera ESP32, vừa nhìn được những gì đang diễn ra trên màn hình chiếc HP Victus 15.

| STT | Tên Tool gợi ý | Nguồn | Tác dụng & Tình huống sử dụng thực tế | Phân loại an toàn |
| :--- | :--- | :--- | :--- | :--- |
| 12 | **`nhin_qua_camera_teo`** *(Physical World Vision)* | Có trong kế hoạch (Mục 4.2 & 6.5) | Gọi HTTP `/capture` tới module camera trên người Tèo để chụp vật thể bạn đang cầm trước mặt robot, sau đó gửi lên `deepseek-flash` (Vision) để hỏi đáp, dịch chữ trên bao bì/thực đơn, hoặc giải bài tập viết tay trên giấy. | Cần bật đèn LED báo hiệu khi chụp |
| 13 | **`nhin_man_hinh_laptop`** *(Screen Vision Assistant)* | **Mới bổ sung** | Chụp nhanh ảnh màn hình (Screenshot) cửa sổ bạn đang mở trên laptop HP Victus 15 gửi cho model thị giác. Cực kỳ hữu ích khi bạn đang xem một biểu đồ phức tạp, một thông báo lỗi phần mềm, hoặc một slide bài giảng bằng tiếng nước ngoài và nói: *"Tèo ơi nhìn màn hình giải thích giúp anh cái sơ đồ này với!"* | Cần lưu ý không chụp khi mở thông tin nhạy cảm |
| 14 | **`quet_hoa_don_chi_tieu_ocr`** *(Receipt OCR & Expense Tracker)* | Có trong kế hoạch (Mục 11) | Bạn đưa tờ hóa đơn mua hàng hoặc ảnh chụp chuyển khoản trước camera của Tèo (hoặc trên màn hình), Tèo tự đọc tên món hàng, tổng số tiền, ngày giờ rồi tự động cộng dồn vào bảng Excel/CSV quản lý chi tiêu tháng. | Ghi file bảng tính nội bộ |

---

## Nhóm 4: Điều khiển Laptop HP Victus 15 & Quản trị Hệ thống (5 Tools)

Biến giọng nói của bạn thành điều khiển từ xa cho chiếc laptop ngay cả khi bạn đang nằm trên giường hoặc đứng xa bàn làm việc.

| STT | Tên Tool gợi ý | Nguồn | Tác dụng & Tình huống sử dụng thực tế | Phân loại an toàn |
| :--- | :--- | :--- | :--- | :--- |
| 15 | **`kiem_tra_suc_khoe_laptop`** *(System Diagnostics)* | Đã triển khai (`tools.py`) | Kiểm tra % Pin và trạng thái sạc, % CPU, % RAM đang dùng, dung lượng ổ cứng C/D còn trống và nhiệt độ/VRAM của card rời RTX 3050 6GB. | Chỉ đọc (An toàn) |
| 16 | **`mo_ung_dung_va_workspace`** *(App & Workspace Launcher)* | Có trong kế hoạch (Mục 6.2) | Mở nhanh một phần mềm (VS Code, Chrome, Word, Spotify, Calculator) hoặc **Mở theo Chế độ (Workspace)**: Ví dụ nói *"Tèo ơi bật chế độ học AI"* $\rightarrow$ Laptop tự động mở cùng lúc VS Code, thư mục đồ án và trang tài liệu học tập. | Chỉ mở ứng dụng trong danh sách cho phép (`allowlist`) |
| 17 | **`tim_va_don_dep_file`** *(Smart File Finder & Organizer)* | Có trong kế hoạch (Mở rộng) | • **Tìm file:** Tìm nhanh file trong máy theo tên hoặc ngày sửa đổi (*"Tìm giúp anh file báo cáo PDF anh mới tải hôm qua"*).<br>• **Dọn thư mục Downloads:** Tự động phân loại các file bừa bộn trong thư mục `Downloads` vào các thư mục con gọn gàng (`Anh/`, `Tai_lieu_PDF/`, `Bo_cai_dat/`, `Nen_ZIP/`). | Giới hạn trong `ALLOWED_DIRS` + Không tự xóa file |
| 18 | **`dieu_khien_he_thong_windows`** *(System Power & Screen Control)* | Có trong kế hoạch (Mục 6.2 & 7) | Điều khiển các thao tác hệ thống của laptop:<br>• Khóa màn hình ngay lập tức (`Win + L`).<br>• Tắt màn hình (nhưng giữ máy chạy ngầm).<br>• Chỉnh độ sáng màn hình hoặc âm lượng tổng.<br>• Hẹn giờ tắt máy (`shutdown`) hoặc ngủ đông (`hibernate`). | **Nhạy cảm:** Bắt buộc hỏi xác nhận giọng nói trước khi tắt máy |
| 19 | **`kiem_tra_ket_noi_mang`** *(Network & Ping Checker)* | **Mới bổ sung** | Kiểm tra tốc độ phản hồi (Ping) tới Google/DeepSeek, địa chỉ IP LAN hiện tại của laptop và trạng thái kết nối WebSocket với mạch ESP32-S3 khi bạn thấy mạng có vẻ chậm. | Chỉ đọc (An toàn) |

---

## Nhóm 5: Giải trí, Âm nhạc & Điều khiển Giọng nói (3 Tools)

| STT | Tên Tool gợi ý | Nguồn | Tác dụng & Tình huống sử dụng thực tế | Phân loại an toàn |
| :--- | :--- | :--- | :--- | :--- |
| 20 | **`phat_nhac_youtube`** *(YouTube & Media Controller)* | Đã triển khai (`tools.py`) | Tìm kiếm và bật nhạc/video trên YouTube (hoặc trình phát nền `mpv`), hỗ trợ các lệnh điều khiển media: *Tạm dừng nhạc, Phát tiếp, Bài tiếp theo, Tăng/giảm âm lượng nhạc*. Kết hợp tự động với hook `pycaw` hạ nhạc xuống 15% khi bạn gọi Tèo. | An toàn |
| 21 | **`doi_giong_teo`** *(Voice Profile Switcher)* | Đã triển khai (`tools.py` & `audio_io.py`) | Cho phép bạn ra lệnh đổi chất giọng của Tèo ngay trong cuộc trò chuyện giữa các cấu hình Piper VITS Offline: Giọng Sóc chuột dễ thương (`chipmunk`), Giọng Nam trầm điềm đạm (`diemdam`), Giọng Nam trầm vang (`tramvang`) hoặc Giọng Nữ Google (`google`). | An toàn |
| 22 | **`tro_choi_do_vui_va_flashcard`** *(Quiz & Study Buddy)* | **Mới bổ sung** | Giúp bạn ôn bài hoặc giải trí: Tèo đọc câu hỏi trắc nghiệm / từ vựng tiếng Anh từ một file tài liệu ôn thi của bạn, lắng nghe câu trả lời của bạn rồi chấm điểm và giải thích đáp án đúng. | Chỉ đọc (An toàn) |

---

## Nhóm 6: Điều khiển Cơ thể Vật lý & Đế 3 bánh Omni LeKiwi (3 Tools)

Nhóm công cụ giao tiếp trực tiếp với cửa sổ mô phỏng 3D `MuJoCo` và mạch `ESP32-S3` + `PCA9685` (điều khiển 3 Servo thân trên `MG90S 180°` và 3 Servo bánh xe Omni `MG90S 360°`).

| STT | Tên Tool gợi ý | Nguồn | Tác dụng & Tình huống sử dụng thực tế | Phân loại an toàn |
| :--- | :--- | :--- | :--- | :--- |
| 23 | **`dieu_khien_co_the_teo`** *(Motion Bundle & Omni Dance)* | Đã triển khai (`tools.py`) | Kích hoạt các gói chuyển động mượt mà kết hợp cả cổ, 2 tay và đế 3 bánh Omni: Vẫy tay chào (`wave_greeting`), Gật đầu (`nod_yes`), Lắc đầu (`shake_no`), Nhảy múa tại chỗ (`happy_dance`), hoặc **Nhảy trượt ngang Moonwalk theo nhịp nhạc BPM (`moonwalk_dance`)**. | Tự động khóa động cơ khi Mic đang thu âm |
| 24 | **`di_chuyen_da_huong_omni`** *(Holonomic Kiwi Drive Navigation)* | **Nâng cấp từ `LeKiwi`** | Điều khiển đế 3 bánh xe Omni di chuyển toàn hướng trên mặt bàn: Tiến (`move_forward`), Lùi (`move_backward`), **Trượt ngang sang trái (`slide_left`)**, **Trượt ngang sang phải (`slide_right`)**, **Lượn vòng cung giữ nguyên hướng mắt nhìn chủ nhân (`circle_strafe`)**, hoặc Xoay tròn tại chỗ (`spin_around`). Luôn đi kèm kiểm tra 3 cảm biến hồng ngoại IR chống rơi mép bàn. | Có giới hạn thời gian chạy mỗi lệnh (1–3 giây) |
| 25 | **`bieu_cam_khuon_mat_va_led`** *(LCD Eyes & RGB Mood)* | Có trong kế hoạch (Mục 5.1 & 11) | Thay đổi biểu cảm đôi mắt hoạt hình trên màn hình LCD ST7789 (Vui vẻ, Ngạc nhiên, Nghi ngờ, Buồn ngủ, Mắt trái tim, Chóng mặt) và đổi hiệu ứng màu sắc của vòng đèn LED `WS2812` theo tâm trạng câu trả lời. | An toàn |

---

## Nhóm 7: Họp hành, Tra cứu Internet & Kết nối Điện thoại (3 Tools)

| STT | Tên Tool gợi ý | Nguồn | Tác dụng & Tình huống sử dụng thực tế | Phân loại an toàn |
| :--- | :--- | :--- | :--- | :--- |
| 26 | **`tra_cuu_thong_tin_truc_tuyen`** *(Web Search & Weather/Finance)* | Có trong kế hoạch (Mục 6.2 & 11) | Tra cứu thông tin thời gian thực mà LLM không biết sẵn: Thời tiết theo giờ tại khu vực của bạn, tỷ giá ngoại tệ, giá vàng, lịch thi đấu thể thao hoặc tìm kiếm nhanh trên Internet (qua DuckDuckGo / Tavily miễn phí). | Chỉ đọc (An toàn) |
| 27 | **`tro_ly_ghi_am_cuoc_hop`** *(Meeting Recorder & Summarizer)* | Có trong kế hoạch (Mục 11) | Khi bạn tham gia họp trực tuyến hoặc nghe giảng, bảo *"Tèo ơi bắt đầu ghi âm cuộc họp nhé"*. Tèo thu âm nền, dùng Whisper chuyển toàn bộ thành văn bản, sau đó tóm tắt các ý chính và trích xuất danh sách việc cần làm lưu thành file Markdown. | Chạy nền bất đồng bộ (`agent_task`) |
| 28 | **`gui_tin_nhan_telegram`** *(Phone Bridge via Telegram Bot)* | Có trong kế hoạch (Mục 11) | Khi bạn đang vội ra khỏi phòng mà muốn mang theo thông tin vừa hỏi Tèo, chỉ cần nói: *"Tèo ơi gửi cái danh sách việc cần làm và địa chỉ vừa tìm được qua Telegram điện thoại cho anh!"* — Tèo bắn tin nhắn hoặc file PDF thẳng vào điện thoại của bạn trong 1 giây. | Cần xác nhận hoặc chỉ gửi tới `CHAT_ID` cố định của chủ nhân |