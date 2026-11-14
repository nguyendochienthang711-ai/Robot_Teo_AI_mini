# DANH SÁCH LINH KIỆN PHẦN CỨNG CẦN MUA — ROBOT AI TRỢ LÝ "TÈO"
*(Chuẩn hóa 100% theo Thiết kế Cơ khí CAD v10 & Lắp ráp Cắm dây Không Cần Hàn)*

> **Dự án:** Robot AI Trợ lý Để bàn "Tèo" (ESP32-S3 + DeepSeek + Piper VITS Offline + 3 Bánh Omni LeKiwi)  
> **Phiên bản vỏ:** CAD v10 Unibody Pod ($116.0 \times 120.0 \times 142.0\text{ mm}$), khoảng sáng gầm $7.0\text{ mm}$, tâm bánh $R = 58.0\text{ mm}$.  
> **Ngày lập danh sách:** 11/11/2026.  
> **Tài liệu đối chiếu:** [thong-so-kich-thuoc-linh-kien-teo.md](file:///C:/Users/Public/Documents/AI_BAITAP/teo_sim_AI/cad_3d_stl/thong-so-kich-thuoc-linh-kien-teo.md) | [robot-ai-agent-ke-hoach.md](file:///C:/Users/Public/Documents/AI_BAITAP/teo_sim_AI/robot-ai-agent-ke-hoach.md).

---

## 📌 TÓM TẮT ĐẶC ĐIỂM HỆ THỐNG PHẦN CỨNG (CAD v10)
1. **Thiết kế thân Unibody Chunky Pod:** Bỏ khớp cổ vật lý (đỡ đứt gãy dây điện và giảm 1 servo); hướng nhìn được điều khiển linh hoạt bằng cách xoay cả thân robot qua 3 bánh xe Omni LeKiwi.
2. **Lắp ráp không dùng mỏ hàn:** Toàn bộ bo mạch mua loại **đã hàn sẵn chân kim**, liên kết bằng dây cắm Breadboard / Dupont và đầu kẹp lò xo `CH-2`.
3. **Cơ chế ngắt nguồn nhanh:** Bỏ công tắc bập bành `KCD11`; ngắt nguồn bằng cách rút giắc `SM-2P` đặt ngay dưới nắp mũ đầu ngàm gài nhanh (Snap-Fit).
4. **Biểu đạt trạng thái AI:** Bỏ vòng LED `WS2812`; trạng thái (Nghe, Nghĩ, Nói, Ngủ, Báo động) hiển thị qua đồ họa đôi mắt hoạt hình trên màn hình `ST7789 2.0 inch` và micro-posture của 2 cánh tay.
5. **Nguồn điện cách ly chống nhiễu:** Dùng 2 mạch hạ áp `MINI560 5V` độc lập từ pack pin 2S (1 mạch nuôi vi điều khiển/mic/màn hình, 1 mạch nuôi riêng 5 servo).

---

## 🛒 CHI TIẾT DANH MỤC LINH KIỆN CẦN MUA THEO NHÓM

### 1. Khối Xử lý Trung tâm, Thị giác & Mạng
| STT | Tên linh kiện | Model / Phân loại chính xác khi đặt mua | SL cần | SL nên mua | Lưu ý quan trọng khi chọn mua |
| :---: | :--- | :--- | :---: | :---: | :--- |
| **1** | **Bo mạch vi điều khiển trung tâm** | **ESP32-S3 DevKitC-1 N16R8** *(WROOM-1)* | **1** | 1 | • Chọn bản **"Đã hàn sẵn rào chân kim"** (`2 × 22 pin`, pitch `2.54mm`).<br>• Đúng mã **`N16R8`** (16MB Flash + 8MB Octal PSRAM) để nạp TinyML Wake Word *"Ê Tèo"* và đệm âm thanh mượt mà. |
| **2** | **Cụm Camera thị giác** | **Module ESP32-CAM + Cảm biến OV3660** | **1** | 1 | • Chọn phân loại **"Came + Chân Đế"** (có kèm đế nạp `ESP32-CAM-MB`).<br>• Dùng đế nạp firmware lần đầu qua cổng Micro-USB, sau khi nạp xong **rút bỏ đế** chỉ lắp bo chính vào trán robot. |

---

### 2. Khối Hiển thị, Âm thanh & Cảm biến Tương tác
| STT | Tên linh kiện | Model / Phân loại chính xác khi đặt mua | SL cần | SL nên mua | Lưu ý quan trọng khi chọn mua |
| :---: | :--- | :--- | :---: | :---: | :--- |
| **3** | **Màn hình hiển thị mắt AI** | **LCD IPS ST7789 2.0 inch** *(240×320 SPI)* | **1** | 1 | • Giao tiếp SPI 8 chân kim thẳng (pitch `2.54mm`), 4 lỗ ốc góc `M2`.<br>• Hiển thị đôi mắt biểu cảm WALL-E thay thế hoàn toàn vòng LED. |
| **4** | **Microphone thu âm** | **INMP441 I2S MEMS Digital Microphone** | **1** | **2** | • Mua dư 1 cái dự phòng (giá rẻ ~25k).<br>• Chọn loại **đã hàn sẵn chân kim thẳng**. |
| **5** | **Mạch khuếch đại âm thanh** | **MAX98357A I2S Class-D Mono 3W** | **1** | 1 | • Có sẵn domino vặn 2 dây loa và hàng chân cắm tín hiệu pitch `2.54mm`. |
| **6** | **Củ loa toàn dải Mini** | **Loa Mini 3W ($4\Omega$ hoặc $8\Omega$) $\varnothing 31\text{mm}$** | **1** | 1 | • Đường kính vành ngoài đúng **$31\text{mm}$**, độ dày $\le 12.5\text{mm}$.<br>• Lắp khít buồng âm kín khí `teo_than_tren` + `teo_nap_hop_loa`. |
| **7** | **Cảm biến chạm đỉnh đầu** | **Module chạm điện dung TTP223** | **1** | **2** | • Kích thước nhỏ gọn $15 \times 11\text{mm}$.<br>• Dán ẩn dưới nắp mũ đầu để chạm ngắt lời (`barge-in`) hoặc xác nhận HITL. |
| **8** | **Cảm biến hiện diện người** | **Radar mmWave HLK-LD2410C (24GHz)** | **1** | 1 | ⚠️ **Bắt buộc:** Chọn đúng bản **LD2410C** chân kim chuẩn **2.54mm** cắm vừa dây Dupont (tránh mua bản LD2410B chân nhỏ 1.27mm khó cắm). |

---

### 3. Khối Cơ cấu Chấp hành & Bánh xe Đa hướng LeKiwi
| STT | Tên linh kiện | Model / Phân loại chính xác khi đặt mua | SL cần | SL nên mua | Lưu ý quan trọng khi chọn mua |
| :---: | :--- | :--- | :---: | :---: | :--- |
| **9** | **Bánh xe đa hướng Omni** | **Nexus Robot 14108 $\varnothing 48\text{mm}$** *(Lego-Compatible)* | **3** | **3** | • Đúng chuẩn: 2 hàng con lăn cao su đen-xám, bề rộng bánh **$25.5\text{mm}$**, lỗ trục $\varnothing 13.9\text{mm}$.<br>• Lắp ăn khớp với 3 chi tiết in 3D `teo_hub_banh_omni`. |
| **10** | **Động cơ 3 bánh xe Omni** | **Micro Servo MG90S loại quay liên tục 360 độ** | **3** | **3** | ⚠️ **Phải là loại 360° Continuous Rotation** (bánh răng kim loại), có sẵn chiết áp canh điểm dừng. |
| **11** | **Động cơ 2 cánh tay** | **Micro Servo MG90S loại quay góc 180 độ** | **2** | **2** | • Loại 180° tiêu chuẩn (bánh răng kim loại). Đi kèm sừng servo chữ thập để bắt khớp vai. |
| **12** | **Mạch điều khiển xung Servo** | **Module PCA9685 (16 kênh PWM I2C)** | **1** | 1 | • Điều khiển chung 5 servo qua 2 chân I2C của ESP32. Có domino cấp nguồn `V+` riêng cho servo. |

---

### 4. Khối Nguồn điện, Mạch Sạc & Hạ Áp Độc Lập
| STT | Tên linh kiện | Model / Phân loại chính xác khi đặt mua | SL cần | SL nên mua | Lưu ý quan trọng khi chọn mua |
| :---: | :--- | :--- | :---: | :---: | :--- |
| **13** | **Pin nguồn chính** | **Pack Pin 2S 7.4V Li-ion (2 cell 18650 đóng sẵn BMS)** | **1** | 1 | • Pack 2 cell 18650 nối tiếp nằm phẳng ($67 \times 37 \times 18.5\text{mm}$) tích hợp sẵn mạch BMS bảo vệ và dây ra giắc **SM-2P**.<br>• Dung lượng khuyến nghị: $2000 - 3000\text{ mAh}$. |
| **14** | **Mạch sạc pin Type-C** | **Mạch sạc 2S Li-ion IP2326 Type-C** | **1** | 1 | • Cổng Type-C cắm sạc qua khe hở sau lưng robot.<br>• Tự ngắt khi pin đầy 8.4V. |
| **15** | **Mạch hạ áp cách ly** | **Mạch Buck MINI560 (Nguồn ra cố định 5V)** | **2** | **2** | • Chọn phân loại **"Đã hàn sẵn rào chân kim"**.<br>• 1 mạch cấp nguồn 5V "Sạch" cho ESP32/Loa/Mic/LCD; 1 mạch cấp nguồn 5V "Cơ bắp" cho 5 Servo. |
| **16** | **Khối kẹp nối dây nhanh** | **Đầu kẹp nối dây lò xo CH-2** | **2** | **4** | • Kẹp chia cực Dương (+) và Âm (-) từ pin ra 2 mạch MINI560 không cần chấm mối hàn. |

---

### 5. Khối Cảm biến Gầm Chống Rơi Mép Bàn
| STT | Tên linh kiện | Model / Phân loại chính xác khi đặt mua | SL cần | SL nên mua | Lưu ý quan trọng khi chọn mua |
| :---: | :--- | :--- | :---: | :---: | :--- |
| **17** | **Cảm biến chống rơi mép bàn** | **Cảm biến hồng ngoại dò line / tránh vật cản TCRT5000** | **3** | **4** | • Mạch có sẵn biến trở xoay chỉnh cự ly phát hiện mép bàn.<br>• Bố trí đối xứng 3 góc lệch nhau $120^\circ$ dưới gầm robot. |

---

### 6. Khối Phụ kiện Cơ khí & Ốc vít
| STT | Tên phụ kiện | Quy cách / Kích thước tiêu chuẩn | SL cần | SL nên mua | Vị trí lắp đặt trong vỏ CAD v10 |
| :---: | :--- | :--- | :---: | :---: | :--- |
| **18** | **Bu lông lục giác chìm dài** | **`M2.5 × 55mm`** (kèm long đen) | 4 con | 1 túi (5-10 con) | Xuyên dọc từ gầm dưới qua vách ngăn lên siết cứng thân trên. |
| **19** | **Ốc vít tự taro / ren nhựa** | **`M2.5 × 8mm`** | 14 con | 1 túi (20 con) | Bắt 5 nẹp giữ servo (10 ốc) + bắt khay trên (2 ốc) + bắt 2 kẹp CH-2 (2 ốc). |
| **20** | **Ốc bắt màn hình LCD** | **`M2.0 × 6mm`** | 4 con | 1 túi (10 con) | Cố định 4 góc mạch LCD ST7789 vào mặt sau trán. |
| **21** | **Ốc bắt cảm biến TCRT5000** | **`M2.5 × 6mm`** (hoặc M3 ngắn) | 3 con | 1 túi (10 con) | Bắt 3 mạch TCRT5000 vào các trụ gá dưới đáy gầm. |
| **22** | **Ốc bắt sừng servo / Hub** | **`M2.0 × 5mm`** | 5 con | Đi kèm hộp MG90S | Siết 3 hub bánh Omni và 2 cánh tay vào trục răng servo. |
| **23** | **Đệm nỉ trượt / Chân PTFE** | **Miếng đệm nỉ tròn $\varnothing 12\text{mm} \times 2\text{mm}$** | **2 miếng** | 1 vỉ | Dán vào 2 bệ tròn dưới đuôi gầm robot để chống lật ngửa khi lùi phanh gấp. |
| **24** | **Đệm mút xốp kín âm mic** | **Băng keo mút xốp EVA dày 1-2mm** | 1 mẩu nhỏ | 1 cuộn | Khoét vòng đệm dán quanh đầu mic INMP441 ép sát vách ngực để triệt tiêu tiếng vang. |

---

### 7. Dây Cắm & Vật tư Phụ Đấu Nối
| STT | Tên phụ kiện | Quy cách | Số lượng khuyến nghị | Ghi chú ứng dụng |
| :---: | :--- | :--- | :---: | :--- |
| **25** | **Dây cắm Dupont** | Loại dài **10cm** và **20cm** | **1 vỉ Đực-Cái (40 sợi) + 1 vỉ Cái-Cái (40 sợi)** | Cắm kết nối toàn bộ module lên khay trên và vách ngăn mà không cần hàn. |
| **26** | **Dây nối giắc SM-2P** | 1 cặp giắc Đực - Cái SM-2P có sẵn dây | 1 - 2 cặp | Làm đầu nối nguồn ngắt nhanh giữa pack pin và kẹp CH-2. |
| **27** | **Bảng cắm Breadboard test** | **Breadboard MB-102 (830 lỗ)** | 1 cái | Dùng để cắm thử nghiệm mạch ngoài trước khi đóng thùng vào robot. |

---

## 🚫 DANH SÁCH LINH KIỆN ĐÃ LOẠI BỎ (KHÔNG MUA LÃNG PHÍ)
* ❌ **Không mua Công tắc gạt KCD11:** Đã bỏ công tắc vật lý; robot ngắt nguồn bằng cách rút giắc `SM-2P` ngay dưới mũ đầu ngàm gài nhanh (Snap-Fit).
* ❌ **Không mua Nam châm Neodymium $\varnothing 6 \times 2\text{mm}$:** Đã loại bỏ 8 viên nam châm và keo dán ở mũ đầu; thay bằng **ngàm gài đàn hồi ẩn 4 điểm (Snap-Fit Clips)** tích hợp sẵn trong bản in `teo_mu_dau` + **rãnh mở nhanh phía sau**.
* ❌ **Không mua Vòng / Thanh LED WS2812:** Đã bỏ để bề mặt robot liền lạc, thẩm mỹ cao; trạng thái AI do màn hình LCD `ST7789` đảm nhiệm.
* ❌ **Không mua Servo khớp cổ:** Thân trên liền khối Unibody; góc nhìn được điều khiển tự nhiên bằng cách xoay cả thân robot qua 3 bánh Omni LeKiwi.
* ❌ **Không mua Mạch cầu H DRV8833 / TB6612:** 3 bánh xe dùng Servo `MG90S 360°` cắm thẳng vào `PCA9685`, không cần mạch công suất cầu H.
* ❌ **Không mua Raspberry Pi 5:** Toàn bộ tác vụ AI nặng đã do Laptop HP Victus 15 gánh qua mạng Wi-Fi LAN nội bộ.

---

## 💰 ƯỚC TÍNH TỔNG NGÂN SÁCH MUA SẮM
* **Khối điện tử, vi điều khiển & cảm biến:** $\sim 650.000 - 800.000\text{ VNĐ}$
* **Khối động cơ 5 Servo MG90S & 3 bánh Omni Nexus 14108:** $\sim 700.000 - 750.000\text{ VNĐ}$ *(riêng 3 bánh Omni $\approx 600.000\text{ VNĐ}$)*
* **Khối nguồn pin 2S, sạc Type-C, hạ áp & phụ kiện ốc vít:** $\sim 200.000 - 250.000\text{ VNĐ}$
* **Tổng chi phí phần cứng trọn gói:** **$\approx 1.550.000 - 1.800.000\text{ VNĐ}$**.
