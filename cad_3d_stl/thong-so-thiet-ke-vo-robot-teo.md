# BẢN ĐẶC TẢ THÔNG SỐ THIẾT KẾ VỎ IN 3D ROBOT AI TRỢ LÝ "TÈO" (CAD v10)
*(Unibody Chunky Pod - Đế 3 Bánh Omni Nexus 14108 LeKiwi - Kính SLA Khói - Lắp Ráp 100% Không Hàn & Không Dán Keo Servo)*

> **Ngày cập nhật:** 07/11/2026  
> **Phiên bản:** v2.0 (CAD v10 Parametric B-Rep — Đã kiểm chứng Boolean `0.00 mm³` va chạm & Mô phỏng MuJoCo)  
> **Mã nguồn CAD gốc:** [build_teo_cad.py](file:///C:/Users/Public/Documents/AI_BAITAP/teo_sim_AI/cad_3d_stl/build_teo_cad.py) | **File STEP:** `cad_3d_stl/step/*.step` | **File STL:** `cad_3d_stl/*.stl`  
> **Tài liệu tham chiếu:** [robot-ai-agent-ke-hoach.md](file:///C:/Users/Public/Documents/AI_BAITAP/teo_sim_AI/cad_3d_stl/robot-ai-agent-ke-hoach.md) | [thong-so-kich-thuoc-linh-kien-teo.md](file:///C:/Users/Public/Documents/AI_BAITAP/teo_sim_AI/cad_3d_stl/thong-so-kich-thuoc-linh-kien-teo.md) | [teo_walle.xml](file:///C:/Users/Public/Documents/AI_BAITAP/teo_sim_AI/teo_walle.xml)

---

## 1. TRIẾT LÝ THIẾT KẾ & NÂNG CẤP CỐT LÕI TRONG CAD v10

| Hạng mục | Quy chuẩn CAD v10 | Giải thích & Lợi ích thực tế |
| :--- | :--- | :--- |
| **Kiểu dáng tổng thể** | **Unibody Chunky Pod ($116 \times 120 \times 142\text{ mm}$)** | Giữ trọn phom viên nang mập mạp bo tròn đáng yêu ($R_{\text{góc}} = 24.0\text{ mm}$, $R_{\text{vòm}} = 21.5\text{ mm}$ chuẩn hình học giải tích $C^1$ `solids=1`), bỏ khớp cổ, xoay toàn thân trên đế Omni. |
| **Đỉnh vòm đầu từ tính** | **Mũ đầu nam châm tháo nhanh (`Z = 122..142 mm`)** | Khóa bằng **4 cặp nam châm $\varnothing 6 \times 2\text{ mm}$** ở 4 góc. Vùng cảm ứng đỉnh đầu khoét mỏng chính xác **$1.0\text{ mm}$** ($\varnothing 22\text{ mm}$) kèm khung định vị cho cảm biến chạm `TTP223`. |
| **Hệ bánh Omni thực tế** | **3 Bánh `Nexus 14108` $\varnothing 48 \times 25.5\text{ mm}$ (2 hàng con lăn)** | Khớp 100% bánh đôi thực tế dày $25.5\text{ mm}$ tại bán kính tâm bánh **$R_{\text{wheel}} = 58.0\text{ mm}$** ($\pm 60^\circ$ phía trước, $180^\circ$ phía sau), kèm **Hub chuyển đổi in 3D** ăn khớp sừng chữ thập `MG90S`. |
| **Ngàm giữ 5 Servo** | **Rãnh trượt chữ T + Nẹp bắt vít đứng (`Zero-Glue`)** | Thay thế hoàn toàn bệ dán keo cũ bằng hốc chữ T khóa cứng tai servo và **5 thanh nẹp `teo_nep_giu_servo`** siết ốc `M2.5 × 8 mm` từ trên xuống — tháo lắp bảo trì trong 30 giây. |
| **Khay điện tử `Pin-Up`** | **Đặt ngửa hàng rào chân kim (`ESP32-S3` + `PCA9685`)** | Cả `ESP32-S3 DevKitC-1` và `PCA9685` đặt nằm ngang ngửa chân kim lên trên (`Z = 99..108 mm`), chừa **$34\text{ mm}$ khoảng không thông thoáng** dưới vòm đầu cho đầu cắm dây Dupont & giắc Servo JR (không bị gập cấn dây). |
| **Quản lý nguồn Không Công Tắc** | **Bỏ công tắc `KCD11` + Kẹp giắc `SM-2P` dưới mũ đầu** | Đóng kín lỗ sườn công tắc cũ; giắc pin `SM-2P` đưa lên kẹp gài nhanh ngay trên khay trên cùng — nhấc mũ đầu nam châm ra là rút/cắm ngắt nguồn vật lý an toàn tức thì. |
| **Mặt nạ & Biểu cảm AI** | **Kính cong 3D SLA + Màn `ST7789 2.0"` + `ESP32-CAM OV3660`** | Bỏ khe LED `WS2812` ở cằm (mặt cằm liền lạc mịn đẹp), thể hiện trạng thái AI qua đôi mắt hoạt hình trên LCD + cử chỉ tay/thân; rãnh trượt ngang giữ chuẩn bo `ESP32-CAM + OV3660` (sau khi tháo đế nạp USB `MB`). |

---

## 2. SƠ ĐỒ PHÂN TẦNG KHÔNG GIAN 3 TẦNG (Z = 0 → 142 mm)

```text
                       ╭───────────────────────────╮
                       │   MŨ ĐẦU NAM CHÂM (Part 5)│  Z = 142.0 mm (Vách đỉnh mỏng 1.0 mm cho TTP223)
                       │  4 cặp nam châm Ø6x2 mm   │
            ╭──────────┴───────────────────────────┴──────────╮ Z = 122.0 mm (Mặt cắt cổ nam châm)
            │  [Khoảng không cắm dây Dupont/JR cao 34 mm]     │
            │  ═══ KHAY ĐIỆN TỬ PIN-UP (Part 4, Z=99..108) ══ │ • ESP32-S3 + PCA9685 + Kẹp SM-2P + MAX98357A
            │                                                 │ • Rãnh ngang ESP32-CAM OV3660 (Tâm mắt Z=108.0)
            │  [HỘP LOA 3W KÍN KHÍ]       [MẶT KÍNH SLA CONG] │ • Màn hình LCD ST7789 2.0" (Tâm Z=75.0)
            │   Lưới 19 lỗ + Nắp gioăng    70 x 60 x 1.8 mm   │ • 2 Servo tay MG90S 180° + Nẹp vít (Trục Z=86.5)
            │   Sạc Type-C IP2326 (Z=64)                      │ • Pack Pin 2S (67x37x18.5) + 2x MINI560 + 2x CH-2
────────────┼─────────────────────────────────────────────────┼──────────── Z = 60.0 mm
════════════╪═════════════════════════════════════════════════╪════════════ Z = 58.0 mm (VÁCH NGĂN Part 2 dày 2mm)
            │                                                 │
 [BÁNH +60°]│        KHOANG GẦM MÁY LEKIWI (Part 1)           │[BÁNH -60°]
 Nexus 14108│ • 3 Servo MG90S 360° khóa rãnh T + Nẹp vít M2.5 │Nexus 14108 (Ø48 x 25.5 mm, R_wheel = 58.0 mm)
 + Hub in 3D│ • 3 Cảm biến IR chống rơi TCRT5000 (0°, ±120°)  │• Radar HLK-LD2410C (Z=33.5, vách mỏng 1.4 mm)
            │ • 2 Đế đệm chống lật đuôi kép (-42, ±36 mm)     │• Mic I2S INMP441 + hốc mút EVA (Z=49.5)
────────────┴────────────────────────┬────────────────────────┴──────────── Z = 7.0 mm (Sàn gầm chính; 2 bệ đuôi Z=5.5)
                                     │ Bánh sau 180° (Tâm trục Z = 24.0 mm)
═════════════════════════════════════╧═════════════════════════════════════ Z = 0.0 mm (Mặt bàn làm việc)
```

| Thông số hình học | Giá trị chuẩn CAD v10 | Chi tiết kỹ thuật & Khoảng hở an toàn |
| :--- | :--- | :--- |
| **Kích thước bao thân vỏ** | **$116.0 \times 120.0 \times 142.0\text{ mm}$** | Dài trước-sau `X` = $116\text{ mm}$ (`[-58, +58]`), Rộng trái-phải `Y` = $120\text{ mm}$ (`[-60, +60]`; tính cả 2 tay = $137\text{ mm}$), Cao `Z` = $142\text{ mm}$. |
| **Khoảng sáng gầm máy** | **$7.0\text{ mm}$** | Đáy vỏ chính tại `Z = 7.0 mm`; 2 bệ gá đệm nỉ chống lật đuôi tại `(-42.0, ±36.0 mm)` hạ xuống `Z = 5.5 mm` (dán nỉ PTFE chừa khe hở $0.5\text{ mm}$). |
| **Hệ bánh Omni LeKiwi** | **$R_{\text{wheel}} = 58.0\text{ mm}$, $Z_{\text{trục}} = 24.0\text{ mm}$** | Vòm chắn bùn $R_{\text{arch}} = 28.0\text{ mm}$ (khe hở hướng kính $4.0\text{ mm}$), vách hốc tại `u = 40..42 mm`; bánh `Nexus 14108` dày $25.5\text{ mm}$ nằm từ `u = 45.25..70.75 mm` (khe hở mặt trong $3.25\text{ mm}$). |
| **Trọng lượng & Trọng tâm** | **$733.1\text{ g}$ — $\text{CoM}_Z = 61.54\text{ mm}$** | $\text{CoM} = (+1.83,\ +0.11,\ 61.54)\text{ mm}$. Góc nghiêng tĩnh tới hạn: **lật trước $23.8^\circ$**, **lật hông $25.9^\circ$**, **lật ngửa được khóa cứng bởi 2 đệm đuôi**. |
| **Kiểm định giao cắt 3D** | **`0.00 mm³` trên toàn bộ 46 khối** | Kiểm tra Boolean 3D tự động giữa 19 chi tiết in + 27 khối linh kiện & đầu cắm Dupont/JR/SM-2P + quét thả khay thẳng đứng `Z = 125 → 99 mm`. |

---

## 3. DANH MỤC 11 FILE IN 3D (19 CHI TIẾT LẮP RÁP) & CẤU HÌNH ORCASLICER

Đường dẫn phần mềm OrcaSlicer:
`C:\Program Files\WindowsApps\OrcaSlicer.OrcaSlicer_2.4.3.0_x64__3qd7h69xpne0g\orca-slicer.exe`

| STT | Tên file (`.stl` / `.step`) | Số lượng in | Công nghệ & Vật liệu | Tư thế đặt bàn in & Cấu hình OrcaSlicer khuyến nghị |
| :---: | :--- | :---: | :--- | :--- |
| **1** | [`teo_than_duoi`](file:///C:/Users/Public/Documents/AI_BAITAP/teo_sim_AI/cad_3d_stl/teo_than_duoi.stl) | **1** | FDM (`PETG` / `PLA+`) | Đặt ngửa đáy xuống bàn (`Z_min` chạm bàn). Layer `0.20 mm`, **4 Walls**, Infill `25% Gyroid`, bật **Tree Support (Auto, On build plate only)** đỡ nhẹ đỉnh 3 vòm bánh xe. |
| **2** | [`teo_vach_ngan`](file:///C:/Users/Public/Documents/AI_BAITAP/teo_sim_AI/cad_3d_stl/teo_vach_ngan.stl) | **1** | FDM (`PETG` / `PLA+`) | Đặt mặt phẳng đáy xuống bàn. Layer `0.20 mm`, 3 Walls, Infill `30%`, **Không cần Support**. |
| **3** | [`teo_than_tren`](file:///C:/Users/Public/Documents/AI_BAITAP/teo_sim_AI/cad_3d_stl/teo_than_tren.stl) | **1** | FDM (`PLA+` / `PETG`) | Đặt mặt cắt eo phẳng xuống bàn. Toàn bộ gân tai nam châm, bệ khay, gá tay và bầu loa đã vát $45^\circ$; chỉ bật **Tree Support (On build plate only)** cho khung cửa sổ LCD & vòm mặt. |
| **4** | [`teo_khay_linh_kien`](file:///C:/Users/Public/Documents/AI_BAITAP/teo_sim_AI/cad_3d_stl/teo_khay_linh_kien.stl) | **1** | FDM (`PLA+` / `PETG`) | Đặt ngửa hoặc lật úp mặt sàn khay xuống bàn kèm Tree Support nhỏ cho gờ kẹp `MAX98357A`. Layer `0.20 mm`, 3 Walls, Infill `25%`. |
| **5** | [`teo_mu_dau`](file:///C:/Users/Public/Documents/AI_BAITAP/teo_sim_AI/cad_3d_stl/teo_mu_dau.stl) | **1** | FDM (`PLA+` / `PETG`) | Đặt miệng cắt cổ xuống bàn (hoặc lật đỉnh vòm kèm Variable Layer Height `0.12 mm` ở đỉnh). Vùng trung tâm đỉnh dày đúng `1.0 mm` (5 lớp `0.20 mm`) cho cảm ứng `TTP223`. |
| **6** | [`teo_kinh_sla`](file:///C:/Users/Public/Documents/AI_BAITAP/teo_sim_AI/cad_3d_stl/teo_kinh_sla.stl) | **1** | **SLA Clear Resin** *(hoặc FDM PETG trong)* | In SLA nghiêng $35^\circ$, layer `0.05 mm`, đánh nhám nước `P1000 → P3000`, phủ 1 lớp mỏng sơn bóng khói **Tamiya TS-71 Smoke Black** (che lỗ camera $\varnothing 6.5\text{ mm}$ khi xịt). |
| **7** | [`teo_nap_hop_loa`](file:///C:/Users/Public/Documents/AI_BAITAP/teo_sim_AI/cad_3d_stl/teo_nap_hop_loa.stl) | **1** | FDM (`PLA+` / `PETG`) | Đặt mặt bích phẳng (`Z = 0`) xuống bàn, **Không cần Support**. Cạnh vát phẳng chữ D xoay xuống dưới để né dây sạc `IP2326`. |
| **8** | [`teo_tay_robot`](file:///C:/Users/Public/Documents/AI_BAITAP/teo_sim_AI/cad_3d_stl/teo_tay_robot.stl) | **2** | FDM (`PLA+`) | Xoay mặt phẳng trong cánh tay (`Y = 0`) áp xuống bàn in để mặt ngoài bo tròn láng mịn. Layer `0.16 mm`, 3 Walls, Infill `20%`. |
| **9** | [`teo_nap_chup_tay`](file:///C:/Users/Public/Documents/AI_BAITAP/teo_sim_AI/cad_3d_stl/teo_nap_chup_tay.stl) | **2** | FDM (`PLA+`) | Đặt mặt mũ phẳng xuống bàn, Layer `0.12–0.16 mm`, Infill `100%`, **Không Support**. |
| **10**| [`teo_hub_banh_omni`](file:///C:/Users/Public/Documents/AI_BAITAP/teo_sim_AI/cad_3d_stl/teo_hub_banh_omni.stl) | **3** | FDM (`PETG` / `PLA+` cứng) | Đặt mặt bích rộng $\varnothing 21\text{ mm}$ xuống bàn (ống trụ $\varnothing 13.8\text{ mm}$ hướng thẳng đứng lên). Layer `0.16 mm`, **5 Walls**, Infill `50%` chịu mô-men xoắn, bật Support nhỏ trong hốc chữ thập `1.8 mm`. |
| **11**| [`teo_nep_giu_servo`](file:///C:/Users/Public/Documents/AI_BAITAP/teo_sim_AI/cad_3d_stl/teo_nep_giu_servo.stl) | **5** | FDM (`PETG` / `PLA+`) | Đặt nằm phẳng xuống bàn, Layer `0.20 mm`, **100% Infill**, **Không Support** (3 thanh cho servo bánh xe + 2 thanh cho servo cánh tay). |

---

## 4. BẢNG VẬT TƯ CƠ KHÍ & PHỤ KIỆN LẮP RÁP (BOM CƠ KHÍ CHUẨN CAD v10)

| STT | Tên vật tư cơ khí | Quy cách chuẩn | Số lượng | Vị trí lắp trên CAD v10 |
| :---: | :--- | :--- | :---: | :--- |
| **1** | Ốc lục giác chìm liên kết thân | `M2.5 × 55 mm` (Inox 304 / Thép đen) | **4 con** | Xuyên từ 4 hốc chìm đáy `teo_than_duoi`, qua `teo_vach_ngan`, vặn vào 4 trụ `teo_than_tren`. |
| **2** | Ốc siết nẹp giữ Servo + Khay + CH-2 | `M2.5 × 8 mm` (ốc tự taro hoặc ren máy) | **14 con** | `10 con` cho 5 thanh `teo_nep_giu_servo` + `2 con` giữ `teo_khay_linh_kien` + `2 con` bắt 2 kẹp `CH-2`. |
| **3** | Ốc bắt màn hình LCD ST7789 | `M2.0 × 6 mm` | **4 con** | Bắt 4 góc bo `ST7789 2.0"` vào 4 trụ mặt trong `teo_than_tren`. |
| **4** | Ốc cảm biến IR chống rơi | `M2.5 × 6 mm` *(hoặc `M3 × 6 mm`)* | **3 con** | Bắt 3 bo `TCRT5000` lên 3 cọc góc $0^\circ, \pm 120^\circ$ dưới sàn gầm. |
| **5** | Ốc giữ sừng trục Servo | `M2.0 × 5 mm` *(có sẵn trong túi MG90S)* | **5 con** | Khóa 3 hub bánh `Nexus 14108` và 2 cánh tay `teo_tay_robot` vào trục 5 servo `MG90S`. |
| **6** | Nam châm đất hiếm Neodymium | Tròn `Ø6 × 2 mm` (N35/N52) | **8 viên** | Dán keo 502/B-7000 đúng chiều cực vào 4 góc cổ `teo_than_tren` & `teo_mu_dau`. |
| **7** | Đệm nỉ chống lật đuôi | Tròn `Ø12 × 2.0 mm` (nỉ PTFE trượt êm) | **2 miếng** | Dán vào 2 hốc tròn âm dưới đáy đuôi `(-42.0, ±36.0 mm)`. |
| **8** | Mút xốp EVA đen & Keo B-7000 | EVA dày `1.0 mm` + Tuýp B-7000 `15 ml` | **1 bộ** | Đệm kín lỗ mic `INMP441`, rãnh gioăng `teo_nap_hop_loa`, và dán kính `teo_kinh_sla`. |
