# BẢNG TỔNG HỢP THÔNG SỐ KÍCH THƯỚC HÌNH HỌC LINH KIỆN ROBOT "TÈO" (CAD v10)
*(Chuẩn hóa 100% theo Linh kiện Thực tế & Bản Thiết kế Hoàn thiện [build_teo_cad.py](file:///C:/Users/Public/Documents/AI_BAITAP/teo_sim_AI/cad_3d_stl/build_teo_cad.py))*

> **Ngày cập nhật:** 07/11/2026  
> **Phiên bản:** v2.0 - Geometry Specs Master Reference (Đồng bộ 100% với **CAD v10** đã kiểm định `0.00 mm³` va chạm 3D & Mô phỏng vật lý MuJoCo)  
> **Tương thích thiết kế CAD:** Khớp tuyệt đối với [thong-so-thiet-ke-vo-robot-teo.md](file:///C:/Users/Public/Documents/AI_BAITAP/teo_sim_AI/thong-so-thiet-ke-vo-robot-teo.md) — Thân vỏ Unibody Chunky Pod **$116.0 \times 120.0 \times 142.0\text{ mm}$**, khoảng sáng gầm **$7.0\text{ mm}$**, bán kính tâm bánh **$R_{\text{wheel}} = 58.0\text{ mm}$**, 11 file in 3D (19 chi tiết).

---

## MỤC LỤC
1. [Khối Xử lý Trung tâm & Thị giác](#1-khối-xử-lý-trung-tâm--thị-giác)
2. [Khối Hiển thị, Âm thanh & Cảm biến Tương tác](#2-khối-hiển-thị-âm-thanh--cảm-biến-tương-tác)
3. [Khối Cơ cấu Chấp hành & Truyền động LeKiwi](#3-khối-cơ-cấu-chấp-hành--truyền-động-lekiwi)
4. [Khối Cảm biến An toàn Gầm máy (Chống rơi)](#4-khối-cảm-biến-an-toàn-gầm-máy-chống-rơi)
5. [Khối Nguồn điện & Mạch Sạc (Lắp ráp Không Hàn)](#5-khối-nguồn-điện--mạch-sạc-lắp-ráp-không-hàn)
6. [Khối Phụ kiện Liên kết & Cơ khí](#6-khối-phụ-kiện-liên-kết--cơ-khí)
7. [Bảng Tổng hợp BOM Hình học & Phân tích Trọng tâm CoM (CAD v10)](#7-bảng-tổng-hợp-bom-hình-học--phân-tích-trọng-tâm-com-cad-v10)

---

## 1. KHỐI XỬ LÝ TRUNG TÂM & THỊ GIÁC

### 1.1. Bo mạch vi điều khiển ESP32-S3 DevKitC-1 N16R8 (WROOM-1)
* **Phân loại sử dụng:** Bản hàn sẵn 2 hàng rào chân kim (`2 × 22 pin`, pitch `2.54 mm`).
* **Kích thước bao ngoài:**
  * Chiều dài tổng thể (tính cả ăng-ten nhô đỉnh và 2 cổng Type-C nhô đáy): **$65.00\text{ mm}$** (PCB dài $57.15\text{ mm}$).
  * Chiều rộng PCB: **$27.94\text{ mm}$** (khoảng cách 2 hàng chân `25.40 mm`).
  * Chiều cao toàn mạch: **$13.00\text{ mm}$** (linh kiện mặt USB-C $4.50\text{ mm}$ + PCB $1.60\text{ mm}$ + chân kim $8.50\text{ mm}$).
* **Bố trí trong CAD v10 (`Pin-Up` trên `teo_khay_linh_kien`):**
  * Đặt **nằm ngang, lật ngửa 44 chân kim lên trên** tại khoang sau của khay trên cùng (`X = -9.8 mm, Y = [-32.5, +32.5] mm`).
  * Hốc rãnh dưới lòng khay (`Z = 101.2..105.8 mm`) chứa lọt 2 cổng USB-C và nút nhấn RST/BOOT (đầu `+Y` khoét hở để cắm cáp nạp code trực tiếp khi cần); PCB tựa trên gờ `Z = 105.8..107.4 mm`; chân kim và vỏ nhựa đầu cắm dây Dupont (`cao 14 mm`) vươn lên đến `Z = 120.0 mm`, **cách trần vòm mũ đầu hơn $19\text{ mm}$** (hoàn toàn không chạm trần như bản v9 cũ).
* **Khối lượng:** $\sim 11.0\text{ g}$ *(cộng dây Dupont cắm đầu mạch $\approx 18\text{ g}$)*.

---

### 1.2. Cụm Module Camera ESP32-CAM + Cảm biến OV3660 (Kèm Đế Nạp ESP32-CAM-MB)
* **Phân loại thực tế của người dùng:** Combo `ESP32-CAM` tích hợp Wi-Fi + Camera `OV3660` kèm đế nạp Micro-USB `ESP32-CAM-MB`.
* **Quy tắc lắp vào robot:** Dùng đế `ESP32-CAM-MB` cắm cáp USB vào máy tính để nạp firmware lần đầu; sau khi nạp xong **rút bỏ đế `MB`**, chỉ lắp bo chính `ESP32-CAM + OV3660` vào trán robot (cấp nguồn 5V & GND qua chân kim, sau này cập nhật code qua Wi-Fi OTA).
* **Kích thước hình học (Bo `ESP32-CAM` đã tháo đế `MB`):**
  * Kích thước PCB: **$40.50 \times 27.00 \times 4.50\text{ mm}$** (tính cả khe thẻ MicroSD và linh kiện SMD; hàng chân kim 2 bên dài $8.5\text{ mm}$ quay về phía trong thân `-X`).
  * Thấu kính `OV3660`: Đế cảm biến $8.5 \times 8.5\text{ mm}$, thân ống kính $\varnothing 8.0\text{ mm}$, khẩu độ quang học $\varnothing 6.0\text{ mm}$; khi gập cáp FPC lên trên khe MicroSD, tâm thấu kính nằm cách tâm PCB **$9.5\text{ mm}$** dọc theo chiều dài bo.
* **Bố trí trong CAD v10 (`teo_than_tren` + `teo_kinh_sla`):**
  * Rãnh chữ U trượt ngang sau trán (`PCB chiếm Z = 94.5..121.5 mm`, nằm cao hơn đỉnh màn hình LCD `Z = 92.5 mm` đúng $2.0\text{ mm}$ không chạm nhau).
  * Tâm PCB lệch sang `Y = +9.5 mm` để **tâm mắt thấu kính `OV3660` nằm chính giữa trục đối xứng `Y = 0.0 mm, Z = 108.0 mm`**, nhìn thẳng qua lỗ $\varnothing 6.6\text{ mm}$ trên vỏ và lỗ vát $45^\circ$ $\varnothing 6.5\text{ mm}$ trên kính `teo_kinh_sla`.
* **Khối lượng:** $\sim 10.0\text{ g}$.

---

## 2. KHỐI HIỂN THỊ, ÂM THANH & CẢM BIẾN TƯƠNG TÁC

### 2.1. Màn hình màu LCD IPS ST7789 2.0 inch (240×320 SPI)
* **Kích thước tổng thể PCB:** **$58.00 \times 35.00 \times 4.00\text{ mm}$**; vùng hiển thị hoạt động $40.80 \times 30.60\text{ mm}$; 4 lỗ ốc M2 ở 4 góc tâm **$53.00 \times 30.00\text{ mm}$**; 8 chân cắm SPI pitch $2.54\text{ mm}$.
* **Bố trí trong CAD v10 (`teo_than_tren`):**
  * Đặt nằm ngang (`58 mm` dọc trục `Y`, `35 mm` dọc trục `Z`) tại **tâm `Z = 75.0 mm`** (`PCB chiếm Z = 57.5..92.5 mm`; vách ngăn `teo_vach_ngan` đã khoét rãnh tránh phần chân đáy LCD).
  * Cửa sổ lọt sáng $42.0 \times 32.0\text{ mm}$; bắt cứng bằng 4 ốc `M2 × 6 mm` vào 4 trụ lỗ mồi $\varnothing 1.76\text{ mm}$ (`Y = ±26.5 mm, Z = 60.0 & 90.0 mm`).
* **Khối lượng:** $\sim 16.0\text{ g}$.

---

### 2.2. Microphone kỹ thuật số I2S MEMS INMP441
* **Kích thước PCB:** **$14.00 \times 12.50 \times 3.00\text{ mm}$**; lỗ thu âm đáy $\varnothing 1.20\text{ mm}$; 6 chân cắm I2S pitch $2.54\text{ mm}$.
* **Bố trí trong CAD v10 (`teo_than_duoi`):** Khe trượt đứng sau ngực trước tại **tâm `Z = 49.5 mm`**; lỗ thu âm $\varnothing 2.0\text{ mm}$ xuyên vách kèm hốc tròn âm $\varnothing 6.4 \times 1.2\text{ mm}$ để dán vòng đệm mút EVA kín âm tuyệt đối.
* **Khối lượng:** $\sim 1.5\text{ g}$.

---

### 2.3. Mạch Khuếch đại Âm thanh I2S Class-D MAX98357A
* **Kích thước PCB:** **$19.00 \times 17.50 \times 10.00\text{ mm}$** (tính cả domino vặn dây loa); 7 chân cắm pitch $2.54\text{ mm}$.
* **Bố trí trong CAD v10 (`teo_khay_linh_kien`):** Gài vào ngàm đàn hồi treo dưới gầm khay trên tại `(X = +18.7, Y = 0.0, Z = 89.0..99.0 mm)`; hai đầu `±Y` để hở hoàn toàn cho đầu cắm Dupont và 2 dây loa đi ra tự do.
* **Khối lượng:** $\sim 3.5\text{ g}$.

---

### 2.4. Củ loa toàn dải Mini 3W ($4\Omega / 8\Omega$) & Hộp Cộng Hưởng Kín Khí
* **Kích thước củ loa:** Đường kính vành ngoài **$\varnothing 31.00\text{ mm}$**, sâu **$12.50\text{ mm}$**, nam châm $\varnothing 16.00\text{ mm}$.
* **Bố trí trong CAD v10 (`teo_than_tren` + `teo_nap_hop_loa`):**
  * Bầu loa trụ liền khối sau lưng tại **tâm `Z = 93.0 mm`** (`X = -56.5..-29.0 mm`, lòng trong $\varnothing 32.0\text{ mm}$, bậc đỡ gờ loa $\varnothing 28.0\text{ mm}$, lưới thoát âm 19 lỗ tổ ong $\varnothing 2.5\text{ mm}$).
  * Đậy kín phía sau bằng nắp rời [`teo_nap_hop_loa`](file:///C:/Users/Public/Documents/AI_BAITAP/teo_sim_AI/cad_3d_stl/teo_nap_hop_loa.stl) có rãnh chèn gioăng EVA $1.0\text{ mm}$, khe luồn dây ở đỉnh và cạnh vát chữ D chống xoay ở đáy (chừa thoáng không gian cho dây cắm sạc `IP2326` bên dưới).
* **Khối lượng:** $\sim 14.5\text{ g}$.

---

### 2.5. Cảm biến chạm điện dung TTP223
* **Kích thước PCB:** **$15.00 \times 11.00 \times 3.00\text{ mm}$**; 3 chân cắm pitch $2.54\text{ mm}$.
* **Bố trí trong CAD v10 (`teo_mu_dau`):** Cài khít vào viền định vị $15.6 \times 11.6\text{ mm}$ dưới trần vòm đầu (`Z = 138.0..141.0 mm`); trần nhựa phía trên khoét mỏng đúng **$1.00\text{ mm}$** ($\varnothing 22\text{ mm}$).
* **Khối lượng:** $\sim 1.5\text{ g}$.

---

### 2.6. Cảm biến hiện diện Radar mmWave HLK-LD2410C (24GHz)
* **Kích thước PCB:** **$22.00 \times 16.00 \times 3.00\text{ mm}$**; 5 chân kim chuẩn pitch **$2.54\text{ mm}$**.
* **Bố trí trong CAD v10 (`teo_than_duoi`):** Khe giữ đứng ẩn sau ngực trước tại **tâm `Z = 33.5 mm`** (`X = 53.5..56.6 mm`), vách nhựa phía trước hạ mỏng còn đúng **$1.40\text{ mm}$** để sóng radar 24GHz xuyên qua nhạy 100% mà mặt ngoài vỏ vẫn liền lạc không cần khoét lỗ.
* **Khối lượng:** $\sim 2.5\text{ g}$.

---

### 2.7. Vòng / Thanh LED RGB WS2812 — *ĐÃ LOẠI BỎ THEO QUYẾT ĐỊNH NGƯỜI DÙNG*
* **Trạng thái trong CAD v10:** Đã hủy bỏ hoàn toàn linh kiện LED `WS2812` và lấp phẳng khe hắt sáng ở cằm dưới kính SLA. Trạng thái AI (Nghe / Nghĩ / Nói / Ngủ) được biểu đạt trực quan qua đồ họa đôi mắt trên màn hình `ST7789 2.0"` kết hợp cử chỉ tay & xoay thân.

---

## 3. KHỐI CƠ CẤU CHẤP HÀNH & TRUYỀN ĐỘNG LEKIWI

### 3.1. Động cơ Bánh xe & Cánh tay: 5 $\times$ Micro Servo MG90S (3 con 360° + 2 con 180°)
* **Kích thước chuẩn `MG90S`:** Thân hộp $22.80 \times 12.20 \times 28.50\text{ mm}$; tổng dài tai bắt ốc $32.50\text{ mm}$ (dày tai $2.5\text{ mm}$, tâm lỗ $28.0\text{ mm}$); cổ trụ trục ra $\varnothing 11.8\text{ mm}$ + ụ bánh răng phụ $\varnothing 5.5\text{ mm}$ nhô cao $4.0\text{ mm}$, trục răng kim loại $\varnothing 4.9\text{ mm}$ lệch tâm $5.6\text{ mm}$.
* **Cơ cấu khóa cứng không keo trong CAD v10:**
  * **3 Servo bánh xe (`teo_than_duoi`):** Đặt nằm ngang hướng tâm ở góc $+60^\circ, -60^\circ, 180^\circ$ (`tâm trục Z = 24.0 mm`); tai servo lọt khít rãnh chữ T (`u = 30.8..34.0 mm`), cổ $\varnothing 11.8\text{ mm}$ + ụ phụ chui lọt lỗ định tâm qua vách hốc vòm, khóa chặt từ trên bằng 3 thanh [`teo_nep_giu_servo`](file:///C:/Users/Public/Documents/AI_BAITAP/teo_sim_AI/cad_3d_stl/teo_nep_giu_servo.stl) và 6 ốc `M2.5 × 8 mm`.
  * **2 Servo cánh tay (`teo_than_tren`):** Đặt nằm ngang ở 2 sườn (`X_trục = 0.0 mm, Z_trục = 86.5 mm`), bệ vát $45^\circ$ liền vách sườn (in không cần support), khóa bằng 2 thanh `teo_nep_giu_servo` và 4 ốc `M2.5 × 8 mm`.
* **Khối lượng:** **$13.4\text{ g} \times 5 = 67.0\text{ g}$**.

---

### 3.2. 3 $\times$ Bánh xe Đa hướng Nexus Robot `14108` 48mm Lego-Compatible Double-Row Omni
* **Phân loại thực tế của người dùng:** Bánh đa hướng 2 hàng con lăn cao su đen-xám `Nexus 14108` ($\varnothing 48\text{ mm}$).
* **Kích thước thực tế (Khác biệt hoàn toàn với bánh đơn 14mm cũ):**
  * Đường kính bao ngoài: **$\varnothing 48.00\text{ mm}$** ($R = 24.00\text{ mm}$).
  * **Bề rộng thực tế 2 hàng con lăn:** **$25.50\text{ mm}$** *(rộng gần gấp đôi thông số giả định $14\text{ mm}$ của CAD v9 cũ)*.
  * Lỗ trục tâm bánh: Lỗ trụ trơn **$\varnothing 13.90\text{ mm}$** kèm rãnh khóa ngang (dùng cho ống nối trục chữ thập Lego).
* **Bố trí trong CAD v10 (`teo_than_duoi` + `teo_hub_banh_omni`):**
  * Hốc vòm bánh xe mở rộng hoàn toàn từ `u = 42.0 mm` ra ngoài biên thân vỏ, bán kính vòm $R = 28.0\text{ mm}$ (khe hở đỉnh bánh $4.0\text{ mm}$).
  * Kết nối vào trục `MG90S` qua 3 chi tiết in [`teo_hub_banh_omni`](file:///C:/Users/Public/Documents/AI_BAITAP/teo_sim_AI/cad_3d_stl/teo_hub_banh_omni.stl) (mặt bích $\varnothing 21.0 \times 2.45\text{ mm}$ ngậm sừng chữ thập `MG90S` + ống trụ $\varnothing 13.80 \times 23.5\text{ mm}$ có 6 gân ép khít lỗ $\varnothing 13.9\text{ mm}$), đặt mặt phẳng giữa bánh xe nằm chính xác tại **$R_{\text{wheel}} = 58.00\text{ mm}$** (`u = 45.25..70.75 mm`, cách vách hốc $3.25\text{ mm}$ an toàn tuyệt đối).
* **Khối lượng:** **$39.0\text{ g} \times 3 = 117.0\text{ g}$** *(cộng 3 Hub in 3D $\approx 12.5\text{ g}$)*.

---

### 3.3. Module Điều khiển 16 Kênh PWM I2C PCA9685
* **Kích thước PCB:** **$62.50 \times 25.40 \times 12.00\text{ mm}$**; 6 chân I2C ngang ở đầu mạch + domino nguồn `V+` + 16 cụm 3 chân cắm servo JR.
* **Bố trí trong CAD v10 (`Pin-Up` trên `teo_khay_linh_kien`):** Đặt nằm phẳng ngửa chân kim lên trên tại khoang trước của khay (`X = +18.7 mm, Y = [-31.25, +31.25] mm, Z = 101.2..113.2 mm`); 2 đầu khung giữ mở thông suốt dọc `±Y` để đầu cắm I2C ngang không vướng vách nhựa, phía trên dư $> 26\text{ mm}$ cho 5 giắc cắm servo JR.
* **Khối lượng:** $\sim 11.0\text{ g}$ *(cộng 5 đầu giắc JR & dây $\approx 16\text{ g}$)*.

---

### 3.4. Cặp Đệm Chống Lật Đuôi Kép (Dual Rear Anti-Tip Pads)
* **Khắc phục lỗi CAD v9:** Vị trí cũ `(X = -45, Y = 0)` rơi thẳng vào hốc trống của bánh sau $180^\circ$.
* **Bố trí trong CAD v10 (`teo_than_duoi`):** Bổ sung **2 bệ gá tròn đối xứng** dưới sàn đuôi tại **`(X = -42.0 mm, Y = ±36.0 mm)`** (nằm hoàn toàn ngoài hốc bánh sau $180^\circ$), hạ mặt bệ xuống `Z = 5.5 mm` kèm hốc âm $\varnothing 12.0 \times 0.5\text{ mm}$ để dán 2 miếng nỉ trượt PTFE dày $2.0\text{ mm}$ (`khe hở tĩnh 0.5 mm` so với mặt bàn, chặn đứng hoàn toàn hiện tượng bốc đầu / ngửa đuôi khi lùi hoặc phanh gấp).
* **Khối lượng:** $\sim 2.0\text{ g}$ (2 miếng).

---

## 4. KHỐI CẢM BIẾN AN TOÀN GẦM MÁY (CHỐNG RƠI)

### 4.1. 3 $\times$ Cảm biến Hồng ngoại TCRT5000 (Đối xứng chuẩn $120^\circ$)
* **Kích thước PCB:** **$32.00 \times 14.00 \times 10.00\text{ mm}$**; đầu cặp LED thu/phát nhô $6.0\text{ mm}$ ($10 \times 6\text{ mm}$).
* **Bố trí trong CAD v10 (`teo_than_duoi`):** Khắc phục góc lệch bất đối xứng của bản v9 — đặt **đối xứng hoàn hảo tại $0^\circ$ (mũi trước), $+120^\circ$ (đuôi trái), $-120^\circ$ (đuôi phải)** xen kẽ chính giữa 3 bánh xe (`cọc ốc tại r = 29.0 mm`, `ô cửa sổ quang 7.2 × 11.2 mm tại r = 45.0 mm`), bảo vệ chống rơi đều 360 độ khi trượt ngang bất kỳ hướng nào.
* **Khối lượng:** **$3.5\text{ g} \times 3 = 10.5\text{ g}$**.

---

## 5. KHỐI NGUỒN ĐIỆN & MẠCH SẠC (LẮP RÁP KHÔNG HÀN)

### 5.1. Pack Pin 2S 7.4V Li-ion (2 Cell 18650 Nguyên Khối + BMS + Jack SM-2P)
* **Kích thước khối pin:** **$67.00 \times 37.00 \times 18.50\text{ mm}$**.
* **Bố trí trong CAD v10 (`teo_vach_ngan`):** Giữ nguyên pack pin nguyên khối đặt nằm ngang trên vách ngăn tại **`X = +9.5 mm` (`chiếm X = [-9.0, +28.0] mm, Y = [-33.5, +33.5] mm, Z = 60.0..78.5 mm`)** — không chạm sạc `IP2326` (`X = -54.8..-23.8`), không chạm màn hình `LCD` (`X = 48.0..52.0`), và cách đáy `MAX98357A` hơn $10\text{ mm}$. Giắc `SM-2P` kéo lên kẹp ngắt nguồn nhanh trên mặt khay trên cùng.
* **Khối lượng:** **$\sim 95.0\text{ g}$**.

### 5.2. Mạch Sạc Pin 2S Type-C IP2326
* **Kích thước PCB:** **$31.00 \times 18.00 \times 4.50\text{ mm}$**; cổng Type-C $9.5 \times 4.0\text{ mm}$.
* **Bố trí trong CAD v10 (`teo_than_tren`):** Rãnh trượt mặt lưng tại **`Z = 61.7..66.2 mm` (`tâm lỗ Type-C Z = 64.0 mm`, 2 lỗ kim LED báo sạc $\varnothing 1.5\text{ mm}$ tại `Z = 68.5 mm`)**, lùi hoàn toàn khỏi khối pin 2S phía trước (`khe hở 14.8 mm` cho đầu cắm dây Dupont thẳng).
* **Khối lượng:** $\sim 4.5\text{ g}$.

### 5.3. 2 $\times$ Mạch Hạ Áp Buck MINI560 5V (Loại Hàn Sẵn Rào Chân Kim)
* **Kích thước PCB:** **$29.00 \times 18.00 \times 5.50\text{ mm}$** *(cộng rào chân kim + đầu cắm Dupont thẳng cao tổng cộng $\approx 19\text{ mm}$)*.
* **Bố trí trong CAD v10 (`teo_vach_ngan`):** Chuyển từ khay chật trên đầu xuống **2 khay cánh bên phía trước của vách ngăn (`X = +27.0 mm, Y = ±44.8 mm, Z = 60.0..79.0 mm`)** — phía trên có tới **$39\text{ mm}$ khoảng không hoàn toàn trống** để cắm dây Dupont thẳng đứng cực kỳ thoải mái.
* **Khối lượng:** **$4.0\text{ g} \times 2 = 8.0\text{ g}$**.

### 5.4. Công tắc Nguồn KCD11 — *ĐÃ LOẠI BỎ THEO QUYẾT ĐỊNH NGƯỜI DÙNG*
* **Trạng thái trong CAD v10:** Đã bỏ công tắc vật lý và bít kín lỗ khoét sườn trái của thân dưới. Thay bằng kẹp gài nhanh giắc `SM-2P` tại `(X = +18.0, Y = +37.2 mm)` ngay dưới mũ đầu ngàm gài Snap-Fit.

### 5.5. 2 $\times$ Đầu Kẹp Nối Dây Nhanh Lò Xo CH-2
* **Kích thước:** **$19.50 \times 17.00 \times 13.00\text{ mm}$**; lỗ bắt ốc giữa $\varnothing 2.5\text{ mm}$.
* **Bố trí trong CAD v10 (`teo_vach_ngan`):** Bắt ốc `M2.5 × 8 mm` lên 2 cọc tại **`(X = -32.5 mm, Y = ±28.5 mm, Z = 64.0..77.0 mm)`** — tách hoàn toàn khỏi gân đỡ servo tay (`X = -5.6 mm`).
* **Khối lượng:** **$2.5\text{ g} \times 2 = 5.0\text{ g}$**.

---

## 6. KHỐI PHỤ KIỆN LIÊN KẾT & CƠ KHÍ

| STT | Phụ kiện | Quy cách | Số lượng | Công dụng trong CAD v10 |
| :---: | :--- | :--- | :---: | :--- |
| **1** | Ốc lục giác chìm | `M2.5 × 55 mm` | 4 | Liên kết cứng `teo_than_duoi` + `teo_vach_ngan` + `teo_than_tren`. |
| **2** | Ốc tự taro / ren máy | `M2.5 × 8 mm` | 14 | 10 ốc cho 5 nẹp `teo_nep_giu_servo` + 2 ốc khay trên + 2 ốc kẹp `CH-2`. |
| **3** | Ốc màn hình LCD | `M2.0 × 6 mm` | 4 | Cố định 4 góc màn hình `ST7789 2.0"`. |
| **4** | Ốc cảm biến IR | `M2.5 × 6 mm` | 3 | Cố định 3 mạch `TCRT5000` dưới sàn gầm. |
| **5** | Ốc khóa trục Servo | `M2.0 × 5 mm` | 5 | Siết 3 hub bánh `Nexus 14108` + 2 cánh tay vào trục `MG90S`. |
| **6** | Đệm nỉ trượt PTFE | `Ø12 × 2 mm` | 2 | Dán 2 bệ chống lật đuôi `(-42, ±36 mm)`. |

---

## 7. BẢNG TỔNG HỢP BOM HÌNH HỌC & PHÂN TÍCH TRỌNG TÂM CoM (CAD v10)

### 7.1. Bảng khối lượng & tọa độ Z thực tế (Tính chính xác từ B-Rep CAD v10)

| Nhóm thành phần | Chi tiết bao gồm | Thể tích nhựa / SL | Khối lượng (g) | Cao độ $Z$ (mm) |
| :--- | :--- | :---: | :---: | :---: |
| **1. Vỏ in 3D (19 mảnh từ 11 file)** | `teo_than_duoi` ($143.9\text{ g}$), `teo_than_tren` ($103.0\text{ g}$), `teo_mu_dau` ($46.5\text{ g}$), `teo_vach_ngan` ($29.2\text{ g}$), `teo_khay_linh_kien` ($16.3\text{ g}$), `teo_kinh_sla` ($8.5\text{ g}$), `teo_nap_hop_loa` ($4.1\text{ g}$), `2× tay + 2× nắp` ($15.2\text{ g}$), `3× hub bánh` ($12.5\text{ g}$), `5× nẹp servo` ($4.7\text{ g}$) | $309.9\text{ cm}^3$ FDM + $7.35\text{ cm}^3$ SLA | **$383.7\text{ g}$** | $5.5 \to 142.0$ |
| **2. Cụm truyền động gầm** | `3× Bánh Nexus 14108` ($117.0\text{ g}$) + `3× MG90S 360°` ($40.2\text{ g}$) + `3× TCRT5000` ($10.5\text{ g}$) + `LD2410C` + `INMP441` + `2× Đệm đuôi` | 12 cụm | **$173.7\text{ g}$** | $0.0 \to 55.0$ |
| **3. Khoang giữa & Nguồn** | `Pack Pin 2S 18650` ($95.0\text{ g}$) + `2× MG90S 180°` ($26.8\text{ g}$) + `LCD ST7789` ($16.0\text{ g}$) + `Loa 3W` ($14.5\text{ g}$) + `2× MINI560` ($8.0\text{ g}$) + `2× CH-2` ($5.0\text{ g}$) + `IP2326` ($4.5\text{ g}$) | 10 cụm | **$169.8\text{ g}$** | $57.5 \to 107.0$ |
| **4. Khay điện tử trên & Vòm đầu** | `ESP32-S3 + Dupont` + `PCA9685 + JR` + `ESP32-CAM OV3660` + `MAX98357A` + `TTP223` + ốc vít | 6 cụm | *(đã gộp chuẩn theo khối đặc)* | $89.0 \to 141.0$ |
| **TỔNG TOÀN BỘ ROBOT** | **Đầy đủ 19 chi tiết in + toàn bộ linh kiện, bánh đôi Nexus 14108, dây cắm & ốc vít** | — | **$733.1\text{ g}$** | **$\text{CoM}_Z = 61.54\text{ mm}$** |

### 7.2. Chỉ số Ổn định Tĩnh & Động lực học MuJoCo (Đã Kiểm Chứng 100%)
* **Tọa độ Trọng tâm 3D chính xác:** $\mathbf{CoM} = (+1.83,\ +0.11,\ 61.54)\text{ mm}$ — nằm gần như ngay chính giữa tâm tam giác đế LeKiwi $R_{\text{wheel}} = 58.0\text{ mm}$ (nhờ khối bánh đôi `Nexus 14108` nặng $117\text{ g}$ ở `Z = 24 mm` kéo trọng tâm xuống thấp hơn đáng kể so với bản v9 cũ dù thân cao $142\text{ mm}$).
* **Góc nghiêng lật tĩnh tới hạn:**
  * Phía trước (qua trục nối 2 bánh $\pm 60^\circ$, tay đòn $27.2\text{ mm}$): **$23.8^\circ$** (tương đương gia tốc phanh ngang $> 0.44\text{ g} \approx 4.3\text{ m/s}^2$, gấp hơn 10 lần gia tốc vận hành thực tế).
  * Hai bên hông $120^\circ$ (tay đòn $29.8\text{ mm}$): **$25.9^\circ$**.
  * Phía sau lưng: **Chống lật ngửa 100%** nhờ bánh sau tại `X = -58.0 mm` kết hợp cặp đệm chống lật kép tại `(-42.0, ±36.0 mm)`.
* **Kết quả chạy kiểm thử động lực học 15 bài test trên `MuJoCo 3.17` (`teo_walle.xml`):** Tăng tốc tối đa rồi phanh khẩn cấp, lùi gấp, trượt ngang `slide_left`, xoay tròn tại chỗ kết hợp vẫy 2 tay `happy_dance` / `moonwalk_dance` đều đạt **`max_tilt ≤ 0.71°`**, không nảy bánh, không lỗi số học `NaN/Inf`.
