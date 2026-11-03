# Kế hoạch dự án Robot AI trợ lý "Tèo" (ESP32-S3 + xiaozhi-esp32 + HP Victus 15)

Cập nhật: 03/11/2026 (Bản hoàn thiện sau khi nâng cấp Đế 3 bánh Omni LeKiwi & Giọng Piper VITS Offline)

> Giá, hạn mức miễn phí và tên model thay đổi rất nhanh. Mọi con số trong file này cần được đối chiếu với trang chính thức trước khi mua phần cứng hoặc nạp tiền API.

---

## 1. Quyết định đã chốt

| Hạng mục | Quyết định |
| :--- | :--- |
| **Tên gọi & Wake Word** | Tên robot là **"Tèo"**; gọi bằng từ khóa **`"Ê Tèo"`** hoặc **`"Tèo ơi"`** (tự huấn luyện bằng giọng thật trên **Edge Impulse** nhúng vào ESP32-S3, kết hợp chế độ **Hội thoại liên tục** không cần gọi lại ở từng câu). |
| **Kích hoạt phụ trợ** | Phím tắt **`Alt + Space`** (hoặc `Enter`) trên bàn phím laptop + **Cảm biến chạm điện dung TTP223** dán ẩn dưới đỉnh đầu (để vỗ tắt tiếng nhanh, xoa đầu hoặc gọi trong đêm khuya) thay cho nút BOOT cứng. |
| **Mục đích** | Dùng hằng ngày như một trợ lý thư ký để bàn. |
| **Server** | Chính laptop **HP Victus 15 (16GB RAM, RTX 3050 6GB VRAM)**, **không thuê server** và **không cần mua Raspberry Pi 5** (tiết kiệm ~2,3 triệu đồng vì mọi tác vụ nặng đã có laptop gánh qua Wi-Fi LAN). |
| **LLM & Thị giác** | **DeepSeek** (dòng Flash — id `deepseek-flash` tích hợp sẵn cả xử lý văn bản và thị giác). |
| **Giọng nói (TTS)** | **Piper VITS Offline** đã tinh chỉnh dấu tiếng Việt (3 phong cách: `chipmunk` sóc chuột, `diemdam` nam trầm điềm đạm, `tramvang` trầm vang — độ trễ siêu tốc ~60–120ms, tốn 0 đồng) + **Google TTS** tự động cho câu ngoại ngữ (`en`, `zh`, `ja`). |
| **Vận hành nguồn** | Laptop **không cho ngủ khi cắm sạc, chỉ tắt màn hình** (mục 7, Hướng 1) kèm cơ chế giữ GPU nghỉ khi nhàn rỗi. Không cần chạy 24/7: nếu tắt laptop hẳn thì bật lại, khởi động dưới 5 phút là chấp nhận được. |
| **Giữ lại** | Màn hình LCD, camera, 3 servo thân trên (cổ + 2 tay), cảm biến hiện diện (`HLK-LD2410C`), pin 2S 18650 (2 nhánh hạ áp độc lập), voiceprint (tích hợp trong model Wake Word của Edge Impulse), RAG. |
| **Tính năng thêm** | Phát nhạc/YouTube kèm hook `pycaw` tự vặn nhỏ nhạc khi nói (6.7), tóm tắt và đọc to văn bản (6.6), đọc truyện (6.8), dịch thuật tự đổi giọng TTS (6.9), đung đưa/nhảy trượt ngang theo nhịp nhạc bằng cơ chế **Motion Bundle** (5.4), tự động hóa viết code kỹ năng mới bằng **`AGENTS.md` & `.claude/skills`** (6.2). |
| **Hình dáng & Đế di chuyển** | Chiều cao cỡ một lon Red Bull; phần thân trên kiểu **WALL-E** (thân hộp, đầu gắn cổ, hai tay) kết hợp **Đế tròn 3 bánh xe đa hướng (3-Wheel Omni / Kiwi Drive học từ `LeKiwi`, đường kính 10–12 cm)**. **Đã bỏ đế bánh xích và hướng nhiều chân.** Dùng duy nhất 1 module **PCA9685 (16 kênh PWM)** để cắm thẳng cả 3 Servo thân trên (`MG90S 180°`) lẫn 3 Servo bánh xe (`MG90S 360°`), **không cần mạch cầu H `DRV8833`**. |
| **Vỏ robot** | Chưa cần đẹp (hộp nhựa hoặc bìa carton cứng ở giai đoạn đầu). |
| **Ưu tiên** | Tổng chi phí thấp nhất (phần cứng + phí API). |

Hệ quả: Bỏ failover cloud, mini server luôn bật và toàn bộ rắc rối về sleep/Wake-on-LAN. Laptop tắt hẳn thì robot không dùng được, và với cách dùng này thì hoàn toàn chấp nhận.

---

## 2. Những điểm cần kiểm chứng & Giải pháp khắc phục từ tài liệu gốc

Tài liệu gốc (kiến trúc hybrid edge-cloud) có ý tưởng tốt nhưng đã được hiệu chỉnh các điểm sau:

1. **Xử lý Tiếng Việt & Từ khóa đánh thức ("Ê Tèo"):**
   * **ASR (Nghe câu lệnh):** Dùng **Google ASR / Groq Whisper (`whisper-large-v3-turbo`)** làm mặc định (để card rời RTX 3050 6GB được nghỉ ở mức 0W khi tắt màn hình) và **`faster-whisper turbo (int8)` trên RTX 3050** làm dự phòng cục bộ.
   * **TTS (Đọc phản hồi):** Đã kiểm chứng và chốt dùng **Piper VITS Offline** (nạp sẵn trong RAM, phản hồi 60–120ms, hỗ trợ đổi giọng `chipmunk` / `diemdam` / `tramvang` bằng giọng nói) kết hợp **Google TTS HTTP Keep-Alive** (~180ms) khi đọc ngoại ngữ. Giải quyết triệt để lỗi nghẽn mạng buổi tối và lỗi `NoAudioReceived` của `EdgeTTS`.
   * **Wake Word + Voiceprint:** Tự thu âm giọng thật từ khóa **`"Ê Tèo"` / `"Tèo ơi"`** trên nền tảng **Edge Impulse** để xuất thư viện C++ TinyML (INT8 ~250KB) chạy ngoại tuyến trên ESP32-S3, kết hợp phím tắt trên laptop và cảm biến chạm TTP223 trên đỉnh đầu.
2. **VRAM thực tế là 6GB (`6144 MiB`):** Đã kiểm tra bằng `nvidia-smi`. Dung lượng 6GB VRAM rất rộng rãi cho phép chạy song song mô phỏng 3D `MuJoCo` và các tác vụ AI cục bộ khi cần, nhưng toàn bộ suy luận LLM chính vẫn đẩy sang API `deepseek-flash` để đạt tốc độ gọi hàm (Tool Calling) tốt nhất.
3. **Tại sao không dùng Raspberry Pi 5 như dự án `LeKiwi` gốc:** Trong `LeKiwi` gốc, Raspberry Pi 5 (~2,3 triệu đồng) dùng để chạy ROS 2, tính động học cánh tay 6 bậc tự do (SO-ARM100) và truyền 2 luồng video liên tục (ngốn 15–25W điện). Với dự án "Tèo", chiếc laptop **HP Victus 15** đã gánh toàn bộ phần AI/Server qua Wi-Fi LAN, còn **ESP32-S3 N16R8** (~115.000đ, tiêu thụ <0,5W) lo phần thu/phát âm thanh và xuất xung I2C qua `PCA9685` điều khiển bánh xe. Nhờ đó tiết kiệm được hơn 2 triệu đồng và dùng được pin 18650 nhỏ gọn.
4. **Lỗi lệnh ngủ & Wake-on-LAN:** Với quyết định dùng Hướng 1 (không ngủ khi cắm sạc, chỉ tắt màn hình), hệ thống bỏ qua sự phụ thuộc vào S0ix Sleep và WoL.

---

## 3. Kiến trúc tổng thể

```
[Robot "Tèo" - ESP32-S3 N16R8] ── WebSocket (Wi-Fi 2.4GHz, LAN) ──► [Laptop HP Victus 15 (16GB RAM, RTX 3050 6GB)]
 ├─ Âm thanh: Mic INMP441, Ampli MAX98357A + Loa 3W                  Hệ thống Server Modular (main, brain, audio_io, tools)
 ├─ Kích hoạt: Model "Ê Tèo" (Edge Impulse) + Chạm TTP223            ├─ Kích hoạt phụ: Phím tắt bàn phím / Auto-VAD (0.7s)
 ├─ Hiển thị & Cảm biến: LCD ST7789, LED WS2812, HLK-LD2410C         ├─ ASR: Google ASR / Groq Whisper | faster-whisper GPU
 ├─ Điều khiển xung I2C: Module PCA9685 (16 kênh PWM)                ├─ LLM & Vision: DeepSeek API (deepseek-flash + Dynamic Suffix Cache)
 │   ├─ Kênh 0..2: 3 Micro Servo MG90S 180° (Cổ + 2 Tay)             ├─ TTS: Piper VITS Offline (chipmunk/diemdam/tramvang) + GoogleTTS
 │   ├─ Kênh 3..5: 3 Servo MG90S 360° ──► Đế 3 bánh Omni (120°)      ├─ Audio Hook: pycaw (tự hạ nhạc trình duyệt xuống 15% khi nghe)
 │   └─ Motion Bundles: wave, happy_dance, slide_left/right, strafe  ├─ Tools: Todo, Đọc PDF/Truyện (Bookmark), Đổi giọng, YouTube, RAG...
 ├─ Chống rơi bàn: 3 cảm biến hồng ngoại IR (đặt ở 3 góc đế Omni)    └─ Quy chuẩn AI Coding: AGENTS.md + .claude/skills (tự sinh tool mới)
 └─ Nguồn: Pin 2S 18650 + BMS ──► 2 Mạch hạ áp MINI560 5V độc lập
 [Module Camera riêng: XIAO ESP32S3 Sense / S3-CAM] ◄── HTTP /capture ── tool nhin()
```

**Nguyên tắc cốt lõi:** ESP32-S3 chỉ lo vào/ra (mic, loa, màn hình, cảm biến, tính công thức Kiwi Drive 3 bánh xe và chạy gói chuyển động `Motion Bundle` qua `PCA9685`). Mọi suy luận LLM, tổng hợp giọng nói Piper Offline, lưu trữ ngữ cảnh hội thoại và công cụ thư ký nằm hoàn toàn ở laptop.

---

## 4. Pipeline và chi phí vận hành

| Khâu | Lựa chọn | Chi phí |
| :--- | :--- | :--- |
| **Wake Word & Voiceprint** | Model TinyML **"Ê Tèo"** (Edge Impulse INT8 chạy trên ESP32-S3) | 0 đồng |
| **ASR (Nhận diện giọng nói)** | **Google ASR / Groq Whisper** làm mặc định + **`faster-whisper turbo (int8)` trên RTX 3050 6GB** làm dự phòng | 0 đồng |
| **LLM & Thị giác (Vision)** | **DeepSeek Flash (`deepseek-flash` / `deepseek-chat`)** tích hợp sẵn Vision (mục 4.1 & 4.2) | Rất thấp (~0,45–0,85 USD/tháng) |
| **TTS (Tổng hợp giọng nói)** | **Piper VITS Offline** (`chipmunk`, `diemdam`, `tramvang` chạy RAM/CPU ~60–120ms) + **Google TTS** (cho ngoại ngữ `en`, `zh`, `ja`) | 0 đồng |
| **Embedding (RAG)** | `bge-m3` chạy trên **CPU** của laptop | 0 đồng |

### 4.1. DeepSeek làm LLM & Kỹ thuật chống vỡ Prompt Cache

* **Endpoint tương thích OpenAI:** `https://api.deepseek.com`.
* **Bảng giá tham khảo:**
  * *Giờ thấp điểm (Off-peak):* Đầu vào **0,15 USD/1M token** (Cache Miss), **0,003 USD/1M token** (Cache Hit — rẻ hơn 50 lần), đầu ra **0,60 USD/1M token**.
  * *Giờ cao điểm (Peak hours):* Nhân đôi (0,30 USD/1M vào khi Cache Miss, 1,20 USD/1M ra).
* **Kỹ thuật tối ưu "Dynamic Suffix Injection" (Chống vỡ Cache 100%):**
  1. Giữ `SYSTEM_PROMPT` và danh sách `TOOLS_SCHEMA` **cố định tuyệt đối từng byte** ở đầu mảng `chat_history`.
  2. Đẩy thông tin biến thiên (giờ hiện tại, đoạn văn bản RAG, trạng thái) vào **cuối tin nhắn `user` mới nhất** (`"[Giờ hệ thống: ...] " + user_text`).
* **Pipeline Streaming 3 tầng (`brain.py`):**
  * `[Tầng 1: llm_producer (AsyncOpenAI stream=True)]` $\rightarrow$ cắt ngay Câu 1 khi gặp dấu chấm câu đẩy sang `[Tầng 2: tts_worker (Piper VITS Offline ~80ms)]` $\rightarrow$ đẩy sang `[Tầng 3: player_worker (Loa Pygame)]`. Giúp tổng thời gian phản hồi từ lúc ngừng nói đến lúc Tèo cất tiếng chỉ còn **~1,0 – 1,2 giây**.

### 4.2. Thị giác (Camera & Màn hình)

* Dùng trực tiếp model **`deepseek-flash`** (gửi qua base64 hoặc URL) cho cả 2 công cụ: chụp ảnh đời thực qua module camera (`nhin_qua_camera_teo`) và chụp màn hình laptop (`nhin_man_hinh_laptop`).
* **Phương án dự phòng miễn phí:** Groq (`Llama 4 Scout/Maverick`), Zhipu (`glm-4v-flash`), Qwen-VL hoặc Gemini Flash qua AI Studio.

---

## 5. Phần cứng

### 5.1. Danh sách mua (Chọn phân loại "Đã hàn chân" để cắm Breadboard/Dupont)

**Bộ tối thiểu — Giai đoạn Bước 2 (khoảng 0,25–0,45 triệu đồng):**
* 1 $\times$ Bo mạch **ESP32-S3 DevKitC N16R8** (chọn loại đã hàn sẵn chân kim).
* 2 $\times$ Mic kỹ thuật số I2S **INMP441** (mua dư 1 cái dự phòng, chọn loại đã hàn chân).
* 1 $\times$ Ampli I2S **MAX98357A** + 1 $\times$ **Loa 3W ($4\Omega$ hoặc $8\Omega$)** có sẵn dây.
* 2 $\times$ Cảm biến chạm điện dung **TTP223** (~3.000đ/cái, dán dưới đỉnh đầu để chạm/vỗ tắt tiếng).
* 1 $\times$ Bảng cắm **Breadboard MB-102 (830 lỗ)** + 1 bộ **Dây cắm Dupont** (Đực-Đực, Đực-Cái, Cái-Cái).

**Phần mở rộng thân trên — Giai đoạn Bước 3 đến Bước 8 (khoảng 0,5–0,85 triệu đồng):**
* 1 $\times$ Màn hình **LCD SPI ST7789** (kích thước 1.54"–2.4", độ phân giải $240\times 240$ hoặc $240\times 320$ hiển thị đôi mắt hoạt hình của Tèo).
* 1 $\times$ Module camera độc lập: **XIAO ESP32S3 Sense** ($2,1 \times 1,8\text{ cm}$) hoặc **ESP32-S3-CAM (OV2640)**.
* 3 $\times$ Micro Servo **MG90S (loại góc 180 độ, bánh răng kim loại)** cho cổ và 2 tay.
* 1 $\times$ Module điều khiển xung I2C **PCA9685 (16 kênh PWM)**: Chỉ tốn 2 chân I2C của ESP32-S3 nhưng điều khiển trực tiếp cả **3 Servo thân trên (`MG90S 180°`)** lẫn **3 Servo bánh xe Omni (`MG90S 360°`)**.
* 1 $\times$ Cảm biến hiện diện mmWave **HLK-LD2410C** (*Lưu ý bắt buộc:* Chọn đúng bản **LD2410C** có chân kim chuẩn **2.54mm** cắm vừa dây Dupont; tránh mua bản LD2410B chân 1.27mm).
* 1 $\times$ Vòng LED **WS2812** (tùy chọn).
* **Hệ thống Pin tách 2 nhánh (Làm ở Bước 8):** 2 cell pin **18650 chính hãng nối tiếp (2S = 7.4V–8.4V)** + mạch bảo vệ sạc xả **BMS 2S** + **2 mạch hạ áp Buck MINI560 5V** (1 mạch cấp riêng đường 5V "Sạch" cho ESP32/Loa/Mic/LCD; 1 mạch cấp riêng đường 5V "Cơ bắp" cho chân `V+` của PCA9685 nuôi 6 Servo).

**Đế 3 bánh xe đa hướng (3-Wheel Omni / Kiwi Drive học từ `LeKiwi`) — Giai đoạn Bước 9 (khoảng 0,25–0,4 triệu đồng):**
* 3 $\times$ **Bánh xe đa hướng Omni Mini** (đường kính 48mm hoặc 58mm, có các con lăn phụ vuông góc trên vành bánh).
* 3 $\times$ **Micro Servo MG90S loại quay liên tục 360 độ (`MG90S 360° Continuous Rotation`)** (~28.000đ/cái): Gắn trực tiếp vào 3 bánh xe Omni đặt lệch nhau góc đều **$120^\circ$**. Vì bản thân Servo 360° đã tích hợp sẵn mạch điều khiển tốc độ và chiều quay bên trong, bạn chỉ cần **cắm thẳng giắc 3 dây của chúng vào kênh 3, 4, 5 trên mạch `PCA9685`** mà **không cần mua mạch cầu H `DRV8833`/`TB6612`**. *(Tùy chọn: Nếu muốn dùng 3 mô tơ giảm tốc kim loại `N20` thì mua kèm 2 mạch `DRV8833` cắm vào 6 kênh PWM trống của `PCA9685`).*
* 3 $\times$ Cảm biến hồng ngoại tránh rơi mép bàn (**IR Obstacle Sensor** hướng xuống gầm, đặt xen kẽ ở 3 góc của đế tam giác/tròn để trượt ngang hướng nào cũng phanh kịp).
* 1 $\times$ Tấm đế tròn hoặc lục giác (đường kính **10–12 cm**, cắt tấm nhựa Mica/bìa cứng hoặc in 3D) để bắt 3 cụm bánh xe lệch góc $120^\circ$.

Tổng dự kiến khoảng **1,0–1,7 triệu đồng** cho toàn bộ lộ trình (rẻ hơn và dễ đấu dây hơn so với phương án bánh xích cũ).

### 5.2. Lưu ý kỹ thuật & Chống nhiễu

* **Quản lý chân GPIO trên ESP32-S3 N16R8:** Màn hình SPI ~6 chân, mic I2S 3, ampli I2S 3, chạm TTP223 1, I2C PCA9685 2 (gánh toàn bộ 3 servo thân trên + 3 servo bánh xe Omni), LD2410C 1, chống rơi IR 3, đo pin ADC 1 $\rightarrow$ tổng cộng **20 chân**, nằm gọn trong giới hạn an toàn của board. Tuyệt đối **không dùng GPIO 35–37** (dành cho Octal PSRAM) và các chân strapping (GPIO 0, 3, 45, 46).
* **Cách ly nhiễu nguồn bằng 2 mạch hạ áp MINI560 5V:** Tách 2 nhánh hạ áp 5V độc lập từ nguồn Pin 2S (7.4V–8.4V), nối chung mass (GND), giúp đường 5V nuôi ESP32 và Ampli loa phẳng tuyệt đối ngay cả khi cả 6 con servo (3 thân trên + 3 bánh xe Omni) khởi động cùng lúc.

### 5.3. Hình dáng, Động học Kiwi Drive (LeKiwi) và Chuyển động Motion Bundle (Mục 5.4)

**Mục tiêu thiết kế:** Thân trên giữ nét đáng yêu của **WALL-E** (cao ~13,5 cm, đầu màn hình LCD hai mắt gắn trên cổ, 2 cánh tay), đặt trên **Đế tròn 3 bánh xe đa hướng (Kiwi Drive, đường kính 10–12 cm)** lấy cảm hứng từ dự án **`SIGRobotics-UIUC/LeKiwi`** và **`Ekumen-OS/lekiwi`**.

**Tại sao Đế 3 bánh Omni (Kiwi Drive) vượt trội hơn Đế bánh xích trên bàn làm việc?**
* **What (Nó là cái gì):** Hệ truyền động toàn hướng (*Holonomic Drive*) gồm 3 bánh xe Omni đặt lệch nhau góc $120^\circ$.
* **How (Công thức toán học điều khiển 3 bánh xe lấy từ `LeKiwi`):**
  Để Tèo trượt ngang trái/phải với vận tốc $v_x$, tiến/lùi với vận tốc $v_y$ và tự xoay quanh trục giữa với tốc độ góc $\omega$, vi điều khiển chỉ cần tính tốc độ quay cho 3 bánh xe ($w_1$ phía trước, $w_2$ sau trái, $w_3$ sau phải, với $R$ là bán kính đế):
  $$w_1 = v_x + R \cdot \omega$$
  $$w_2 = -0.5 \cdot v_x + \frac{\sqrt{3}}{2} \cdot v_y + R \cdot \omega$$
  $$w_3 = -0.5 \cdot v_x - \frac{\sqrt{3}}{2} \cdot v_y + R \cdot \omega$$
* **Why (Ưu điểm tuyệt đối so với bánh xích):**
  1. **Trượt ngang giữ nguyên ánh mắt (Strafing with Eye-Contact):** Bánh xích muốn đi sang ngang bắt buộc phải quay mặt đi $90^\circ$ (làm mất góc nhìn màn hình LCD và camera). Với đế 3 bánh Omni, Tèo có thể **trượt ngang sang trái, trượt ngang sang phải, đi chéo hoặc lượn vòng cung quanh mặt bàn trong khi đôi mắt LCD và ống kính Camera vẫn luôn khóa cứng nhìn thẳng vào mặt bạn!**
  2. **Vũ đạo "Moonwalk" & Nhảy theo nhạc 360 độ:** Kết hợp trượt ngang mềm mại + xoay tâm + vẫy 2 tay và gật cổ theo nhịp BPM mà không lo tuột xích hay kẹt ma sát mặt bàn.
  3. **Đấu dây siêu gọn:** Dùng 3 con `Servo MG90S 360°` cắm thẳng vào `PCA9685`, loại bỏ hoàn toàn mạch cầu H `DRV8833`.
* **Trade-off (Đánh đổi):** Đường kính đế tròn khoảng 10–12 cm (rộng hơn đế bánh xích khoảng 1,5–2 cm) và cần 3 mắt hồng ngoại IR chống rơi bàn (thay vì 2 mắt như bánh xích) vì robot có thể trượt theo mọi hướng.

**Cơ chế đóng gói "Motion Bundle" (Kết hợp `KingKongRobotics/jumper` + `LeKiwi`):**
* Định nghĩa sẵn các gói quỹ đạo mượt trên ESP32-S3 (xuất xung I2C 50Hz qua `PCA9685`):
  * `wave_greeting`: Nghiêng cổ + vẫy tay phải chào.
  * `nod_yes` / `shake_no`: Gật đầu / lắc cổ.
  * `slide_left` / `slide_right`: Trượt ngang sang trái / phải giữ nguyên hướng mặt nhìn chủ nhân.
  * `circle_strafe`: Lượn vòng cung quanh bàn làm việc trong khi mặt vẫn hướng về phía người ngồi.
  * `happy_dance` / `moonwalk_dance`: Nhảy trượt ngang đa hướng kết hợp vẫy 2 tay theo nhịp nhạc BPM.
* **Quy tắc chống ồn cơ khí lọt mic:** Chỉ chạy `Motion Bundle` khi không đang thu âm; ngay khi chuyển sang trạng thái `Listening` (nghe lệnh) thì khóa đứng yên toàn bộ 6 servo.

---

## 6. Phần mềm trên laptop HP Victus 15 (Kiến trúc Modular)

### 6.1. Cấu trúc thư mục mã nguồn (Đã triển khai và chạy ổn định)

```text
teo_sim_AI/
├── .env                  # Lưu DEEPSEEK_API_KEY và cấu hình TEO_TTS_MODE
├── config.py             # Hằng số, PIPER_PROFILES (chipmunk, diemdam, tramvang), SYSTEM_PROMPT tĩnh
├── audio_io.py           # Auto-VAD (0.7s), Google ASR, Piper VITS Offline + GoogleTTS, pycaw Auto-Ducking
├── doc_reader.py         # Trích xuất PDF/Word/TXT bằng MarkItDown, cắt câu đọc nguyên văn & lưu Bookmark
├── tools.py              # Định nghĩa TOOLS_SCHEMA & thực thi công cụ (Đổi giọng, Đọc sách, YouTube, Todo, 3D Sim)
├── brain.py              # Lõi DeepSeek Streaming 3 tầng (Producer -> TTS Worker -> Player) & xử lý Tool Call
├── main.py               # Điểm khởi chạy chính (Entry point)
├── teo_walle.xml         # Mô hình 3D MuJoCo
└── teo_sim_runner.py     # Trình chạy cửa sổ 3D MuJoCo nhận lệnh UDP (127.0.0.1:5555)
```

### 6.2. Hệ thống Công cụ (Tools) & Tự động hóa mở rộng bằng `AGENTS.md`

* Chi tiết **28 công cụ chia làm 7 nhóm chức năng** được lưu trong tài liệu riêng: **`danh-sach-tool-robot-teo.md`**.
* Sử dụng tệp quy chuẩn **`AGENTS.md` và `.claude/skills`** ngay trong thư mục dự án để các AI Coding Assistant (Claude Code, Cline, Cursor) tự động viết thêm hàm công cụ mới theo đúng chuẩn văn nói tiếng Việt và bảo mật `allowlist`.

### 6.3. Quy trình huấn luyện "Ê Tèo" kiêm Voiceprint trên Edge Impulse

* Thu thập mẫu 16.000 Hz (50 mẫu `e_teo`, 50 mẫu `unknown` vần *"èo"*, 3–5 phút `noise`) $\rightarrow$ Huấn luyện khối `Audio (MFCC/MFE) + Keras Classification (INT8)` $\rightarrow$ Xuất thư viện C++ (~200KB) nhúng vào ESP32-S3.
* Duy trì chế độ **Hội thoại liên tục**: Gọi *"Ê Tèo"* 1 lần để mở phiên, tự động mở lại mic sau mỗi câu trả lời cho đến khi hết việc.

### 6.4. Đọc tài liệu, Đọc truyện, Phát nhạc & Dịch thuật (Mục 6.6 – 6.9)

* **Tóm tắt & Đọc nguyên văn (`doc_reader.py`):** Dùng `markitdown` đọc file `.pdf`, `.docx`, `.txt`, `.md` trong thư mục `tai_lieu/`, lưu vị trí câu vào `teo_bookmark.json` (hỗ trợ *đọc mới, đọc tiếp, đọc lại*) và đọc bằng giọng **Piper VITS Offline** tốn 0 đồng, không bao giờ bị giới hạn băng thông.
* **Phát nhạc YouTube & Auto-Ducking (`pycaw`):** Tự động hạ âm lượng trình duyệt (`chrome.exe`, `msedge.exe`, `spotify.exe`, `mpv.exe`) xuống **15%** ngay khi bắt đầu thu âm và khôi phục **100%** khi Tèo trả lời xong.
* **Dịch thuật đa ngôn ngữ:** Tự động nhận diện ngôn ngữ bằng `detect_lang_fast()`: Tiếng Việt đọc bằng **Piper VITS Offline**, tiếng Anh/Trung/Nhật tự động chuyển sang **Google TTS** đúng giọng bản xứ.

---

## 7. Khởi động và quản lý nguồn laptop HP Victus 15

**Đã chọn Hướng 1: Không cho ngủ khi cắm sạc, chỉ tắt màn hình.**
* Trong Windows 11: Khi cắm sạc đặt `Sleep = Never`, tắt màn hình sau 3–5 phút, đóng nắp máy = `"Do nothing"`.
* Chế độ quạt `Balanced` / `Quiet` trong Omen Gaming Hub; bật giới hạn sạc pin (~80%).
* Nhờ Piper VITS chạy nhẹ trên CPU/RAM và LLM gọi qua API, card rời **RTX 3050 6GB** hoàn toàn được nghỉ (0W Idle) khi tắt màn hình, giúp toàn bộ laptop chỉ tiêu thụ khoảng **8W – 12W**.

---

## 8. Lộ trình thực hiện từng bước

| Bước | Việc cần làm | Trạng thái / Chi phí |
| :--- | :--- | :--- |
| **0** | Thiết lập môi trường trên HP Victus 15 (RTX 3050 6GB), xây dựng kiến trúc Modular (`config`, `audio_io`, `brain`, `tools`, `main`), tích hợp DeepSeek Streaming 3 tầng + **Piper VITS Offline** (3 giọng) + Google ASR + Auto-VAD 0.7s. | **ĐÃ HOÀN THÀNH (0 đồng)** |
| **1** | Hoàn thiện bộ công cụ Thư ký trên Laptop (Đọc/Tóm tắt PDF `doc_reader.py`, Clipboard, Chụp màn hình Vision, Pomodoro, RAG `bge-m3`), cập nhật mô hình 3D `MuJoCo` sang đế 3 bánh Omni và thiết lập `AGENTS.md`. | **Đang thực hiện (0 đồng)** |
| **2** | Mua bộ tối thiểu (ESP32-S3 N16R8, INMP441, MAX98357A + loa 3W, cảm biến chạm TTP223, breadboard, dây Dupont). Ghép mạch, nạp firmware `.bin` test qua Wi-Fi LAN; thu âm trên **Edge Impulse** và nạp bản nhận từ khóa **`"Ê Tèo"`**. | **~0,25–0,45 triệu** |
| **3** | Thêm màn hình LCD ST7789 hiển thị hai mắt hoạt hình. Cấu hình hoàn chỉnh nguồn laptop không ngủ khi cắm sạc và Task Scheduler tự chạy server. | **~0,1–0,15 triệu** |
| **4** | Lắp module I2C `PCA9685` + 3 micro servo `MG90S 180°` (đầu + 2 tay) + vòng LED `WS2812`; nạp các gói cử chỉ mượt **Motion Bundle** (`wave_greeting`, `nod_yes`, `happy_dance`). | **~0,15–0,2 triệu** |
| **5** | Gắn cảm biến hiện diện `HLK-LD2410C` (chân 2.54mm) + tính năng tự mở mắt chào và đọc Bản tin buổi sáng khi chủ nhân ngồi vào bàn. | **~0,08–0,12 triệu** |
| **6** | Lắp module camera riêng (`XIAO ESP32S3 Sense` / `ESP32-S3-CAM`) + kết nối vào tool `nhin_qua_camera_teo()`. | **~0,2–0,35 triệu** |
| **7** | Mở khóa các tool có thể ghi/hành động trên laptop (Mở Workspace ứng dụng, Dọn file Downloads, Khóa/Tắt máy có xác nhận giọng nói). | **0 đồng** |
| **8** | Lắp hệ thống Pin 2S 18650 + BMS 2S + **2 mạch hạ áp MINI560 5V tách độc lập** nhánh Logic/Audio và nhánh 6 Servo trên `PCA9685`. | **~0,18–0,3 triệu** |
| **9** | **Lắp Đế 3 bánh xe đa hướng (3-Wheel Omni / Kiwi Drive kiểu `LeKiwi`, đường kính 10–12 cm):** Gắn 3 bánh Omni (48mm/58mm) vào **3 Servo `MG90S 360°`** cắm thẳng vào kênh 3, 4, 5 trên `PCA9685` + 3 cảm biến IR chống rơi mép bàn. | **~0,25–0,4 triệu** |
| **10** | Tùy chọn: Hoàn thiện vỏ hộp đẹp hơn, kết nối Telegram Bot, trợ lý ghi âm tóm tắt họp, Home Assistant. | **Tùy chọn** |

---

## 9. Bảo mật & Quyền riêng tư

* Luôn dùng `allowlist` thư mục (`ALLOWED_DIRS`), tách biệt tool đọc/ghi, bắt buộc xác nhận bằng giọng nói trước khi xóa file hoặc tắt máy.
* Không mở cổng (port forwarding) ra Internet; dùng Tailscale nếu cần kết nối từ xa.
* Làm nắp che cơ học cho camera và bật đèn LED báo hiệu khi chụp ảnh.
* Giữ khóa API trong file `.env` cục bộ (đã đưa vào `.gitignore`).

---

## 10. Danh sách việc cần kiểm chứng (Checklist)

* [x] **Kiểm tra VRAM thực tế của RTX 3050 trên HP Victus 15:** Đã xác nhận bản **6GB VRAM (`6144 MiB`)**.
* [x] **Tối ưu độ trễ giọng đọc tiếng Việt (TTS) & Chống lỗi mất câu:** Đã giải quyết triệt để bằng **Piper VITS Offline** (3 giọng: Sóc chuột, Điềm đạm, Trầm vang — độ trễ ~60–120ms) kết hợp `GoogleTTS` cho ngoại ngữ trong `audio_io.py`.
* [x] **Pipeline Streaming 3 tầng & Chống vỡ Prompt Cache DeepSeek:** Đã triển khai trong `brain.py` và `config.py` (tổng phản hồi Câu 1 đạt ~1,0–1,2 giây).
* [x] **Hook tự động hạ nhỏ nhạc trình duyệt khi nói:** Đã tích hợp `pycaw` trong `audio_io.py`.
* [x] **Chắt lọc kỹ thuật từ `KingKongRobotics/jumper`:** Đã tích hợp kiến trúc **Motion Bundle** và quy chuẩn **`AGENTS.md`**.
* [x] **Nghiên cứu `SIGRobotics-UIUC/LeKiwi` & `Ekumen-OS/lekiwi`:** Đã chốt chuyển từ Đế bánh xích sang **Đế 3 bánh Omni (Kiwi Drive)** dùng 3 Servo `MG90S 360°` cắm thẳng vào `PCA9685` (bỏ mạch cầu H `DRV8833` và không cần mua Raspberry Pi 5).
* [ ] **Hoàn thiện các Tool Đợt 2 trên Laptop:** Thêm công cụ đọc Clipboard (`Ctrl+C`), chụp màn hình laptop và đồng hồ Pomodoro.
* [ ] **Kiểm tra thực tế ở Bước 2 & Bước 9:** Thu âm model `"Ê Tèo"` trên Edge Impulse và test độ bám của 3 bánh xe Omni mini trên mặt bàn làm việc.

---

## Nguồn tham khảo

* Tài liệu gốc: "Kiến trúc Hệ thống Robot Agent Lai (Hybrid Edge-Cloud) trên Nền tảng ESP32-S3 và Laptop HP Victus 15"
* DeepSeek API Docs: https://api-docs.deepseek.com/quick_start/pricing
* SIGRobotics UIUC LeKiwi (3-Wheel Omni Kiwi Drive Hardware): https://github.com/SIGRobotics-UIUC/LeKiwi
* Ekumen-OS LeKiwi (Holonomic Omni Wheel Kinematics & Gazebo Sim): https://github.com/Ekumen-OS/lekiwi
* KingKongRobotics Jumper AI Toolkit (`AGENTS.md` & Motion Bundle architecture): https://github.com/KingKongRobotics/jumper
* Edge Impulse Audio Classification & Keyword Spotting: https://docs.edgeimpulse.com/docs/tutorials/end-to-end-tutorials/audio-classification