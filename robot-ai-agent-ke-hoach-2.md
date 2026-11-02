# Kế hoạch dự án Robot AI trợ lý "Tèo" (ESP32-S3 + xiaozhi-esp32 + HP Victus 15)

Cập nhật: 02/11/2026 (Bản hoàn thiện sau rà soát kỹ thuật & tích hợp kỹ thuật từ `KingKongRobotics/jumper`)

> Giá, hạn mức miễn phí và tên model thay đổi rất nhanh. Mọi con số trong file này cần được đối chiếu với trang chính thức trước khi mua phần cứng hoặc nạp tiền API.

## 1. Quyết định đã chốt

| Hạng mục | Quyết định | 
| ----- | ----- | 
| **Tên gọi & Wake Word** | Tên robot là **"Tèo"**; gọi bằng từ khóa **`"Ê Tèo"`** hoặc **`"Tèo ơi"`** (tự huấn luyện bằng giọng thật trên **Edge Impulse** nhúng vào ESP32-S3, kết hợp chế độ **Hội thoại liên tục** không cần gọi lại ở từng câu). | 
| **Kích hoạt phụ trợ** | Phím tắt **`Alt + Space`** trên bàn phím laptop (khi đang ngồi làm việc) + **Cảm biến chạm điện dung TTP223** dán ẩn dưới đỉnh đầu (để vỗ tắt tiếng nhanh, xoa đầu hoặc gọi trong đêm khuya) thay cho nút BOOT cứng. | 
| **Mục đích** | Dùng hằng ngày như một trợ lý thư ký để bàn. | 
| **Server** | Chính laptop **HP Victus 15 (16GB RAM, RTX 3050)**, **không thuê server**. | 
| **LLM & Thị giác** | **DeepSeek** (dòng Flash — id `deepseek-flash` tích hợp sẵn cả xử lý văn bản và thị giác). | 
| **Vận hành nguồn** | Laptop **không cho ngủ khi cắm sạc, chỉ tắt màn hình** (mục 7, Hướng 1) kèm cơ chế tự giải phóng VRAM của GPU khi nhàn rỗi. Không cần chạy 24/7: nếu tắt laptop hẳn thì bật lại, khởi động dưới 5 phút là chấp nhận được. | 
| **Giữ lại** | Màn hình LCD, camera, 3 servo, cảm biến hiện diện (`HLK-LD2410C`), pin 2S 18650 (2 nhánh hạ áp độc lập), voiceprint (tích hợp trong model Wake Word của Edge Impulse), RAG. | 
| **Tính năng thêm** | Phát nhạc/YouTube kèm hook `pycaw` tự vặn nhỏ nhạc khi nói (6.7), tóm tắt và đọc to văn bản (6.6), đọc truyện (6.8), dịch thuật tự đổi giọng TTS (6.9), đung đưa/nhảy theo nhịp nhạc bằng cơ chế **Motion Bundle** (5.4), tự động hóa viết code kỹ năng mới bằng **`AGENTS.md` & `.claude/skills`** (6.2). | 
| **Hình dáng** | Chiều cao cỡ một lon Red Bull; **dáng tham khảo kiểu WALL-E** (thân hộp, đầu gắn cổ, hai tay, đế bánh xích). **Đã chấp nhận chiều rộng 8–10 cm** để làm đế bánh xích và **bỏ hướng nhiều chân**. Dùng chung 1 module **PCA9685 (16 kênh PWM)** để điều khiển cả 3 servo lẫn driver động cơ bánh xích. | 
| **Vỏ robot** | Chưa cần đẹp (hộp nhựa hoặc bìa carton cứng ở giai đoạn đầu). | 
| **Ưu tiên** | Tổng chi phí thấp nhất (phần cứng + phí API). | 

Hệ quả: Bỏ failover cloud, mini server luôn bật và toàn bộ rắc rối về sleep/Wake-on-LAN. Laptop tắt hẳn thì robot không dùng được, và với cách dùng này thì hoàn toàn chấp nhận.

## 2. Những điểm cần kiểm chứng & Giải pháp khắc phục từ tài liệu gốc

Tài liệu gốc (kiến trúc hybrid edge-cloud) có ý tưởng tốt nhưng đã được hiệu chỉnh các điểm sau:

1. **Xử lý Tiếng Việt & Từ khóa đánh thức ("Ê Tèo"):** FunASR/SenseVoice nặng về Trung, Anh, Nhật, Hàn và WakeNet mặc định của ESP-SR không có sẵn từ khóa tiếng Việt. **Giải pháp:**

   * **ASR (Nghe câu lệnh):** Dùng **Groq Whisper (`whisper-large-v3-turbo`)** làm mặc định (để card rời RTX 3050 được nghỉ ở mức 0W khi tắt màn hình) và **`faster-whisper turbo (int8)` trên RTX 3050** làm dự phòng cục bộ (hoặc tự xả khỏi VRAM sau 5 phút nghỉ).

   * **TTS (Đọc phản hồi):** Dùng **EdgeTTS** (`vi-VN-HoaiMyNeural`, `vi-VN-NamMinhNeural`) kèm **`piper-tts` (chạy CPU)** làm dự phòng khi đọc văn bản dài.

   * **Wake Word + Voiceprint:** Tự thu âm giọng thật từ khóa **`"Ê Tèo"` / `"Tèo ơi"`** trên nền tảng **Edge Impulse** để xuất thư viện C++ TinyML (INT8 \~250KB) chạy ngoại tuyến trên ESP32-S3, kết hợp phím tắt `Alt + Space` trên laptop và cảm biến chạm TTP223 trên đỉnh đầu.

2. **VRAM chỉ khoảng 4GB** (một số bản 6GB, kiểm tra bằng `nvidia-smi`): Không đủ để chạy LLM cục bộ tốt, và mô hình nhỏ gọi tool kém. Toàn bộ suy luận LLM được đẩy sang API `deepseek-flash`.

3. **Lỗi lệnh ngủ:** `psshutdown64.exe -d` là *suspend* (S0ix), đúng chế độ cần tránh trên Victus. Nếu cần ngủ đông thì dùng `shutdown /h` (hibernate), bật bằng `powercfg /hibernate on`.

4. **Wake-on-LAN chỉ đáng tin qua cáp Ethernet:** WoL qua Wi-Fi từ trạng thái hibernate/tắt thường không hoạt động. Với quyết định dùng Hướng 1 (không ngủ khi cắm sạc, chỉ tắt màn hình), hệ thống bỏ qua sự phụ thuộc vào WoL.

5. **"24/7, không gián đoạn" là nói quá:** Failover có độ trễ, mất ngữ cảnh, và bản cloud không đụng được tool trên laptop.

6. **Khác biệt giữa các nhánh mã nguồn:** Các cờ như `CONFIG_STACKCHAN_MDNS_DISCOVERY` thuộc nhánh fork `stackchan-mcp`, còn endpoint `/xiaozhi/echo` thuộc `xiaozhi-openclaw-bridge`, không có sẵn trong mã gốc `78/xiaozhi-esp32` hay bản Minimal mặc định. Cần viết thêm route webhook nội bộ `/api/speak` hoặc cài kèm bridge tương ứng.

## 3. Kiến trúc tổng thể

```
[Robot "Tèo" - ESP32-S3 N16R8] -- WebSocket (Wi-Fi 2.4GHz, LAN) --> [Laptop HP Victus 15 (Windows 11)]
 |- Âm thanh: Mic INMP441, Ampli MAX98357A + Loa 3W                  xiaozhi-esp32-server (Minimal Install)
 |- Kích hoạt: Model "Ê Tèo" (Edge Impulse) + Chạm TTP223            |- Kích hoạt phụ: Phím tắt Alt+Space
 |- Hiển thị & Cảm biến: LCD ST7789, LED WS2812, HLK-LD2410C         |- ASR: Groq Whisper (chính) | faster-whisper GPU (dự phòng/auto-unload)
 |- Điều khiển xung I2C: Module PCA9685 (16 kênh PWM)                |- LLM & Vision: DeepSeek API (deepseek-flash + Dynamic Suffix Cache)
 |   |- Kênh 0..2: 3 Micro Servo MG90S (Cổ + 2 Tay)                  |- TTS: EdgeTTS (đa ngữ) + piper-tts CPU (dự phòng đọc dài)
 |   |- Kênh 3..6: Driver DRV8833/TB6612 --> Đế bánh xích + IR       |- Audio Hook: pycaw (tự hạ nhạc YouTube xuống 10% khi nghe)
 |   +- Motion Bundles: wave, nod, happy_dance (nội suy mượt cục bộ) |- FastMCP tools: todo, PDF, file, RAG (bge-m3 CPU), dịch, đọc truyện...
 +- Nguồn: Pin 2S 18650 + BMS --> 2 Mạch hạ áp MINI560 5V độc lập    +- Quy chuẩn AI Coding: AGENTS.md + .claude/skills (tự sinh tool mới)
 [Module Camera riêng: XIAO ESP32S3 Sense / S3-CAM] <-- HTTP /capture -- tool nhin()
```

**Nguyên tắc cốt lõi:** ESP32-S3 chỉ lo vào/ra (mic, loa, màn hình, cảm biến, chạy gói chuyển động `Motion Bundle` qua `PCA9685` và chạy model TinyML bắt từ khóa *"Ê Tèo"*). Mọi suy luận LLM, lưu trữ ngữ cảnh hội thoại và công cụ thư ký nằm hoàn toàn ở laptop.

## 4. Pipeline và chi phí vận hành

| Khâu | Lựa chọn | Chi phí | 
| ----- | ----- | ----- | 
| **Wake Word & Voiceprint** | Model TinyML **"Ê Tèo"** (Edge Impulse INT8 chạy trên ESP32-S3) | 0 đồng | 
| **ASR (Nhận diện giọng nói)** | **Groq Whisper (`whisper-large-v3-turbo`)** làm mặc định (để GPU nghỉ) + **`faster-whisper turbo (int8)` trên RTX 3050** (tự xả VRAM sau 5 phút) làm dự phòng | 0 đồng | 
| **LLM & Thị giác (Vision)** | **DeepSeek Flash (`deepseek-flash`)** tích hợp sẵn Vision (mục 4.1 & 4.2) | Rất thấp (\~0,45–0,85 USD/tháng) | 
| **TTS (Tổng hợp giọng nói)** | **EdgeTTS** (giao tiếp & dịch thuật) + **`piper-tts` trên CPU** (dự phòng khi đọc sách/truyện dài) | 0 đồng | 
| **Embedding (RAG)** | `bge-m3` chạy trên **CPU** của laptop | 0 đồng | 

*Ghi chú hạn mức Groq Whisper gói Free:* 20 request/phút, 2.000 request/ngày, 7.200 giây audio/giờ, 28.800 giây/ngày (mỗi request tính tối thiểu 10 giây). Với nhu cầu \~100 câu lệnh/ngày (khoảng 1.000 giây tính cước), bạn mới chỉ dùng hết \~3,5% hạn mức miễn phí mỗi ngày. Trả phí khoảng 0,04 USD/giờ audio (bản turbo).

### 4.1. DeepSeek làm LLM & Kỹ thuật chống vỡ Prompt Cache

* **Endpoint tương thích OpenAI:** `https://api.deepseek.com`.

* **ID Model hiện hành (Tháng 10/2026):** `deepseek-flash` (trỏ tới bản V4.1 Flash cập nhật tháng 10/2026, đã hỗ trợ đọc ảnh trực tiếp).

* **Bảng giá thực tế:**

  * *Giờ thấp điểm (Off-peak):* Đầu vào **0,15 USD/1M token** (Cache Miss), **0,003 USD/1M token** (Cache Hit — rẻ hơn 50 lần), đầu ra **0,60 USD/1M token**.

  * *Giờ cao điểm (Peak hours - 08:00–11:00 và 13:00–17:00 giờ VN từ Thứ 2 đến Thứ 6):* Nhân đôi (0,30 USD/1M vào khi Cache Miss, 1,20 USD/1M ra).

* **Chọn dòng Flash cho giọng nói**, không dùng Pro hay chế độ suy luận (thinking) vì độ trễ.

* **Ước tính chi phí:** 100 lệnh/ngày $\times$ \~1.500 token vào + 200 token ra $\approx$ 4,5M token vào + 0,6M token ra mỗi tháng. Khi áp dụng kỹ thuật tối ưu Cache Hit dưới đây, tổng chi phí thực tế chỉ khoảng **0,45 – 0,85 USD/tháng (\~12.000đ – 22.000đ/tháng)**.

**Kỹ thuật tối ưu "Dynamic Suffix Injection" (Chống vỡ Cache 100%):**

* *Vấn đề:* `xiaozhi-esp32-server` mặc định chèn biến giờ hiện tại (`current_time`) vào đầu `system_prompt`. Chỉ cần nhảy sang phút mới là toàn bộ `system_prompt` và 15 JSON Schema của FastMCP bị tính là **Cache Miss**.

* *Cách làm:*

  1. Xóa mọi biến thời gian động khỏi `system_prompt` trong `.config.yaml`, giữ `system_prompt` và danh sách 10–15 tool **cố định tuyệt đối từng byte** giữa các lượt.

  2. Trong hàm Python gửi request của server, nối thông tin biến thiên (giờ hiện tại, đoạn văn bản RAG, trạng thái) vào **cuối tin nhắn `user` mới nhất** (`messages[-1]`): `"[Giờ hệ thống: 11:30 02/11/2026] " + user_text`.

**Cấu hình mẫu** (trong `.config.yaml` của `xiaozhi-esp32-server`):

```yaml
selected_module:
  LLM: DeepSeekLLM
LLM:
  DeepSeekLLM:
    type: openai
    model_name: deepseek-flash      # kiểm tra id trong docs
    base_url: https://api.deepseek.com
    api_key: <khóa_của_bạn>         # không đưa lên Git
```

**Lưu ý khi dùng:**

* Trả lời ngắn, nói được: 1–3 câu, không markdown, không danh sách, không emoji, đọc số/ngày dạng lời nói.

* Giữ danh sách tool ngắn (khoảng 10–15), mô tả rõ. Giữ `strict_input_validation=False` mặc định của FastMCP để tự ép kiểu.

* Máy chủ ở nước ngoài nên có lúc chậm/bận. Bật streaming, đặt timeout, cho robot câu báo lỗi rõ ràng.

* Nạp tiền trả trước (Prepaid Top-up khoảng 2–5 USD bằng thẻ Visa/Mastercard) làm trần chi tiêu tự nhiên.

### 4.2. Thị giác (Camera)

* Dùng trực tiếp model **`deepseek-flash`** (mỗi ảnh tính tối đa 384 token theo chuẩn V4.1 Flash Vision, gửi qua base64, URL hoặc Files API) để đồng nhất 1 API key và 1 ví nạp tiền.

* **Phương án dự phòng miễn phí:**

  * Groq: các model Llama 4 Scout/Maverick (hỗ trợ ảnh) trong gói free.

  * Zhipu `glm-4v-flash`, Qwen-VL qua Alibaba Bailian (có hạn mức miễn phí).

  * Gemini Flash/Flash-Lite qua AI Studio (không đưa ảnh riêng tư qua gói free).

  * Cục bộ: VLM nhỏ (Qwen2.5-VL-3B, Gemma 3 4B, moondream) qua Ollama (chỉ dùng khi thật cần vì VRAM 4GB chật).

## 5. Phần cứng

### 5.1. Danh sách mua (Chọn phân loại "Đã hàn chân" để cắm Breadboard/Dupont)

**Bộ tối thiểu — Giai đoạn Bước 2 (khoảng 0,25–0,45 triệu đồng):**

* 1 $\times$ Bo mạch **ESP32-S3 DevKitC N16R8** (chọn loại đã hàn sẵn chân kim).

* 2 $\times$ Mic kỹ thuật số I2S **INMP441** (mua dư 1 cái dự phòng, chọn loại đã hàn chân).

* 1 $\times$ Ampli I2S **MAX98357A** + 1 $\times$ **Loa 3W (**$4\Omega$ **hoặc** $8\Omega$**)** có sẵn dây.

* 2 $\times$ Cảm biến chạm điện dung **TTP223** (\~3.000đ/cái, dán dưới đỉnh đầu để chạm/vỗ tắt tiếng).

* 1 $\times$ Bảng cắm **Breadboard MB-102 (830 lỗ)** + 1 bộ **Dây cắm Dupont** (Đực-Đực, Đực-Cái, Cái-Cái).

**Phần mở rộng thân trên WALL-E — Giai đoạn Bước 3 đến Bước 8 (khoảng 0,5–0,85 triệu đồng):**

* 1 $\times$ Màn hình **LCD SPI ST7789** (kích thước 1.54"–2.4", độ phân giải $240\times 240$ hoặc $240\times 320$ để hiển thị đôi mắt hoạt hình của Tèo trên cùng một màn hình).

* 1 $\times$ Module camera độc lập: **XIAO ESP32S3 Sense** (siêu nhỏ $2,1 \times 1,8\text{ cm}$) hoặc **ESP32-S3-CAM (OV2640/OV5640)**.

* 3 $\times$ Micro Servo **MG90S** (bánh răng kim loại, bền hơn SG90) cho cổ và 2 tay.

* 1 $\times$ Module điều khiển xung I2C **PCA9685 (16 kênh PWM)**: Chỉ tốn 2 chân I2C của ESP32-S3 nhưng điều khiển được cả **3 Servo MG90S** lẫn **4 kênh PWM của mạch động cơ đế bánh xích**.

* 1 $\times$ Cảm biến hiện diện mmWave **HLK-LD2410C** (*Lưu ý bắt buộc:* Chọn đúng bản **LD2410C** có chân kim chuẩn **2.54mm** cắm vừa dây Dupont; tránh mua bản LD2410B chân 1.27mm).

* 1 $\times$ Vòng LED **WS2812** (tùy chọn).

* **Hệ thống Pin tách 2 nhánh (Làm ở Bước 8):** 2 cell pin **18650 chính hãng nối tiếp (2S = 7.4V–8.4V)** + mạch bảo vệ sạc xả **BMS 2S** + **2 mạch hạ áp Buck MINI560 5V** (1 mạch cấp riêng đường 5V "Sạch" cho ESP32/Loa/Mic/LCD; 1 mạch cấp riêng đường 5V "Cơ bắp" cho Servo/Motor).

**Đế bánh xích kiểu WALL-E — Giai đoạn Bước 9 (khoảng 0,3–0,6 triệu đồng):**

* 1 $\times$ Kit khung xe bánh xích mini (rộng 8–10 cm, có sẵn 2 động cơ DC/N20, ưu tiên xích cao su để bám mặt bàn).

* 1 $\times$ Mạch cầu H điều khiển động cơ **DRV8833** hoặc **TB6612FNG** (cắm 4 dây tín hiệu IN1..IN4 vào các kênh PWM còn trống trên mạch PCA9685, **không cần mua thêm vi điều khiển ESP32-C3 riêng** để tránh nhiễu sóng Wi-Fi 2.4GHz nội bộ).

* 2 $\times$ Cảm biến hồng ngoại tránh rơi mép bàn (IR Obstacle Sensor hướng xuống gầm xe).

Tổng dự kiến khoảng 1,0–1,8 triệu đồng cho toàn bộ lộ trình.

### 5.2. Tiết kiệm

* Dùng **cảm biến chạm TTP223** (3.000đ) kết hợp **nút BOOT có sẵn** và phím tắt `Alt + Space` trên laptop.

* Ở giai đoạn đầu (Bước 2–7), cấp nguồn trực tiếp qua **cổng USB laptop** hoặc củ sạc điện thoại sẵn có.

* Vỏ ban đầu: hộp nhựa hoặc bìa carton cứng + keo nến.

* Mua phần cứng **sau khi** đã kiểm chứng pipeline phần mềm (mục 8, Bước 0).

### 5.3. Lưu ý kỹ thuật & Chống nhiễu

* **Quản lý chân GPIO:** Màn hình SPI \~6 chân, mic I2S 3, ampli I2S 3, chạm TTP223 1, I2C PCA9685 2 (gánh toàn bộ 3 servo + 4 kênh motor bánh xích), LD2410C 1, chống rơi IR 2, đo pin ADC 1 $\rightarrow$ tổng cộng khoảng **19 chân**, nằm gọn trong giới hạn an toàn của ESP32-S3. Board N16R8 dùng PSRAM octal nên **tuyệt đối không dùng GPIO 35–37** (và các chân flash); tránh các chân strapping (GPIO 0, 3, 45, 46).

* **Camera đặt trên module riêng:** Camera DVP ngốn khoảng 14 chân nên tách sang `XIAO ESP32S3 Sense` / `ESP32-S3-CAM` có endpoint HTTP `/capture`; tool `nhin()` trên laptop lấy ảnh rồi gửi cho `deepseek-flash` mà không phải sửa firmware xiaozhi.

* **Cách ly nhiễu nguồn bằng 2 mạch hạ áp MINI560 5V:** Không dùng chung 1 bộ hạ áp 5V cho cả ESP32/Ampli và Servo/Motor. Tách 2 nhánh hạ áp 5V độc lập từ nguồn Pin 2S (7.4V–8.4V), nối chung mass (GND), giúp đường 5V nuôi ESP32 và Loa phẳng tuyệt đối ngay cả khi 3 servo và 2 motor đảo chiều đột ngột.

* **Cảm biến hiện diện:** Dùng chân `OUT` (1 GPIO, chuẩn chân 2.54mm trên `HLK-LD2410C`) cho sự kiện "có người / không có người".

* **Wi-Fi:** ESP32-S3 chỉ hỗ trợ 2.4GHz. Gán IP tĩnh (Static IP) hoặc DHCP reservation cho laptop.

### 5.4. Hình dáng, kích thước và chuyển động

**Mục tiêu:** Robot nhỏ cỡ một lon Red Bull (cao khoảng 13,5 cm), thân và đế bánh xích rộng khoảng **8–10 cm** theo dáng tham khảo kiểu **WALL-E** (thân hộp, đầu gắn cổ, hai tay, đế bánh xích). Đã bỏ hướng nhiều chân vì tốn quá nhiều servo (8–12 servo), nặng, ồn và vượt quá kích thước.

**Ba mức chuyển động** (làm tuần tự):

| Mức | Mô tả | Ghi chú | 
| ----- | ----- | ----- | 
| 0 | 0 servo: mắt hoạt hình trên màn hình LCD + vòng LED chớp theo nhịp | Rẻ, êm, ít điện | 
| 1 | 3 micro servo MG90S: xoay đầu + 2 tay (gật, vẫy, lắc theo nhịp) qua PCA9685 | Đủ để biểu cảm và nhảy tại chỗ | 
| 2 | Mức 1 + đế bánh xích (nối chung vào PCA9685) + 2 mắt IR chống rơi bàn | **Đã chọn**, lắp ở Bước 9 | 

**Cơ chế đóng gói "Motion Bundle" cho cử chỉ & Nhảy theo nhạc (Học từ `KingKongRobotics/jumper`):**

* **What (Nó là cái gì):** Thay vì điều khiển từng góc servo rời rạc qua mạng Wi-Fi (dễ bị giật cục do độ trễ và jitter), mỗi hành động biểu cảm và vũ đạo của Tèo được đóng gói sẵn thành một **Motion Bundle** (gói quỹ đạo chuyển động mượt theo hàm điều hòa sinusoid/spline) lưu trực tiếp trong firmware của ESP32-S3.

* **How (Làm như thế nào):**

  1. Định nghĩa sẵn 5–6 gói chuyển động mẫu trong C++ trên ESP32-S3 để xuất xung I2C sang mạch `PCA9685` (với tần số cập nhật 50Hz mượt mà và giới hạn góc an toàn):

     * `wave_greeting`: Nghiêng cổ nhẹ + vẫy tay phải chào 3 nhịp.

     * `nod_yes` / `shake_no`: Gật đầu / lắc cổ xác nhận.

     * `look_around`: Xoay cổ tìm kiếm kết hợp đảo mắt trên LCD.

     * `happy_dance`: Tổ hợp nhún nhẹ bánh xích tiến-lùi + lắc cổ + vẫy 2 tay lệch pha theo nhịp BPM.

  2. Khi LLM `deepseek-flash` muốn biểu cảm hoặc khi laptop phân tích xong nhạc (BPM, thời điểm bắt đầu), laptop chỉ cần gửi **1 lệnh JSON mức cao** xuống ESP32-S3: `play_motion(bundle="happy_dance", bpm=120, duration_s=15)`.

  3. ESP32-S3 tự nội suy góc quay theo đồng hồ nội bộ và chỉ đồng bộ lại pha nhịp mỗi vài giây (kèm tham số bù trễ âm thanh chỉnh tay).

* **Why (Tại sao lại làm như thế):** Giúp 3 servo `MG90S` và 2 bánh xích của Tèo chuyển động mềm mại, có hồn như robot cao cấp mà không tốn băng thông WebSocket, đồng thời kiểm soát được gia tốc góc để tránh giật dòng điện đột ngột.

* **Trade-off:** Cần khai báo trước bảng góc giới hạn (`min_angle`, `max_angle`) cho từng gói trong code C++ của ESP32-S3.

* **Chống ồn cơ khí lọt mic:** Tiếng motor, xích và servo gây nhiễu mic `INMP441`. Quy tắc: Chỉ chạy `Motion Bundle` khi không đang nghe; ngay khi chuyển sang trạng thái `Listening` (nghe lệnh) thì hàm `stop_motion()` lập tức khóa yên toàn bộ servo và motor.

**Kích thước linh kiện tham khảo:** ESP32-S3 DevKitC khoảng $7 \times 2,5\text{ cm}$; XIAO ESP32S3 Sense khoảng $2,1 \times 1,8\text{ cm}$; PCA9685 khoảng $6,2 \times 2,5\text{ cm}$; pin 18650 khoảng $1,8 \times 6,5\text{ cm}$; loa $2,8\text{ cm}$; HLK-LD2410C khoảng $1,6 \times 2,2\text{ cm}$; servo MG90S khoảng $2,3 \times 1,2 \times 2,2\text{ cm}$; MINI560 khoảng $2,0 \times 1,5\text{ cm}$.

## 6. Phần mềm trên laptop HP Victus 15

### 6.1. Server

* `xiaozhi-esp32-server` bản **Minimal Install**, bật cấu hình streaming.

* Chạy thẳng Python trên Windows 11 (hoặc WSL2 bật `networkingMode=mirrored`). Mở firewall cho các cổng server dùng (mặc định 8000/8003).

* Cho server **tự chạy khi đăng nhập Windows** bằng Task Scheduler.

### 6.2. FastMCP tools & Tự động hóa mở rộng bằng `AGENTS.md`

**Thứ tự xây dựng các nhóm công cụ:**

1. **Chỉ đọc trước:** Todo, ghi chú, tóm tắt PDF/Office (`markitdown`), lịch, thời tiết, tìm tài liệu (`tim_tai_lieu`). Kiểm thử bằng `MCP Inspector` rồi mới nối vào robot.

2. **Tool có thể ghi/hành động:** Thao tác file (trong `allowlist` thư mục), mở app, tắt máy. Thêm xác nhận bằng giọng nói.

3. **Tác vụ dài** dùng `agent_task` bất đồng bộ: trả `task_id` ngay, xong thì laptop đẩy văn bản vào hàng đợi phát âm thanh qua route nội bộ `/api/speak` (hoặc `/xiaozhi/echo` nếu cài kèm `xiaozhi-openclaw-bridge`) để Tèo báo lại.

4. Các công cụ nhạy cảm đăng ký bằng `AddUserOnlyTool` để LLM không tự ý gọi.

**Tự động hóa lập trình kỹ năng mới bằng `AGENTS.md` và `.claude/skills` (Học từ `KingKongRobotics/jumper`):**

* **What (Nó là cái gì):** Tổ chức một tệp quy chuẩn `AGENTS.md` và thư mục kỹ năng `.claude/skills` ngay trong thư mục dự án `xiaozhi-esp32-server` trên chiếc HP Victus 15 để biến các AI Coding Assistant (như Claude Code, Cline, Aider, Cursor trên VS Code) thành công cụ tự động viết, kiểm tra lỗi và đăng ký hàm `FastMCP` mới cho Tèo chỉ bằng 1 câu lệnh.

* **How (Làm như thế nào):**

  1. Tạo file `AGENTS.md` ở thư mục gốc của dự án trên laptop, định nghĩa rõ 4 quy tắc bắt buộc khi AI viết thêm tool cho Tèo:

     * Mẫu chuẩn (boilerplate) của một hàm `@mcp.tool()` với docstring tiếng Việt ngắn gọn để không làm tốn token của `deepseek-flash`.

     * Quy tắc đầu ra: Mọi chuỗi văn bản trả về cho Tèo đọc phải là văn nói thuần túy (1–3 câu, không markdown, không ký hiệu đặc biệt).

     * Quy tắc bảo mật: Bắt buộc kiểm tra đường dẫn qua mảng `ALLOWED_DIRS` nếu đụng tới file và dùng `agent_task` + `/api/speak` nếu tác vụ chạy lâu hơn 3 giây.

     * Lệnh kiểm thử tự động: Tự chạy `ruff check` kiểm tra cú pháp Python và test schema trên `MCP Inspector`.

  2. Tạo các khuôn mẫu kỹ năng trong `.claude/skills/` (ví dụ: `add-readonly-tool`, `add-async-reader-tool`, `add-motion-bundle`).

  3. Khi muốn dạy Tèo việc mới, bạn chỉ cần mở VS Code và gõ 1 câu tự nhiên: *"Thêm cho Tèo kỹ năng kiểm tra lịch thi trong file Excel và đọc to kết quả"*. AI Coding Agent sẽ đọc `AGENTS.md` và tự động viết code, kiểm tra lỗi rồi gắn vào server mà bạn không cần gõ tay.

* **Why (Tại sao lại làm như thế):** Giúp bạn mở rộng nhanh từ 10 công cụ ban đầu lên hàng chục kỹ năng thư ký cá nhân hóa với tốc độ cực nhanh và chuẩn hóa 100%, không bao giờ bị lỗi lệch định dạng làm vỡ Prompt Cache của DeepSeek.

* **Trade-off:** Mất khoảng 15 phút ở Bước 1 để khởi tạo file `AGENTS.md` đầu tiên cho dự án.

### 6.3. Quy trình huấn luyện "Ê Tèo" kiêm Voiceprint trên Edge Impulse

Thay vì chạy thêm model Voiceprint riêng tốn tài nguyên, kết hợp huấn luyện từ khóa đánh thức và nhận diện giọng chủ nhân ngay trên **Edge Impulse**:

1. **Thu thập mẫu (16.000 Hz, cửa sổ 1 giây):**

   * Nhãn `e_teo` (\~50 mẫu): Giọng thật của bạn gọi *"Ê Tèo"* / *"Tèo ơi"* ở khoảng cách 30cm – 2m.

   * Nhãn `unknown` (\~50 mẫu): Các từ tiếng Việt dễ nhầm có vần *"èo"* (*"con mèo, bánh bèo, trèo cây"*) và câu nói thường.

   * Nhãn `noise` (3–5 phút cắt đoạn 1 giây): Tiếng quạt laptop Victus 15, tiếng gõ phím, tiếng ồn nền.

2. **Cấu trúc Impulse:** Khối `Audio (MFCC)` hoặc `Audio (MFE)` $\rightarrow$ Khối `Classification (Keras 1D/2D Conv)`.

3. **Đóng gói:** Xuất `C++ Library / ESP-IDF Component` với `EON Compiler (Quantized int8)` (\~200KB) nhúng vào luồng đọc mic I2S của ESP32-S3.

4. **Hội thoại liên tục:** Sau khi gọi *"Ê Tèo"* 1 lần để mở phiên, Tèo tự động mở lại mic sau mỗi câu trả lời cho đến khi hết việc (im lặng 10–15 giây hoặc bảo *"Nghỉ đi"*), không cần gọi lại *"Ê Tèo"* ở từng câu.

### 6.4. RAG

* Embedding `bge-m3` chạy trên **CPU** (chỉ lập chỉ mục một lần, truy vấn rất nhanh, tốn 0 MB VRAM).

* Vector DB dạng nhúng: ChromaDB, Qdrant hoặc LanceDB. Đọc tài liệu bằng `markitdown`.

* Đóng gói thành tool MCP `tim_tai_lieu`; chỉ gửi vài đoạn liên quan cho `deepseek-flash`.

### 6.5. Camera, quyền riêng tư

* Chỉ chụp khi có lệnh `nhin()`, không phát video trực tiếp.

* Có nắp che cơ học và đèn LED báo khi chụp.

* Không đưa ảnh/tài liệu nhạy cảm qua các gói API miễn phí dùng dữ liệu để huấn luyện.

### 6.6. Tóm tắt văn bản và đọc to

* **Đọc nguyên văn không cần qua LLM:** LLM chỉ hiểu lệnh (*"đọc tài liệu X"*), sau đó tiến trình nền trên laptop cắt văn bản thành câu rồi đẩy lần lượt cho TTS qua `/api/speak`. Không tốn token LLM cho phần đọc và không bị giới hạn độ dài đầu ra.

* Lưu trạng thái phiên đọc (tài liệu nào, đang ở câu nào) ra file JSON và hỗ trợ các lệnh: dừng, tiếp, đọc lại, đọc từ đầu.

* **Tóm tắt:** `markitdown` trích văn bản $\rightarrow$ `deepseek-flash` tóm tắt với văn phong để nghe (câu ngắn, không ký hiệu).

* **Dự phòng EdgeTTS:** Dùng `EdgeTTS` làm chính; tự động chuyển (fallback) sang **`piper-tts` chạy CPU** nếu Microsoft giới hạn tốc độ khi đọc văn bản dài 20 trang.

### 6.7. Phát nhạc YouTube và Hook `pycaw` tự vặn nhỏ nhạc

* **Phát bản nhạc thật** trên laptop (Mức 1: mở trình duyệt/trình phát qua YouTube Data API; hoặc Mức 2: `mpv + yt-dlp` chỉ lấy âm thanh phát ra loa laptop/loa Bluetooth). Không dùng TTS để đọc lời bài hát.

* **Giải pháp Auto-Ducking bằng `pycaw` (Chống nhạc lọt mic robot):**

  * Trong `xiaozhi-esp32-server` trên Windows, dùng thư viện Python `pycaw` bắt bản tin WebSocket `{"type": "listen", "state": "start"}` (gửi lên ngay khi Tèo nghe *"Ê Tèo"*, hoặc khi bấm `Alt + Space` / chạm đầu).

  * Lập tức kéo âm lượng của riêng ứng dụng phát nhạc (`chrome.exe`, `msedge.exe`, `mpv.exe`) trong Windows Volume Mixer từ **100% xuống 10%**.

  * Khi Tèo trả lời xong (`tts: stop`), tự động nâng âm lượng nhạc về lại **100%**.

### 6.8. Đọc truyện

* Dùng chung cơ chế cắt câu + lưu vị trí đọc của mục 6.6.

* **Nguồn truyện:** Kho truyện hết hạn bản quyền, ebook cá nhân, hoặc truyện ngắn 1.000 từ do `deepseek-flash` sáng tác theo yêu cầu.

* Dùng `EdgeTTS` kèm dự phòng `piper-tts` trên CPU.

### 6.9. Dịch thuật tự động đổi giọng ngôn ngữ đích

* **Tự động chuyển giọng đọc theo ngôn ngữ:** Trước khi đẩy văn bản vào `EdgeTTS`, dùng hàm kiểm tra ngôn ngữ (`langdetect` hoặc bảng mã Unicode) để chọn đúng giọng bản xứ thay vì đọc tiếng nước ngoài bằng giọng Việt:

  * Tiếng Việt (`vi`) $\rightarrow$ `vi-VN-HoaiMyNeural`

  * Tiếng Anh (`en`) $\rightarrow$ `en-US-AvaNeural`

  * Tiếng Trung (`zh`) $\rightarrow$ `zh-CN-XiaoxiaoNeural`

  * Tiếng Nhật (`ja`) $\rightarrow$ `ja-JP-NanamiNeural`

  * Tiếng Hàn (`ko`) $\rightarrow$ `ko-KR-SunHiNeural`

* Hỗ trợ dịch khi hỏi, phiên dịch hai chiều, dịch tài liệu (`markitdown` + lưu file) và dịch chữ trên ảnh qua camera (`deepseek-flash` vision).

## 7. Khởi động và quản lý nguồn laptop HP Victus 15

**Đã chọn Hướng 1: Không cho ngủ khi cắm sạc, chỉ tắt màn hình (đơn giản và ổn định nhất).**

* **Thiết lập Windows 11:** Khi cắm sạc: `Sleep = Never`, tắt màn hình sau 3–5 phút, đóng nắp máy (`Closing the lid`) = `"Do nothing"` khi cắm điện (kê thoáng đáy máy).

* **Thiết lập Omen Gaming Hub & BIOS:** Chế độ quạt `Balanced` hoặc `Quiet`/`Eco`; bật giới hạn sạc pin (\~80% / Adaptive Battery Optimizer).

* **Để GPU RTX 3050 ngủ hoàn toàn (0W Idle):** Dùng **Groq Whisper API** làm ASR mặc định (hoặc tự xả `faster-whisper` khỏi VRAM sau 5 phút không dùng). Khi không có tiến trình giữ CUDA Context và màn hình tắt, công nghệ NVIDIA Optimus sẽ ngắt điện card rời, giúp toàn bộ laptop chỉ tiêu thụ khoảng **8W – 12W** (\~15.000đ – 25.000đ tiền điện/tháng).

* **Chống gián đoạn do Windows Update:** Đặt `Active Hours` và thiết lập Task Scheduler tự chạy lại server khi máy khởi động/đăng nhập.

* *(Hướng 2 ngủ S0ix + WoL và Hướng 3 Hibernate + WoL qua cáp Ethernet được lưu làm phương án tham khảo nếu sau này thay đổi nhu cầu).*

## 8. Lộ trình thực hiện từng bước

| Bước | Việc cần làm | Chi phí ước tính | 
| ----- | ----- | ----- | 
| **0** | Chạy `xiaozhi-esp32-server` Minimal trên HP Victus 15 + client giả lập trên PC + phím tắt `Alt + Space`. Kết nối `deepseek-flash` (áp dụng Dynamic Suffix Cache), `Groq Whisper` / `faster-whisper` và `EdgeTTS`. Thử 20 lệnh tiếng Việt gồm cả gọi tool, đo độ trễ và token. | **0 đồng** | 
| **1** | Thiết lập quy chuẩn **`AGENTS.md` & `.claude/skills`** để tự động hóa viết FastMCP tools chỉ đọc (Todo, PDF `markitdown`, RAG `bge-m3` CPU); viết route `/api/speak` đọc to + đọc truyện (kèm fallback `piper-tts`); thêm hook `pycaw` tự hạ âm lượng nhạc và tự đổi giọng TTS khi dịch thuật; thử thị giác bằng ảnh có sẵn. | **0 đồng** | 
| **2** | Mua bộ tối thiểu (ESP32-S3 N16R8, INMP441, MAX98357A + loa 3W, cảm biến chạm TTP223, breadboard, dây Dupont). Ghép mạch, nạp firmware `.bin` sẵn có để test phần cứng qua Wi-Fi LAN trước; sau đó thu âm trên **Edge Impulse** và nạp bản firmware nhận từ khóa **`"Ê Tèo"`**. | **\~0,25–0,45 triệu** | 
| **3** | Thêm màn hình LCD ST7789 hiển thị hai mắt hoạt hình. Cấu hình hoàn chỉnh nguồn laptop không ngủ khi cắm sạc và Task Scheduler tự chạy server. | **\~0,1–0,15 triệu** | 
| **4** | Lắp module I2C PCA9685 + 3 micro servo MG90S (đầu + 2 tay) + vòng LED WS2812; lập trình các gói cử chỉ mượt **Motion Bundle** (`wave_greeting`, `nod_yes`, `happy_dance`) đồng bộ nhịp nhạc (mục 5.4). | **\~0,15–0,2 triệu** | 
| **5** | Gắn cảm biến hiện diện `HLK-LD2410C` (chân 2.54mm) + tính năng tự mở mắt chào khi chủ nhân lại gần bàn làm việc. | **\~0,08–0,12 triệu** | 
| **6** | Lắp module camera riêng (`XIAO ESP32S3 Sense` / `ESP32-S3-CAM`) + kết nối vào tool `nhin()`. | **\~0,2–0,35 triệu** | 
| **7** | Mở khóa các FastMCP tool có thể ghi/hành động trên laptop (kèm `allowlist` và xác nhận giọng nói). | **0 đồng** | 
| **8** | Lắp hệ thống Pin 2S 18650 + BMS 2S + **2 mạch hạ áp MINI560 5V tách độc lập** nhánh Logic/Audio và nhánh Servo/Motor. | **\~0,18–0,3 triệu** | 
| **9** | Lắp đế bánh xích kiểu WALL-E (rộng 8–10 cm) + driver `DRV8833`/`TB6612` (nối vào 4 kênh PWM trống trên `PCA9685`) + 2 cảm biến IR chống rơi mép bàn. | **\~0,3–0,6 triệu** | 
| **10** | Tùy chọn: Hoàn thiện vỏ hộp WALL-E đẹp hơn, kết nối Telegram Bot, trợ lý ghi âm tóm tắt họp, Home Assistant. | **Tùy chọn** | 

Mỗi tính năng là một module độc lập để một cái hỏng không kéo theo cả robot.

## 9. Bảo mật

* LLM + shell + file + lệnh shutdown điều khiển bằng giọng nói rất nhạy cảm: luôn dùng `allowlist` thư mục, tách tool đọc/ghi, bắt xác nhận bằng giọng nói cho việc xóa/gửi/tắt máy.

* Không mở cổng (port forwarding) ra Internet. Nếu cần truy cập từ xa, dùng Tailscale hoặc Cloudflare Tunnel.

* Xử lý tài liệu cục bộ bằng `markitdown` và RAG `bge-m3`, chỉ gửi đoạn trích ngắn cần thiết lên API DeepSeek.

* Đặt khóa API trong file cấu hình cục bộ (`.config.yaml` / `.env`), thêm vào `.gitignore`.

## 10. Phương án server miễn phí (Không dùng hiện tại, lưu tham khảo)

* **xiaozhi.me (cloud chính thức):** Miễn phí, tool trên laptop nối ra qua MCPPipe (nhưng phụ thuộc model của họ và dữ liệu đi qua bên thứ ba).

* **Oracle Always Free (Ampere A1):** Đã giảm hạn mức còn 2 OCPU/12GB từ giữa tháng 6/2026; khó đăng ký và có thể bị thu hồi nếu nhàn rỗi.

* **Google Cloud e2-micro:** Chỉ có 1GB RAM, sát giới hạn.

* **Máy cũ tại nhà** (Raspberry Pi, Android box): 0 đồng nếu có sẵn.

## 11. Ý tưởng mở rộng (Sau khi lõi chạy ổn)

* Bản tin buổi sáng khi bạn lại gần bàn làm việc (kích hoạt qua `HLK-LD2410C`): lịch, việc cần làm, thời tiết, tin tức.

* Telegram bot làm cổng nhập văn bản và nơi nhận thông báo từ Tèo.

* Trợ lý họp: ghi âm bằng mic laptop, phiên âm bằng Whisper, tóm tắt và trích việc cần làm.

* Đọc OCR hóa đơn/tài liệu qua camera rồi lưu vào bảng tính.

* Nối Home Assistant / Matter qua MCP.

* Biểu cảm mắt LCD theo trạng thái (đang nghe, đang nghĩ, đang đọc sách, buồn ngủ).

* Lưu sơ đồ kiến trúc, số đo độ trễ/chi phí, video demo và repo sạch để làm Portfolio AI Engineering.

## 12. Danh sách việc cần kiểm chứng (Checklist)

* \[x\] **ID model và giá hiện hành của DeepSeek:** Đã xác nhận id `deepseek-flash` (V4.1 Flash tháng 10/2026, gộp sẵn Vision); giá thấp điểm 0,15 USD/1M vào (Cache Miss), **0,003 USD/1M vào (Cache Hit)**, 0,60 USD/1M ra.

* \[x\] **Prompt mặc định của `xiaozhi-server` có phá cache không:** Có (do chèn giờ ở đầu `system_prompt`) $\rightarrow$ Khắc phục bằng **Dynamic Suffix Injection** (đẩy giờ xuống cuối tin nhắn `user`).

* \[x\] **Cơ chế gọi "Ê Tèo" rảnh tay:** Dùng **Edge Impulse** huấn luyện từ khóa `"Ê Tèo"` chạy trên ESP32-S3 + chế độ Hội thoại liên tục + phím tắt `Alt + Space` + cảm biến chạm `TTP223`.

* \[x\] **Hook tạm dừng/hạ nhỏ nhạc khi nói:** Dùng thư viện **`pycaw`** trên Windows bắt bản tin `{"type": "listen", "state": "start"}` để hạ nhạc xuống 10%.

* \[x\] **Tự chọn giọng TTS theo ngôn ngữ khi dịch thuật:** Dùng `langdetect` tự đổi mã giọng `EdgeTTS` cho từng lượt nói.

* \[x\] **Giải quyết xung đột GPIO & nguồn cho đế bánh xích WALL-E:** Dùng chung module I2C **`PCA9685`** cho cả 3 servo lẫn driver motor `DRV8833`, chọn cảm biến **`HLK-LD2410C`** (chân 2.54mm) và tách **2 mạch hạ áp MINI560 5V** từ Pin 2S.

* \[x\] **Chắt lọc kỹ thuật từ `KingKongRobotics/jumper`:** Đã tích hợp cơ chế **`AGENTS.md` + `.claude/skills`** (Mục 6.2) để tự động hóa viết tool FastMCP và cơ chế **Motion Bundle** (Mục 5.4) để chạy quỹ đạo servo/bánh xích mượt mà ngay trên ESP32-S3.

* \[ \] **Thực nghiệm Bước 0 trên HP Victus 15:** Kiểm tra `nvidia-smi` (4GB hay 6GB VRAM), test độ nhạy tiếng Việt của `Groq Whisper` / `faster-whisper` và gọi thử 20 lệnh tool tiếng Việt qua `deepseek-flash`.

* \[ \] **Kiểm tra kích thước thực tế khi mua linh kiện:** Xếp thử các mạch lên khung hộp rộng 8–10 cm và kiểm tra độ bám của kit bánh xích mini trên mặt bàn.

## Nguồn tham khảo

* Tài liệu gốc: "Kiến trúc Hệ thống Robot Agent Lai (Hybrid Edge-Cloud) trên Nền tảng ESP32-S3 và Laptop HP Victus 15"

* DeepSeek API Docs: https://api-docs.deepseek.com/quick_start/pricing và https://api-docs.deepseek.com/news/news260821

* Bài hướng dẫn DeepSeek-V4.1-Flash Vision (bên thứ ba): https://apidog.com/blog/deepseek-v4-1-flash-vision-api/

* Bảng giá DeepSeek tổng hợp: https://developer.puter.com/tutorials/deepseek-api-pricing/

* Gemini API pricing: https://ai.google.dev/gemini-api/docs/pricing

* Groq rate limits: https://console.groq.com/docs/rate-limits

* Edge Impulse Audio Classification & Keyword Spotting: https://docs.edgeimpulse.com/docs/tutorials/end-to-end-tutorials/audio-classification

* KingKongRobotics Jumper AI Toolkit (`AGENTS.md` & Motion Bundle architecture): https://github.com/KingKongRobotics/jumper

* Microsoft, Modern Standby và Wake-on-LAN: https://learn.microsoft.com/en-us/windows-hardware/drivers/network/standardized-inf-keywords-for-power-management