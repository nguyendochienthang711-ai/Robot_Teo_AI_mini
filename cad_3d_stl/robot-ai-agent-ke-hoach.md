# Kế hoạch dự án Robot AI trợ lý "Tèo" (ESP32-S3 + xiaozhi-esp32 + HP Victus 15)

Cập nhật: 07/11/2026 (đồng bộ hoàn chỉnh phần cứng/vỏ với **CAD v10**: kích thước $116 \times 120 \times 142\text{ mm}$, gầm $7.0\text{ mm}$, tâm bánh `Nexus 14108` $R = 58.0\text{ mm}$, ngàm khóa 5 servo bắt vít không keo, camera `ESP32-CAM OV3660`, khay điện tử `Pin-Up`, 11 file in `.stl`/`.step` đạt `0.00 mm³` va chạm & đã kiểm chứng động lực học MuJoCo — xem 5.2). Các mục phần mềm giữ nguyên bản 04/11/2026 (mô phỏng MuJoCo, 12 Tools, ANTIGRAVITY.md).

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
| **Giữ lại** | Màn hình LCD, camera, 2 servo cánh tay (bỏ khớp cổ, tạo hình nguyên cục Unibody và dùng đế Omni tự xoay cả thân để đổi góc nhìn), cảm biến hiện diện (`HLK-LD2410C`), pin 2S 18650 (2 nhánh hạ áp độc lập), voiceprint (tích hợp trong model Wake Word của Edge Impulse), RAG. |
| **Tính năng thêm** | Phát nhạc/YouTube kèm hook `pycaw` tự vặn nhỏ nhạc khi nói (6.7), tóm tắt và đọc to văn bản (6.6), đọc truyện (6.8), dịch thuật tự đổi giọng TTS (6.9), đung đưa/nhảy trượt ngang theo nhịp nhạc bằng cơ chế **Motion Bundle** (5.4), tự động hóa viết code kỹ năng mới bằng **`ANTIGRAVITY.md` & GitHub Spec-Kit SDD** (6.2). |
| **Hình dáng & Đế di chuyển** | Thiết kế **nguyên cục liền khối (Unibody Chunky Pod)** bo tròn đáng yêu ($116 \times 120 \times 142\text{ mm}$, đã bỏ khớp cổ), đỉnh đầu bo cong vòm mềm mại (dome 3D). Thân gắn liền với cụm 3 bánh xe đa hướng đôi **`Nexus 14108` $\varnothing 48 \times 25.5\text{ mm}$ bố trí kiểu LeKiwi** (2 bánh trước góc $\pm 60^\circ$, 1 bánh sau $180^\circ$ tại bán kính **$R = 58.0\text{ mm}$** kèm 2 đệm chống lật đuôi kép tại `(-42, ±36 mm)`). Dùng duy nhất 1 module **PCA9685 (16 kênh PWM)** điều khiển cả **2 Servo cánh tay (`MG90S 180°`)** lẫn **3 Servo bánh xe (`MG90S 360°`)** (tổng 5 servo khóa cứng bằng nẹp vít `teo_nep_giu_servo`, không dùng keo). Bên trong có **vách ngăn ngang tại $Z = 58.0\text{ mm}$** đỡ **Pack Pin 2S nguyên khối**, 2 mạch `MINI560` và 2 kẹp `CH-2`; tầng trên cùng là khay `Pin-Up` (`Z = 99 mm`) chứa `ESP32-S3` + `PCA9685` + kẹp ngắt nguồn nhanh `SM-2P` (bỏ công tắc vật lý `KCD11` và bỏ LED cằm `WS2812`). Tổng khối lượng $733.1\text{ g}$, $CoM_Z = 61.54\text{ mm}$, góc lật tĩnh $23.8^\circ / 25.9^\circ$ (đã pass 100% MuJoCo). |
| **Vỏ robot & Kính mặt** | **In 3D toàn bộ thân vỏ và kính che mặt (11 file `.stl` + `.step` sinh từ `build_teo_cad.py`):** Gồm thân dưới + vách ngăn + thân trên ghép bằng 4 ốc lục giác chìm `M2.5 × 55 mm` từ đáy, **mũ đầu tháo bằng 4 cặp nam châm $\varnothing 6 \times 2\text{ mm}$**, khay điện tử thả đứng, nắp hộp loa kín khí, 2 cánh tay + 2 nắp chụp, 3 hub nối bánh `Nexus 14108`, và 5 thanh nẹp giữ servo; **Mặt kính che hốc màn hình in 3D SLA Clear Resin** ($70 \times 60 \times 1.8\text{ mm}$) phủ bóng khói Tamiya TS-71 giấu viền LCD `ST7789 2.0"`, chừa lỗ vát $45^\circ$ $\varnothing 6.5\text{ mm}$ cho `ESP32-CAM OV3660`. |
| **Ưu tiên** | Cân bằng tối ưu giữa chi phí thấp và thẩm mỹ hoàn thiện cao cấp chuẩn robot AI để bàn. |

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
[Robot "Tèo" - ESP32-S3 N16R8] ── WebSocket / UDP (Wi-Fi LAN, HMAC Auth) ──► [Laptop HP Victus 15 (16GB RAM, RTX 3050 6GB)]
 ├─ Âm thanh: Mic INMP441, Ampli MAX98357A + Loa 3W                           Hệ thống Server Modular (main, brain, audio_io, tools/)
 ├─ Kích hoạt: Model "Ê Tèo" (Edge Impulse) + Chạm TTP223                     ├─ Kích hoạt phụ: Phím tắt bàn phím / Auto-VAD (0.7s)
 ├─ Hiển thị & Cảm biến: LCD ST7789, LED WS2812, HLK-LD2410C                  ├─ ASR: Google ASR / Groq Whisper | faster-whisper GPU
 ├─ Điều khiển xung I2C: Module PCA9685 (16 kênh PWM)                         ├─ LLM & Vision: DeepSeek API (deepseek-flash + Suffix Cache)
 │   ├─ Kênh 0..1: 2 Micro Servo MG90S 180° (2 Cánh tay - Bỏ servo cổ)         ├─ TTS: Piper VITS Offline (3 giọng) + GoogleTTS
 │   ├─ Kênh 3..5: 3 Servo MG90S 360° ──► 3 bánh Omni 48mm gắn liền gầm thân     ├─ Audio Hook: pycaw (tự hạ nhạc trình duyệt khi nghe)
 │   └─ Motion Bundles: wave, happy_dance, slide_left/right, circle_strafe    ├─ 12 Tools Cốt lõi: Kiwi Sim, Doc, Pomodoro, Memory, Web...
 ├─ Chống lật & rơi: 3 mắt hồng ngoại IR + Đệm chống lật đuôi (omni_pad_tail) └─ Quy chuẩn AI Coding: ANTIGRAVITY.md (GitHub Spec-Kit SDD)
 └─ Nguồn: Pin 2S 18650 + BMS (đặt sát đáy CoM <= 3cm) ──► 2 Buck MINI560 5V
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
* 2 $\times$ Micro Servo **MG90S (loại góc 180 độ, bánh răng kim loại)** cho 2 cánh tay (đã bỏ servo cổ để làm thân nguyên cục unibody, robot xoay hướng nhìn bằng cách xoay cả thân qua 3 bánh xe Omni).
* 1 $\times$ Module điều khiển xung I2C **PCA9685 (16 kênh PWM)**: Chỉ tốn 2 chân I2C của ESP32-S3 nhưng điều khiển trực tiếp cả **2 Servo cánh tay (`MG90S 180°`)** lẫn **3 Servo bánh xe Omni (`MG90S 360°`)** (tổng 5 servo, giảm 1 servo cổ).
* 1 $\times$ Cảm biến hiện diện mmWave **HLK-LD2410C** (*Lưu ý bắt buộc:* Chọn đúng bản **LD2410C** có chân kim chuẩn **2.54mm** cắm vừa dây Dupont; tránh mua bản LD2410B chân 1.27mm).
* 1 $\times$ Vòng LED **WS2812** (tùy chọn).
* **Hệ thống Pin tách 2 nhánh (Làm ở Bước 8):** 2 cell pin **18650 chính hãng nối tiếp (2S = 7.4V–8.4V)** + mạch bảo vệ sạc xả **BMS 2S** + **2 mạch hạ áp Buck MINI560 5V** (1 mạch cấp riêng đường 5V "Sạch" cho ESP32/Loa/Mic/LCD; 1 mạch cấp riêng đường 5V "Cơ bắp" cho chân `V+` của PCA9685 nuôi 6 Servo).

**Đế 3 bánh xe đa hướng (3-Wheel Omni / Kiwi Drive học từ `LeKiwi`) — Giai đoạn Bước 9 (khoảng 0,25–0,4 triệu đồng):**
* 3 $\times$ **Bánh xe đa hướng Omni Mini** (đường kính 48mm hoặc 58mm, có các con lăn phụ vuông góc trên vành bánh).
* 3 $\times$ **Micro Servo MG90S loại quay liên tục 360 độ (`MG90S 360° Continuous Rotation`)** (~28.000đ/cái): Gắn trực tiếp vào 3 bánh xe Omni đặt lệch nhau góc đều **$120^\circ$**. Vì bản thân Servo 360° đã tích hợp sẵn mạch điều khiển tốc độ và chiều quay bên trong, bạn chỉ cần **cắm thẳng giắc 3 dây của chúng vào kênh 3, 4, 5 trên mạch `PCA9685`** mà **không cần mua mạch cầu H `DRV8833`/`TB6612`**. *(Tùy chọn: Nếu muốn dùng 3 mô tơ giảm tốc kim loại `N20` thì mua kèm 2 mạch `DRV8833` cắm vào 6 kênh PWM trống của `PCA9685`).*
* 1 $\times$ **Đệm chống lật / Con lăn phụ đuôi xe (Anti-tip Tail Pad / Mini Felt Pad / Ball Caster)** (~5.000–10.000đ): Gắn dưới gầm phía sau tấm đế tại tọa độ $x = -4.5\text{ cm}$, bán kính tiếp xúc ~6mm. *(⚠ CAD v9 chưa dựng được đệm này: sàn dưới bánh sau bị hốc bánh cắt qua; cần thiết kế lại.)* Có tác dụng mở rộng đa giác tiếp xúc mặt bàn thành tứ giác hình thoi, chống lật ngửa tuyệt đối khi giơ 2 tay hoặc phanh giật lùi.
* 3 $\times$ Cảm biến hồng ngoại tránh rơi mép bàn (**IR Obstacle Sensor** hướng xuống gầm, đặt xen kẽ ở 3 góc của đế tam giác/tròn để trượt ngang hướng nào cũng phanh kịp).
* 1 $\times$ Tấm đế tròn hoặc lục giác (đường kính **10–12 cm**, cắt tấm nhựa Mica/bìa cứng hoặc in 3D) để bắt 3 cụm bánh xe lệch góc $120^\circ$ và điểm tỳ chống lật đuôi.

Tổng dự kiến khoảng **1,0–1,7 triệu đồng** cho toàn bộ lộ trình (rẻ hơn và dễ đấu dây hơn so với phương án bánh xích cũ).

### 5.2. Lưu ý kỹ thuật, Chống nhiễu & Cân bằng động lực học

* **Quản lý chân GPIO trên ESP32-S3 N16R8:** Màn hình SPI ~6 chân, mic I2S 3, ampli I2S 3, chạm TTP223 1, I2C PCA9685 2 (gánh toàn bộ 2 servo cánh tay + 3 servo bánh xe Omni), LD2410C 1, chống rơi IR 3, đo pin ADC 1 $\rightarrow$ tổng cộng **20 chân**, nằm gọn trong giới hạn an toàn của board. Tuyệt đối **không dùng GPIO 35–37** (dành cho Octal PSRAM) và các chân strapping (GPIO 0, 3, 45, 46).
* **Cách ly nhiễu nguồn bằng 2 mạch hạ áp MINI560 5V:** Tách 2 nhánh hạ áp 5V độc lập từ nguồn Pin 2S (7.4V–8.4V), nối chung mass (GND), giúp đường 5V nuôi ESP32 và Ampli loa phẳng tuyệt đối ngay cả khi cả 5 con servo (2 cánh tay + 3 bánh xe Omni) khởi động cùng lúc.
* **✅ Cập nhật 07/11/2026 — Đã hoàn thiện & kiểm chứng CAD v10 + MuJoCo:** Phiên bản **CAD v10** ($116 \times 120 \times 142\text{ mm}$, khoảng sáng gầm $7.0\text{ mm}$, bán kính bánh `Nexus 14108` $R = 58.0\text{ mm}$) đã giải quyết triệt để mọi giao cắt nội thất (`0.00 mm³` trên toàn bộ 19 chi tiết in và 27 khối linh kiện/đầu cắm Dupont). Nhờ cụm 3 bánh đôi `Nexus 14108` nặng $117\text{ g}$ ở $Z = 24\text{ mm}$ và mở rộng $R_{\text{wheel}}$ lên $58.0\text{ mm}$ kèm 2 đệm chống lật đuôi kép tại `(-42, ±36 mm)`, tổng khối lượng robot đạt **$733.1\text{ g}$**, **$CoM_Z = 61.54\text{ mm}$**, góc lật tĩnh đạt **$23.8^\circ$ (trước) / $25.9^\circ$ (hông)**. Mô phỏng động lực học `teo_walle.xml` trên MuJoCo đã vượt qua toàn bộ 15 bài test chuyển động & phanh khẩn cấp (`max_tilt ≤ 0.71°`) và 24/24 unit & integration tests. Hai khối "Quy tắc" và "Giải pháp thực nghiệm" ngay dưới là **bản v1.0 (04/11/2026), giữ lại để đối chiếu**.
* **Quy tắc phân bổ trọng tâm CoM (Center of Mass) thấp $\le 3\text{ cm}$ (bản v1.0, 04/11/2026):**
  * Chiều cao robot khoảng 13,5 cm. Nếu để pin 18650 hoặc linh kiện nặng trên ngực/đầu, trọng tâm sẽ bị đẩy lên cao ($7–8\text{ cm}$), làm góc nghiêng tới hạn lật ngửa giảm xuống dưới $19^\circ$, chỉ cần cử động tay nhanh là đổ.
  * *Giải pháp thực nghiệm (đã kiểm chứng qua MuJoCo):* Toàn bộ phần nặng nhất gồm 2 cell pin 18650 (~95g), 3 Servo kim loại MG90S 360° bánh xe (~40g), module PCA9685 và 2 mạch hạ áp MINI560 **phải được đặt ép sát tấm sàn đế ($z \le 2\text{ cm}$)**.
  * Thân trên unibody (hộp thân, 2 tay, màn hình ST7789, camera) in 3D với mật độ Infill 15–20%, khống chế khối lượng thân trên $\le 100\text{g}$.
  * Nhờ đó, trọng tâm tổng thể ($CoM$) luôn nằm ở độ cao $\le 3\text{ cm}$ so với mặt bàn $\rightarrow$ Góc nghiêng tới hạn lật ngửa đạt **$> 37^\circ$**, giúp Tèo đứng vững chãi tuyệt đối.
* **Bộ lọc làm mượt xung điều khiển Servo (Exponential Smoothing / Slew Rate Limiter):**
  * Khi AI ra lệnh cử chỉ (ví dụ vẫy tay từ $0^\circ \to -51^\circ$), nếu xuất lệnh tức thời dạng bậc thang (step command), gia tốc góc cực lớn ($180\text{ rad/s}^2$) sẽ sinh mô-men phản lực pitch hất ngược thân robot về phía sau gây giật nảy.
  * *Giải pháp:* Cả trong mô phỏng (`teo_sim_runner.py`) lẫn firmware ESP32, tín hiệu góc servo bắt buộc phải đi qua bộ lọc làm mượt hàm mũ:
    $$\theta_{\text{target}}(t) = (1 - \alpha) \cdot \theta_{\text{curr}} + \alpha \cdot \theta_{\text{cmd}} \quad (\text{với } \alpha = 0.15)$$
    hoặc giới hạn tốc độ biến thiên (Slew Rate Limit $\le 60^\circ / 0.1\text{s}$) tương thích đúng giới hạn vật lý của Servo kim loại MG90S. Giúp mọi cử chỉ diễn ra êm mượt, bảo vệ bánh răng và triệt tiêu hoàn toàn rung giật bàn.

### 5.3. Hình dáng, Động học Kiwi Drive (LeKiwi) và Cơ chế Chống lật Đuôi

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
* **Cơ chế chống lật đuôi (Anti-tip Geometry):**
  Đế Kiwi Drive chuẩn có 1 bánh trước tại $x = +4.5\text{ cm}$ và 2 bánh sau tại $x = -2.25\text{ cm}, y = \pm 3.9\text{ cm}$. Mép sau tấm đế tròn kéo dài đến $x = -5.5\text{ cm}$, nhưng 2 điểm tiếp xúc đất chỉ nằm ở $x = -2.25\text{ cm}$. Khi bổ sung đệm chống lật `omni_pad_tail` tại $x = -4.5\text{ cm}$, khoảng đỡ phía sau tăng gấp đôi, biến tam giác tiếp xúc thành tứ giác hình thoi vững chắc, loại trừ 100% rủi ro lật đuôi khi cử động mạnh.

### 5.4. Mô phỏng Vật lý 3D MuJoCo & Gói chuyển động Motion Bundle

* **Môi trường mô phỏng MuJoCo (`teo_walle.xml` & `teo_sim_runner.py`):**
  * Mô phỏng chính xác kích thước thực tế, trọng lượng từng cụm linh kiện, ma sát bánh xe đa hướng và phản lực tiếp xúc mặt bàn trước khi chế tạo thật.
  * *Xử lý lỗi nổ gia tốc số học (`QACC NaN at DOF 6`):* Cấu hình bộ tích phân ngầm gia tốc nhanh `integrator="implicitfast"`, kết hợp giảm chấn khớp `damping="0.005"`, `kv="0.05"` và bộ giảm chấn chống nghiêng lắc thân, đảm bảo mô phỏng chạy mượt mà ở 60 FPS không bao giờ bị văng.
  * Hỗ trợ điều khiển tương tác trực quan qua UDP socket (127.0.0.1:5555): phím W/A/S/D để trượt đa hướng, phím số 1..6 để kích hoạt các cử chỉ Motion Bundle.
* **Cơ chế đóng gói "Motion Bundle" (Kết hợp `KingKongRobotics/jumper` + `LeKiwi`):**
  * Định nghĩa sẵn các gói quỹ đạo mượt trên ESP32-S3 và bản giả lập mô phỏng:
    * `wave_greeting`: Nghiêng cổ + vẫy tay phải chào.
    * `nod_yes` / `shake_no`: Gật đầu / lắc cổ.
    * `slide_left` / `slide_right`: Trượt ngang sang trái / phải giữ nguyên hướng mặt nhìn chủ nhân.
    * `circle_strafe`: Lượn vòng cung quanh bàn làm việc trong khi mặt vẫn hướng về phía người ngồi.
    * `happy_dance` / `moonwalk_dance`: Nhảy trượt ngang đa hướng kết hợp vẫy 2 tay theo nhịp nhạc BPM.
  * **Quy tắc chống ồn cơ khí lọt mic:** Chỉ chạy `Motion Bundle` khi không đang thu âm; ngay khi chuyển sang trạng thái `Listening` (nghe lệnh) thì khóa đứng yên toàn bộ 6 servo.

---

## 6. Phần mềm trên laptop HP Victus 15 (Kiến trúc Modular)

### 6.1. Cấu trúc thư mục mã nguồn (Đã hoàn thiện & Kiểm thử 100%)

```text
teo_sim_AI/
├── .env                  # Lưu DEEPSEEK_API_KEY, TEO_TTS_MODE, TEO_SHARED_SECRET
├── ANTIGRAVITY.md        # Chuẩn đặc tả Agent GitHub Spec-Kit SDD (Specification-Driven Development)
├── config.py             # Hằng số, PIPER_PROFILES (chipmunk, diemdam, tramvang), SYSTEM_PROMPT tĩnh
├── audio_io.py           # Auto-VAD (0.7s), Google ASR, Piper VITS Offline + GoogleTTS, pycaw Auto-Ducking
├── brain.py              # Lõi DeepSeek Streaming 3 tầng & bộ điều phối Tool Call
├── main.py               # Điểm khởi chạy chính (Entry point)
├── teo_walle.xml         # Mô hình 3D MuJoCo (Kiwi Drive + omni_pad_tail + integrator="implicitfast")
├── teo_sim_runner.py     # Cửa sổ mô phỏng 3D MuJoCo nhận lệnh UDP socket (127.0.0.1:5555)
├── test_tools.py         # Unit tests cho 12 công cụ cốt lõi (20 tests pass 100%)
├── test_sim_integration.py # Integration tests kiểm thử giao tiếp UDP với MuJoCo (4 tests pass 100%)
└── tools/                # Hệ thống 12 công cụ cốt lõi chia theo module chức năng
    ├── __init__.py       # Registry gom TOOLS_SCHEMA & dispatch hàm thực thi an toàn
    ├── motion.py         # di_chuyen_banh_omni (Kiwi kinematics) & cu_chi_motion_bundle
    ├── doc.py            # doc_tai_lieu_va_truyen (MarkItDown + Piper Offline Bookmark)
    ├── system.py         # thay_doi_giong_noi (Piper switch) & hen_gio_pomodoro
    ├── vision.py         # nhin_man_hinh_laptop (PIL + DeepSeek Vision)
    ├── media.py          # phat_nhac_youtube (webbrowser + pycaw ducking)
    ├── productivity.py   # doc_clipboard_laptop (pyperclip Ctrl+C)
    └── knowledge.py      # ghi_nho_thong_tin, tim_lai_ky_uc (SQLite) & tim_kiem_duckduckgo
```

### 6.2. Hệ thống Công cụ (Tools) & Chuẩn GitHub Spec-Kit `ANTIGRAVITY.md`

* **Chuẩn hóa Agent theo GitHub Spec-Kit (`ANTIGRAVITY.md`):** Dự án áp dụng phương pháp luận Specification-Driven Development (SDD) chuẩn quốc tế thay cho tệp `AGENTS.md` cũ, định nghĩa rõ ràng: System Prompt, 12 Core Tool Schemas, Giao thức Wi-Fi an toàn (HMAC-SHA256 Auth + Nonce chống Replay Attack), Quy tắc xác nhận người dùng (HITL - Human-in-the-Loop) và Tiêu chí nghiệm thu tự động (Acceptance Criteria).
* **Đã hoàn thành 100% Bộ công cụ Cốt lõi (12 tools):**
  1. *Nhóm Chuyển động (2):* `di_chuyen_banh_omni` (trượt đa hướng Kiwi Drive), `cu_chi_motion_bundle` (vẫy tay, gật đầu, lắc cổ, nhảy nhạc, lượn vòng cung).
  2. *Nhóm Thư ký & Đọc tài liệu (2):* `doc_tai_lieu_va_truyen` (MarkItDown + Piper Offline Bookmark lưu vị trí), `thay_doi_giong_noi` (chuyển đổi tức thời 3 phong cách Piper).
  3. *Nhóm Năng suất & Tiện ích (3):* `doc_clipboard_laptop` (đọc nội dung bôi đen `Ctrl+C`), `nhin_man_hinh_laptop` (chụp màn hình gửi DeepSeek Vision), `hen_gio_pomodoro` (bộ đếm giờ tập trung phát giọng nói).
  4. *Nhóm Ký ức & Tri thức (3):* `ghi_nho_thong_tin` (lưu vào CSDL SQLite lâu dài), `tim_lai_ky_uc` (truy vấn ký ức theo ngữ nghĩa), `tim_kiem_duckduckgo` (cập nhật thông tin thời sự mới nhất).
  5. *Nhóm Giải trí & Hội thoại (2):* `phat_nhac_youtube` (mở nhạc kèm auto-ducking `pycaw`), `tro_chuyen_va_hoi_dap`.
* *Lưu ý:* Các công cụ can thiệp sâu hệ thống Đợt 3 (`mo_ung_dung_va_workspace`, `tim_va_don_dep_file`, `dieu_khien_he_thong_windows`) tạm hoãn, sẽ triển khai sau khi hoàn tất phần cứng.

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
| **1** | Hoàn thiện bộ công cụ Thư ký trên Laptop (Đọc/Tóm tắt PDF `doc_reader.py`, Clipboard, Chụp màn hình Vision, Pomodoro, SQLite Long-term Memory, DuckDuckGo Search), xây dựng & kiểm chứng mô phỏng 3D `MuJoCo` (Kiwi Drive + đệm chống lật đuôi `omni_pad_tail`) và thiết lập đặc tả chuẩn **`ANTIGRAVITY.md`** (GitHub Spec-Kit). | **ĐÃ HOÀN THÀNH (100% - 0 đồng)** |
| **2** | Mua bộ tối thiểu (ESP32-S3 N16R8, INMP441, MAX98357A + loa 3W, cảm biến chạm TTP223, breadboard, dây Dupont). Ghép mạch, nạp firmware `.bin` test qua Wi-Fi LAN; thu âm trên **Edge Impulse** và nạp bản nhận từ khóa **`"Ê Tèo"`**. | **Sẵn sàng thực hiện (~0,25–0,45 triệu)** |
| **3** | Thêm màn hình LCD ST7789 hiển thị hai mắt hoạt hình. Cấu hình hoàn chỉnh nguồn laptop không ngủ khi cắm sạc và Task Scheduler tự chạy server. | **~0,1–0,15 triệu** |
| **4** | Lắp module I2C `PCA9685` + 2 micro servo `MG90S 180°` (2 cánh tay, đã bỏ servo cổ) + vòng LED `WS2812`; nạp các gói cử chỉ mượt **Motion Bundle** (`wave_greeting`, `happy_dance`). | **~0,12–0,18 triệu** |
| **5** | Gắn cảm biến hiện diện `HLK-LD2410C` (chân 2.54mm) + tính năng tự mở mắt chào và đọc Bản tin buổi sáng khi chủ nhân ngồi vào bàn. | **~0,08–0,12 triệu** |
| **6** | Lắp module camera riêng (`XIAO ESP32S3 Sense` / `ESP32-S3-CAM`) + kết nối vào tool `nhin_qua_camera_teo()`. | **~0,2–0,35 triệu** |
| **7** | Mở khóa các tool có thể ghi/hành động trên laptop (Mở Workspace ứng dụng, Dọn file Downloads, Khóa/Tắt máy có xác nhận giọng nói). | **0 đồng** |
| **8** | Lắp hệ thống **Pack Pin 2S 7.4V 18650 (2000–2600mAh bọc màng co sẵn Jack SM-2P & BMS)** + Module sạc Type-C IP2326 (kết nối không hàn qua kẹp CH-2) + **2 mạch hạ áp MINI560 5V hàn sẵn rào chân** đặt trên vách ngăn `teo_vach_ngan`, giắc `SM-2P` đưa lên kẹp ngắt nguồn nhanh dưới mũ đầu nam châm (bỏ công tắc `KCD11`). | **~0,18–0,3 triệu** |
| **9** | **Lắp Cụm 3 bánh xe đa hướng (`Nexus 14108` $\varnothing 48 \times 25.5\text{ mm}$ kiểu `LeKiwi`, $R = 58\text{ mm}$):** Gắn 3 bánh qua 3 hub in 3D `teo_hub_banh_omni` vào **3 Servo `MG90S 360°`** khóa bằng nẹp vít `teo_nep_giu_servo` (2 bánh trước $\pm 60^\circ$, 1 bánh sau $180^\circ$) + 3 cảm biến IR chống rơi đối xứng $120^\circ$ + 2 đệm nỉ chống lật đuôi. | **~0,25–0,4 triệu** |
| **10** | **In 3D Thân vỏ Unibody CAD v10 & Kính cong SLA:** In 11 file `.step`/`.stl` (19 chi tiết: thân dưới, vách ngăn, thân trên, khay linh kiện `Pin-Up`, mũ đầu nam châm, kính SLA, nắp hộp loa, tay ×2, nắp chụp tay ×2, hub bánh Omni ×3, nẹp giữ servo ×5), xem `thong-so-thiet-ke-vo-robot-teo.md`. | **~0,2–0,35 triệu** |

---

## 9. Bảo mật & Quyền riêng tư

* Luôn dùng `allowlist` thư mục (`ALLOWED_DIRS`), tách biệt tool đọc/ghi, bắt buộc xác nhận người dùng (Human-in-the-Loop - HITL) bằng giọng nói trước khi xóa file hoặc tắt máy.
* Giao thức truyền tin Wi-Fi an toàn giữa Laptop và ESP32 sử dụng chữ ký HMAC-SHA256 (`TEO_SHARED_SECRET`) kèm Nonce ngẫu nhiên chống tấn công phát lại (Replay Attack).
* Không mở cổng (port forwarding) ra Internet; dùng Tailscale nếu cần kết nối từ xa.
* Làm nắp che cơ học cho camera và bật đèn LED báo hiệu khi chụp ảnh.
* Giữ khóa API trong file `.env` cục bộ (đã đưa vào `.gitignore`).

---

## 10. Danh sách việc cần kiểm chứng (Checklist)

* [x] **Kiểm tra VRAM thực tế của RTX 3050 trên HP Victus 15:** Đã xác nhận bản **6GB VRAM (`6144 MiB`)**.
* [x] **Tối ưu độ trễ giọng đọc tiếng Việt (TTS) & Chống lỗi mất câu:** Đã giải quyết triệt để bằng **Piper VITS Offline** (3 giọng: Sóc chuột, Điềm đạm, Trầm vang — độ trễ ~60–120ms) kết hợp `GoogleTTS` cho ngoại ngữ trong `audio_io.py`.
* [x] **Pipeline Streaming 3 tầng & Chống vỡ Prompt Cache DeepSeek:** Đã triển khai trong `brain.py` và `config.py` (tổng phản hồi Câu 1 đạt ~1,0–1,2 giây).
* [x] **Hook tự động hạ nhỏ nhạc trình duyệt khi nói:** Đã tích hợp `pycaw` trong `audio_io.py`.
* [x] **Kiểm chứng cơ chế chống lật & phân bổ trọng tâm CoM trên Mô phỏng 3D MuJoCo:** Đã giải quyết triệt để vấn đề phản lực quán tính bằng đệm chống lật đuôi (`omni_pad_tail`), bố trí CoM thấp $\le 3\text{ cm}$ và bộ lọc tốc độ servo ($\alpha = 0.15$), triệt tiêu hoàn toàn lỗi nổ gia tốc `QACC NaN`.
* [x] **Nghiên cứu `SIGRobotics-UIUC/LeKiwi` & `Ekumen-OS/lekiwi`:** Đã chốt chuyển từ Đế bánh xích sang **Đế 3 bánh Omni (Kiwi Drive)** dùng 3 Servo `MG90S 360°` cắm thẳng vào `PCA9685` (bỏ mạch cầu H `DRV8833` và không cần mua Raspberry Pi 5).
* [x] **Hoàn thiện các Tool Đợt 1 & Đợt 2 trên Laptop:** Hoàn thành 100% 12 công cụ cốt lõi (Kiwi Drive 3D Sim, Motion Bundle, Doc Bookmark, Clipboard `Ctrl+C`, Chụp màn hình Vision, Pomodoro, SQLite Long-term Memory, DuckDuckGo Search) với 24/24 unit tests & integration tests pass.
* [x] **Chuẩn hóa Agent theo GitHub Spec-Kit SDD (`ANTIGRAVITY.md`):** Đã thay thế `AGENTS.md` bằng tài liệu đặc tả `ANTIGRAVITY.md` chuẩn quốc tế, tích hợp cơ chế bảo mật HMAC-SHA256 và quy chuẩn kiểm thử tự động.
* [x] **Hoàn thiện CAD v10 (`build_teo_cad.py`) & Chạy kiểm chứng MuJoCo (07/11/2026):** Đã dựng mới tham số hóa 11 file `.step`/`.stl` (`116 × 120 × 142 mm`, $R_{\text{wheel}} = 58.0\text{ mm}$, bánh đôi `Nexus 14108`, camera `ESP32-CAM OV3660`, nẹp vít 5 servo không keo, kiểm định Boolean `0.00 mm³` giao cắt), đồng bộ `teo_walle.xml` + `teo_sim_runner.py` và vượt qua 100% bài test động lực học & 24/24 unit/integration tests.
* [ ] **In thử đồ gá nhanh trước khi in nguyên bộ vỏ lớn:** In trước 1 `teo_hub_banh_omni` + 1 `teo_nep_giu_servo` để ướm thử độ khít với sừng chữ thập `MG90S` và lỗ trục $\varnothing 13.9\text{ mm}$ của bánh `Nexus 14108` trên máy in thực tế, sau đó tiến hành in toàn bộ thân vỏ trong OrcaSlicer.
* [ ] **Kiểm tra thực tế ở Bước 2 & Bước 9:** Thu âm model `"Ê Tèo"` trên Edge Impulse và ráp thử nghiệm mạch ESP32-S3 cùng đế 3 bánh xe Omni kèm đệm chống lật đuôi trên mặt bàn làm việc thật.

---

## Nguồn tham khảo

* Tài liệu gốc: "Kiến trúc Hệ thống Robot Agent Lai (Hybrid Edge-Cloud) trên Nền tảng ESP32-S3 và Laptop HP Victus 15"
* DeepSeek API Docs: https://api-docs.deepseek.com/quick_start/pricing
* SIGRobotics UIUC LeKiwi (3-Wheel Omni Kiwi Drive Hardware): https://github.com/SIGRobotics-UIUC/LeKiwi
* Ekumen-OS LeKiwi (Holonomic Omni Wheel Kinematics & Gazebo Sim): https://github.com/Ekumen-OS/lekiwi
* KingKongRobotics Jumper AI Toolkit (`AGENTS.md` & Motion Bundle architecture): https://github.com/KingKongRobotics/jumper
* Edge Impulse Audio Classification & Keyword Spotting: https://docs.edgeimpulse.com/docs/tutorials/end-to-end-tutorials/audio-classification