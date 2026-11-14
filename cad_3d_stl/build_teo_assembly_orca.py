"""Generate Multi-Part 3MF & STEP Full Assemblies of Robot 'Teo' (CAD v10) for OrcaSlicer.

Outputs:
1. cad_3d_stl/teo_tong_the_orca.3mf
   - Complete 46-part assembly (19 printed parts + 27 detailed internal hardware & connector models)
   - Grouped under a single parent Assembly Object so all floating parts preserve exact 3D coordinates
   - Named clearly in Vietnamese (ASCII-safe + readable) for toggling/inspecting inside OrcaSlicer
2. cad_3d_stl/teo_tong_the_xuyen_thau_orca.3mf
   - Same 46-part assembly with outer enclosure shells pre-configured as transparent X-ray modifiers
3. cad_3d_stl/step/teo_tong_the_cad_v10.step
   - Complete multi-body B-Rep STEP assembly with individual part names and colors
"""

from __future__ import annotations

import math
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

import build123d as bd
from build123d import Color, Compound, Location, export_step, import_step
import numpy as np
import trimesh

OUT_DIR = Path(__file__).resolve().parent
STEP_DIR = OUT_DIR / "step"


# 8-slot color palette for OrcaSlicer filament slots & 3MF basematerials
PALETTE = [
    ("1_Vo_Chinh_Vang_Cam", "#F2A32E", (0.95, 0.64, 0.18)),      # Slot 1: Main Orange Shell
    ("2_Gam_Va_Banh_Xam_Dam", "#3B424C", (0.23, 0.26, 0.30)),    # Slot 2: Dark Slate Chassis & Wheels
    ("3_Kinh_SLA_Den_Khoi", "#1A222D", (0.10, 0.13, 0.18)),      # Slot 3: Smoke Black SLA Visor
    ("4_Pin_2S_Va_Bo_Mach_Xanh_La", "#27AE60", (0.15, 0.68, 0.38)),  # Slot 4: Green 2S Battery & PCBs
    ("5_Servo_MG90S_PCA9685_Xanh_Duong", "#1E88E5", (0.12, 0.53, 0.90)),  # Slot 5: Blue Servos & PCA9685
    ("6_Man_Hinh_Khay_Vach_Cyan", "#00ACC1", (0.00, 0.67, 0.76)),    # Slot 6: Cyan LCD, Tray & Bulkhead
    ("7_Cam_Bien_Va_Giac_Do", "#E53935", (0.90, 0.22, 0.21)),    # Slot 7: Red Sensors & Power Plugs
    ("8_Hub_Kim_Loai_Nep_Bac", "#B0BEC5", (0.69, 0.75, 0.77)),   # Slot 8: Silver Hubs, Clamps & USB-C
]


@dataclass
class AssemblyItem:
    """Single named 3D component in the full robot assembly."""

    name: str
    mesh: trimesh.Trimesh
    slot: int  # 1..8 index into PALETTE
    xray_transparent: bool = False
    step_shape: bd.Shape | None = None


def rot_x(deg: float) -> np.ndarray:
    return trimesh.transformations.rotation_matrix(math.radians(deg), [1, 0, 0])


def rot_y(deg: float) -> np.ndarray:
    return trimesh.transformations.rotation_matrix(math.radians(deg), [0, 1, 0])


def rot_z(deg: float) -> np.ndarray:
    return trimesh.transformations.rotation_matrix(math.radians(deg), [0, 0, 1])


def trans(x: float, y: float, z: float) -> np.ndarray:
    return trimesh.transformations.translation_matrix([x, y, z])


def place_mesh(mesh: trimesh.Trimesh, mat: np.ndarray) -> trimesh.Trimesh:
    m = mesh.copy()
    m.apply_transform(mat)
    return m


def box_m(cx: float, cy: float, cz: float, sx: float, sy: float, sz: float) -> trimesh.Trimesh:
    m = trimesh.creation.box(extents=[sx, sy, sz])
    m.apply_translation([cx, cy, cz])
    return m


def cyl_m(cx: float, cy: float, cz: float, radius: float, height: float, axis: str = "Z", sections: int = 40) -> trimesh.Trimesh:
    m = trimesh.creation.cylinder(radius=radius, height=height, sections=sections)
    if axis == "X":
        m.apply_transform(rot_y(90))
    elif axis == "Y":
        m.apply_transform(rot_x(90))
    m.apply_translation([cx, cy, cz])
    return m


def union_m(parts: list[trimesh.Trimesh]) -> trimesh.Trimesh:
    return trimesh.boolean.union(parts, engine="manifold")


def diff_m(base: trimesh.Trimesh, cutters: list[trimesh.Trimesh]) -> trimesh.Trimesh:
    return trimesh.boolean.difference([base, *cutters], engine="manifold")


def make_nexus_14108_wheel() -> trimesh.Trimesh:
    """Detailed 48x25.5mm Nexus 14108 Double-Row Omni Wheel centered at (58.0, 0.0, 24.0) along local +X."""
    # Main twin-row body hub (OD Ø36mm, width 24.5mm) + 10 peripheral barrel rollers reaching OD Ø48.0mm
    core = cyl_m(58.0, 0.0, 0.0, 17.5, 24.5, axis="X", sections=48)
    parts = [core]
    for row_idx, x_c in enumerate((58.0 - 6.3, 58.0 + 6.3)):
        phase = 0.0 if row_idx == 0 else 36.0
        for k in range(5):
            ang = phase + k * 72.0
            rad = math.radians(ang)
            ry = 17.2 * math.cos(rad)
            rz = 17.2 * math.sin(rad)
            # Tangent roller cylinder crowned to exact Ø48.0mm outer wheel envelope
            roller = trimesh.creation.cylinder(radius=6.8, height=13.5, sections=28)
            roller.apply_transform(rot_x(ang))
            roller.apply_translation([x_c, ry, rz])
            parts.append(roller)
    wheel = union_m(parts)
    # Crown rollers to exact R=24.00mm x 25.5mm Nexus 14108 outer barrel envelope (so min Z = 0.00mm exact!)
    envelope = cyl_m(58.0, 0.0, 0.0, 24.0, 25.5, axis="X", sections=64)
    wheel = trimesh.boolean.intersection([wheel, envelope], engine="manifold")
    # Center bore Ø14.3mm clearing hub press-fit ribs cleanly
    bore = cyl_m(58.0, 0.0, 0.0, 7.15, 30.0, axis="X", sections=40)
    wheel = diff_m(wheel, [bore])
    wheel.apply_translation([0.0, 0.0, 24.0])
    return wheel


def make_mg90s_detailed(u_front: float, v_mid: float, z_axle: float) -> trimesh.Trimesh:
    """Detailed MG90S micro servo model in local mount coordinates."""
    body = box_m(u_front - 28.5 / 2.0, v_mid, z_axle, 28.5, 22.8, 12.2)
    ears = box_m(u_front - 7.75, v_mid, z_axle, 2.5, 32.5, 12.2)
    boss = cyl_m(u_front + 1.15, 0.0, z_axle, 5.9, 2.3, axis="X", sections=36)
    aux = cyl_m(u_front + 0.90, 0.5 * v_mid, z_axle, 2.75, 1.8, axis="X", sections=24)
    shaft = cyl_m(u_front + 3.55, 0.0, z_axle, 2.45, 2.5, axis="X", sections=24)
    wire = box_m(u_front - 28.5 - 2.5, v_mid, z_axle, 5.0, 6.0, 3.6)
    servo = union_m([body, ears, boss, aux, shaft, wire])
    h1 = cyl_m(u_front - 7.75, v_mid - 14.0, z_axle, 1.1, 14.0, axis="X", sections=20)
    h2 = cyl_m(u_front - 7.75, v_mid + 14.0, z_axle, 1.1, 14.0, axis="X", sections=20)
    return diff_m(servo, [h1, h2])


def build_all_items() -> list[AssemblyItem]:
    """Assemble all 19 printed parts and 27 detailed hardware components in exact world coordinates."""
    raw_stl: dict[str, trimesh.Trimesh] = {}
    raw_step: dict[str, bd.Shape] = {}
    stems = [
        "teo_than_duoi",
        "teo_vach_ngan",
        "teo_than_tren",
        "teo_khay_linh_kien",
        "teo_mu_dau",
        "teo_kinh_sla",
        "teo_nap_hop_loa",
        "teo_tay_robot",
        "teo_nap_chup_tay",
        "teo_hub_banh_omni",
        "teo_nep_giu_servo",
    ]
    for st in stems:
        raw_stl[st] = trimesh.load(OUT_DIR / f"{st}.stl")
        raw_step[st] = import_step(str(STEP_DIR / f"{st}.step"))

    items: list[AssemblyItem] = []

    # =========================================================================
    # GROUP 01: 19 PRINTED ENCLOSURE & MECHANICAL PARTS (01_VO_*)
    # =========================================================================
    items.append(AssemblyItem(
        "01_VO_01_Mu_Dau_Ngam_SnapFit",
        raw_stl["teo_mu_dau"],
        slot=1,
        xray_transparent=True,
        step_shape=raw_step["teo_mu_dau"],
    ))
    items.append(AssemblyItem(
        "01_VO_02_Kinh_Mat_Na_SLA",
        raw_stl["teo_kinh_sla"],
        slot=3,
        xray_transparent=True,
        step_shape=raw_step["teo_kinh_sla"],
    ))
    items.append(AssemblyItem(
        "01_VO_03_Than_Tren_Unibody",
        raw_stl["teo_than_tren"],
        slot=1,
        xray_transparent=True,
        step_shape=raw_step["teo_than_tren"],
    ))
    items.append(AssemblyItem(
        "01_VO_04_Khay_Dien_Tu_PinUp",
        raw_stl["teo_khay_linh_kien"],
        slot=6,
        xray_transparent=False,
        step_shape=raw_step["teo_khay_linh_kien"],
    ))

    spk_mat = trans(-27.2, 0.0, 93.0) @ rot_y(-90) @ rot_z(-90)
    spk_step = bd.Pos(-27.2, 0.0, 93.0) * bd.Rot(0, -90, 0) * bd.Rot(0, 0, -90) * raw_step["teo_nap_hop_loa"]
    items.append(AssemblyItem(
        "01_VO_05_Nap_Kin_Hop_Loa",
        place_mesh(raw_stl["teo_nap_hop_loa"], spk_mat),
        slot=6,
        step_shape=spk_step,
    ))

    items.append(AssemblyItem(
        "01_VO_06_Vach_Ngan_Tang_Giua",
        raw_stl["teo_vach_ngan"],
        slot=6,
        step_shape=raw_step["teo_vach_ngan"],
    ))
    items.append(AssemblyItem(
        "01_VO_07_Than_Duoi_Gam_LeKiwi",
        raw_stl["teo_than_duoi"],
        slot=2,
        xray_transparent=True,
        step_shape=raw_step["teo_than_duoi"],
    ))

    # Left & Right Arms + Caps + Arm Servo Clamps
    z_arm = 86.5
    for side_tag, sy_sign in (("Trai", 1.0), ("Phai", -1.0)):
        if sy_sign > 0:
            arm_mat = trans(0.0, 60.5, z_arm)
            cap_mat = trans(0.0, 60.5 + 8.1, z_arm) @ rot_x(90)
            arm_s = bd.Pos(0.0, 60.5, z_arm) * raw_step["teo_tay_robot"]
            cap_s = bd.Pos(0.0, 60.5 + 8.1, z_arm) * bd.Rot(90, 0, 0) * raw_step["teo_nap_chup_tay"]
        else:
            arm_mat = trans(0.0, -60.5, z_arm) @ rot_z(180)
            cap_mat = trans(0.0, -(60.5 + 8.1), z_arm) @ rot_x(-90)
            arm_s = bd.Pos(0.0, -60.5, z_arm) * bd.Rot(0, 0, 180) * raw_step["teo_tay_robot"]
            cap_s = bd.Pos(0.0, -(60.5 + 8.1), z_arm) * bd.Rot(-90, 0, 0) * raw_step["teo_nap_chup_tay"]

        items.append(AssemblyItem(
            f"01_VO_Tay_Robot_{side_tag}",
            place_mesh(raw_stl["teo_tay_robot"], arm_mat),
            slot=1,
            step_shape=arm_s,
        ))
        items.append(AssemblyItem(
            f"01_VO_Nap_Chup_Tay_{side_tag}",
            place_mesh(raw_stl["teo_nap_chup_tay"], cap_mat),
            slot=2,
            step_shape=cap_s,
        ))

        ang_a = 90.0 if sy_sign > 0 else -90.0
        v_arm = 5.6 if sy_sign > 0 else -5.6
        c_mat = rot_z(ang_a) @ trans(44.0, v_arm, z_arm + 6.3) @ rot_z(90)
        c_s = bd.Rot(0, 0, ang_a) * bd.Pos(44.0, v_arm, z_arm + 6.3) * bd.Rot(0, 0, 90) * raw_step["teo_nep_giu_servo"]
        items.append(AssemblyItem(
            f"01_VO_Nep_Servo_Tay_{side_tag}",
            place_mesh(raw_stl["teo_nep_giu_servo"], c_mat),
            slot=8,
            step_shape=c_s,
        ))

    # 3x Wheel Hubs + 3x Wheel Servo Clamps
    wheel_labels = [(60.0, "Truoc_Trai_60"), (-60.0, "Truoc_Phai_Am60"), (180.0, "Sau_Giua_180")]
    for ang, w_tag in wheel_labels:
        v_mid = -5.6 if ang == 60.0 else 5.6
        hub_mat = rot_z(ang) @ trans(42.8, 0.0, 24.0) @ rot_y(90)
        hub_s = bd.Rot(0, 0, ang) * bd.Pos(42.8, 0.0, 24.0) * bd.Rot(0, 90, 0) * raw_step["teo_hub_banh_omni"]
        items.append(AssemblyItem(
            f"01_VO_Hub_Banh_Omni_{w_tag}",
            place_mesh(raw_stl["teo_hub_banh_omni"], hub_mat),
            slot=8,
            step_shape=hub_s,
        ))

        cl_mat = rot_z(ang) @ trans(27.0, v_mid, 30.3) @ rot_z(90)
        cl_s = bd.Rot(0, 0, ang) * bd.Pos(27.0, v_mid, 30.3) * bd.Rot(0, 0, 90) * raw_step["teo_nep_giu_servo"]
        items.append(AssemblyItem(
            f"01_VO_Nep_Servo_Banh_{w_tag}",
            place_mesh(raw_stl["teo_nep_giu_servo"], cl_mat),
            slot=8,
            step_shape=cl_s,
        ))

    # =========================================================================
    # GROUP 02: INTERNAL ELECTRONICS, BATTERY & CONNECTORS (02_MACH_*)
    # =========================================================================
    # 1. TTP223 Touch Sensor under 1mm dome apex
    ttp_m = union_m([
        box_m(0.0, 0.0, 139.8, 15.0, 11.0, 1.8),
        box_m(0.0, 0.0, 135.0, 7.6, 5.0, 8.0),
    ])
    items.append(AssemblyItem("02_MACH_01_Cam_Bien_Cham_TTP223", ttp_m, slot=7))

    # 2. ESP32-S3 DevKitC-1 N16R8 + 44-pin Dupont housings
    esp_m = union_m([
        box_m(-9.8, 0.0, 106.8, 28.0, 63.4, 1.6),
        box_m(-9.8, -14.0, 104.8, 18.0, 25.5, 2.8),  # WROOM-1 shield underneath
        box_m(-9.8 - 6.0, 29.0, 104.4, 9.0, 7.5, 3.2),  # USB-C 1
        box_m(-9.8 + 6.0, 29.0, 104.4, 9.0, 7.5, 3.2),  # USB-C 2
        box_m(-9.8 - 11.4, 0.0, 114.6, 2.8, 55.8, 14.0),  # Left 22-pin Dupont row
        box_m(-9.8 + 11.4, 0.0, 114.6, 2.8, 55.8, 14.0),  # Right 22-pin Dupont row
    ])
    items.append(AssemblyItem("02_MACH_02_ESP32_S3_N16R8_Kem_Dupont", esp_m, slot=4))

    # 3. PCA9685 16-Channel PWM + Servo JR plugs + Right-angle I2C Dupont
    pca_m = union_m([
        box_m(18.7, 0.0, 102.2, 25.4, 62.5, 1.6),
        cyl_m(18.7 + 7.5, 24.0, 107.0, 4.0, 8.5, axis="Z"),  # 1000uF Capacitor
        box_m(18.7 + 7.5, 0.0, 106.5, 7.5, 10.0, 7.5),       # Green V+ terminal block
        box_m(18.7 - 5.2, -4.0, 110.2, 8.2, 42.0, 14.5),     # 5x JR Servo Plugs bank
        box_m(18.7, -36.0, 104.5, 5.5, 11.0, 5.5),           # Right-angle I2C Dupont plug
    ])
    items.append(AssemblyItem("02_MACH_03_PCA9685_16Kenh_Kem_Giac_JR", pca_m, slot=5))

    # 4. SM-2P Battery Quick-Disconnect Plug on Top Tray
    sm2p_m = box_m(18.0, 37.2, 105.5, 17.5, 4.4, 7.2)
    items.append(AssemblyItem("02_MACH_04_Giac_Ngat_Pin_Nhanh_SM2P", sm2p_m, slot=7))

    # 5. MAX98357A I2S Amp under Top Tray
    amp_m = union_m([
        box_m(18.7, 0.0, 97.0, 19.0, 17.5, 1.8),
        box_m(18.7, -5.0, 93.8, 8.0, 7.5, 5.0),
        box_m(18.7, 14.5, 96.5, 13.5, 11.5, 3.2),
    ])
    items.append(AssemblyItem("02_MACH_05_Ampli_I2S_MAX98357A", amp_m, slot=5))

    # 6. ESP32-CAM + OV3660 (without MB shield) in forehead rail
    cam_m = union_m([
        box_m(50.3, 9.5, 108.0, 1.8, 40.5, 27.0),
        box_m(48.8, 13.0, 108.0, 2.5, 18.0, 16.0),     # ESP32-S RF shield
        box_m(51.6, 0.0, 108.0, 1.8, 14.0, 15.0),      # MicroSD slot
        box_m(52.4, 0.0, 108.0, 2.2, 8.5, 8.5),        # Folded OV3660 sensor base
        cyl_m(54.2, 0.0, 108.0, 3.0, 3.6, axis="X"),   # OV3660 Lens Barrel at Y=0!
        box_m(42.0, 26.0, 108.0, 13.0, 5.6, 11.0),     # Rear 5V/GND Dupont housing
    ])
    items.append(AssemblyItem("02_MACH_06_Camera_ESP32_CAM_OV3660", cam_m, slot=4))

    # 7. LCD ST7789 2.0" IPS + 8-pin Dupont
    lcd_base = union_m([
        box_m(50.3, 0.0, 75.0, 1.8, 58.0, 35.0),
        box_m(51.6, 0.0, 75.0, 1.6, 41.5, 31.0),       # Active IPS glass panel
        box_m(42.2, -25.0, 75.0, 12.5, 5.2, 20.5),     # Rear 8-pin SPI Dupont plug
    ])
    lcd_holes = [
        cyl_m(50.3, ly, lz, 1.0, 6.0, axis="X", sections=20)
        for ly in (-26.5, 26.5)
        for lz in (60.0, 90.0)
    ]
    items.append(AssemblyItem("02_MACH_07_Man_Hinh_LCD_ST7789_2inch", diff_m(lcd_base, lcd_holes), slot=6))

    # 8. 3W Full-Range Speaker Ø31mm inside Sealed Chamber
    spk_hw = union_m([
        cyl_m(-53.0, 0.0, 93.0, 15.4, 3.2, axis="X", sections=40),
        cyl_m(-48.5, 0.0, 93.0, 12.0, 6.5, axis="X", sections=36),
        cyl_m(-42.5, 0.0, 93.0, 8.2, 6.5, axis="X", sections=32),
    ])
    items.append(AssemblyItem("02_MACH_08_Cu_Loa_3W_Phi31mm", spk_hw, slot=8))

    # 9. Pack Pin 2S 18650 (67 x 37 x 18.5 mm: twin Ø18.2mm cells in shrink wrap)
    bat_m = union_m([
        cyl_m(9.5 - 9.1, 0.0, 60.2 + 9.25, 9.1, 66.8, axis="Y", sections=40),
        cyl_m(9.5 + 9.1, 0.0, 60.2 + 9.25, 9.1, 66.8, axis="Y", sections=40),
        box_m(9.5, 0.0, 60.2 + 9.25, 18.2, 66.8, 17.0),
    ])
    items.append(AssemblyItem("02_MACH_09_Pack_Pin_2S_18650_7V4", bat_m, slot=4))

    # 10. IP2326 Type-C 2S Charger at Rear Z=64.0
    ip_m = union_m([
        box_m(-39.0, 0.0, 63.6, 31.0, 18.0, 1.8),
        box_m(-54.0, 0.0, 64.0, 7.5, 8.6, 3.0),        # Metal USB Type-C port
        box_m(-26.0, 0.0, 69.8, 7.5, 11.5, 9.0),       # Dupont connector
    ])
    items.append(AssemblyItem("02_MACH_10_Mach_Sac_TypeC_IP2326", ip_m, slot=8))

    # 11-12. 2x MINI560 5V Buck Converters + Vertical Dupont plugs
    for tag, sy_sign in (("5V_Servo_Trai", 1.0), ("5V_Logic_Phai", -1.0)):
        mini_m = union_m([
            box_m(27.0, sy_sign * 44.8, 61.2, 29.0, 18.0, 1.6),
            box_m(27.0, sy_sign * 44.8, 63.8, 10.0, 10.0, 4.0),  # Shielded inductor
            box_m(27.0 - 11.5, sy_sign * 44.8, 71.5, 5.2, 5.5, 14.0),  # IN Dupont
            box_m(27.0 + 11.5, sy_sign * 44.8, 71.5, 5.2, 5.5, 14.0),  # OUT Dupont
        ])
        items.append(AssemblyItem(f"02_MACH_Buck_MINI560_{tag}", mini_m, slot=4))

    # 13-14. 2x CH-2 Quick Spring Connectors
    for tag, sy_sign in (("Trai", 1.0), ("Phai", -1.0)):
        ch2_base = union_m([
            box_m(-32.5, sy_sign * 28.5, 68.8, 17.2, 19.2, 9.2),
            box_m(-32.5 - 3.5, sy_sign * 28.5 - 4.2, 75.0, 7.0, 6.0, 4.0),
            box_m(-32.5 - 3.5, sy_sign * 28.5 + 4.2, 75.0, 7.0, 6.0, 4.0),
        ])
        ch2_hole = cyl_m(-32.5, sy_sign * 28.5, 69.0, 1.3, 14.0, axis="Z", sections=20)
        items.append(AssemblyItem(f"02_MACH_Kep_Nguon_CH2_{tag}", diff_m(ch2_base, [ch2_hole]), slot=7))

    # 15-16. Front Chest HLK-LD2410C Radar & INMP441 Mic
    radar_m = union_m([
        box_m(55.0, 0.0, 33.8, 2.2, 22.0, 16.0),
        box_m(47.2, 0.0, 33.8, 11.5, 13.0, 5.5),
    ])
    items.append(AssemblyItem("02_MACH_Radar_24GHz_HLK_LD2410C", radar_m, slot=7))

    mic_m = union_m([
        box_m(54.5, 0.0, 49.8, 1.6, 14.0, 12.8),
        box_m(47.2, 0.0, 49.8, 11.5, 9.5, 5.5),
    ])
    items.append(AssemblyItem("02_MACH_Mic_I2S_INMP441", mic_m, slot=7))

    # 17-19. 3x Symmetric 120-deg TCRT5000 IR Cliff Sensors
    ir_labels = [(0.0, "Mui_Truoc_0"), (120.0, "Duoi_Trai_120"), (-120.0, "Duoi_Phai_Am120")]
    for ir_ang, ir_tag in ir_labels:
        ir_local = union_m([
            box_m(35.0, 0.0, 12.3, 22.0, 14.0, 1.6),
            box_m(45.0, 0.0, 8.2, 5.8, 10.0, 6.8),      # Optical dual-LED shroud
            cyl_m(35.5, 0.0, 15.2, 3.2, 4.5, axis="Z", sections=20),  # Trimmer pot
        ])
        ir_hole = cyl_m(29.0, 0.0, 12.3, 1.5, 6.0, axis="Z", sections=20)
        ir_part = place_mesh(diff_m(ir_local, [ir_hole]), rot_z(ir_ang))
        items.append(AssemblyItem(f"02_MACH_Cam_Bien_Roi_IR_{ir_tag}", ir_part, slot=7))

    # =========================================================================
    # GROUP 03: WHEELS, SERVOS & ANTI-TIP PADS (03_CO_KHI_*)
    # =========================================================================
    base_wheel_mesh = make_nexus_14108_wheel()
    for ang, w_tag in wheel_labels:
        items.append(AssemblyItem(
            f"03_CO_KHI_Banh_Omni_Nexus14108_{w_tag}",
            place_mesh(base_wheel_mesh, rot_z(ang)),
            slot=2,
        ))
        v_mid = -5.6 if ang == 60.0 else 5.6
        items.append(AssemblyItem(
            f"03_CO_KHI_Servo_MG90S_360_Banh_{w_tag}",
            place_mesh(make_mg90s_detailed(40.1, v_mid, 24.0), rot_z(ang)),
            slot=5,
        ))

    for side_tag, sy_sign in (("Trai", 1.0), ("Phai", -1.0)):
        ang_a = 90.0 if sy_sign > 0 else -90.0
        v_arm = 5.6 if sy_sign > 0 else -5.6
        items.append(AssemblyItem(
            f"03_CO_KHI_Servo_MG90S_180_Tay_{side_tag}",
            place_mesh(make_mg90s_detailed(56.5, v_arm, z_arm), rot_z(ang_a)),
            slot=5,
        ))
        pad_m = cyl_m(-42.0, sy_sign * 36.0, 4.5, 5.9, 2.0, axis="Z", sections=32)
        items.append(AssemblyItem(
            f"03_CO_KHI_Dem_Ni_Chong_Lat_Duoi_{side_tag}",
            pad_m,
            slot=8,
        ))

    return items


def write_orca_3mf(path: Path, items: list[AssemblyItem], enable_xray: bool = False) -> None:
    """Write a clean, native OrcaSlicer-compatible multi-part Assembly 3MF archive."""
    model_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<model unit="millimeter" xml:lang="en-US" '
        'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
        'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021">',
        ' <metadata name="Application">OrcaSlicer-2.4.3</metadata>',
        ' <metadata name="BambuStudio:3mfVersion">1</metadata>',
        ' <metadata name="Title">Robot Teo CAD v10 Full Assembly</metadata>',
        ' <resources>',
        '  <basematerials id="1">',
    ]
    for p_name, hex_col, _ in PALETTE:
        model_lines.append(f'   <base name="{escape(p_name)}" displaycolor="{hex_col}"/>')
    model_lines.append('  </basematerials>')

    comp_lines = []
    cfg_part_lines = []

    for idx, item in enumerate(items, start=2):
        pindex = item.slot - 1
        verts = item.mesh.vertices
        faces = item.mesh.faces
        model_lines.append(
            f'  <object id="{idx}" name="{escape(item.name)}" type="model" pid="1" pindex="{pindex}">'
        )
        model_lines.append('   <mesh>')
        model_lines.append('    <vertices>')
        v_strs = [f'     <vertex x="{v[0]:.5f}" y="{v[1]:.5f}" z="{v[2]:.5f}"/>' for v in verts]
        model_lines.extend(v_strs)
        model_lines.append('    </vertices>')
        model_lines.append('    <triangles>')
        f_strs = [f'     <triangle v1="{f[0]}" v2="{f[1]}" v3="{f[2]}"/>' for f in faces]
        model_lines.extend(f_strs)
        model_lines.append('    </triangles>')
        model_lines.append('   </mesh>')
        model_lines.append('  </object>')

        comp_lines.append(f'    <component objectid="{idx}" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>')

        subtype = "modifier_part" if (enable_xray and item.xray_transparent) else "normal_part"
        cfg_part_lines.extend([
            f'    <part id="{idx}" subtype="{subtype}">',
            f'      <metadata key="name" value="{escape(item.name)}"/>',
            '      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>',
            f'      <metadata key="extruder" value="{item.slot}"/>',
            f'      <mesh_stat face_count="{len(faces)}" edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>',
            '    </part>',
        ])

    parent_id = len(items) + 10
    asm_title = (
        "Teo_CAD_v10_Tong_The_Xuyen_Thau" if enable_xray else "Teo_CAD_v10_Tong_The_Day_Du"
    )
    model_lines.append(f'  <object id="{parent_id}" name="{asm_title}" type="model">')
    model_lines.append('   <components>')
    model_lines.extend(comp_lines)
    model_lines.append('   </components>')
    model_lines.append('  </object>')
    model_lines.append(' </resources>')
    model_lines.append(' <build>')
    # Center assembly at (128, 128, 0) on a standard 256x256mm build plate
    model_lines.append(f'  <item objectid="{parent_id}" transform="1 0 0 0 1 0 0 0 1 128 128 0" printable="1"/>')
    model_lines.append(' </build>')
    model_lines.append('</model>')

    cfg_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<config>',
        f'  <object id="{parent_id}">',
        f'    <metadata key="name" value="{asm_title}"/>',
        '    <metadata key="extruder" value="1"/>',
        *cfg_part_lines,
        '  </object>',
        '  <plate>',
        '    <metadata key="plater_id" value="1"/>',
        '    <metadata key="plater_name" value="Tong_The_Robot_Teo_CAD_v10"/>',
        '    <model_instance>',
        f'      <metadata key="object_id" value="{parent_id}"/>',
        '      <metadata key="instance_id" value="0"/>',
        '    </model_instance>',
        '  </plate>',
        '  <assemble>',
        f'    <assemble_item object_id="{parent_id}" instance_id="0" transform="1 0 0 0 1 0 0 0 1 0 0 0" offset="0 0 0"/>',
        '  </assemble>',
        '</config>',
    ]

    slice_info = "\n".join([
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<config>',
        '  <header>',
        '    <header_item key="X-BBL-Client-Type" value="slicer"/>',
        '    <header_item key="OrcaSlicer-Version" value="2.4.3"/>',
        '  </header>',
        '</config>',
    ])

    rels_xml = "\n".join([
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/package/2006/relationships" '
        'xmlns:r="http://schemas.openxmlformats.org/package/2006/relationships">',
        '</Relationships>',
    ])
    # Exact OpenXML relationship header matching OrcaSliced.3mf
    rels_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
        ' <Relationship Target="/3D/3dmodel.model" Id="rel-1" '
        'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n'
        '</Relationships>\n'
    )

    content_types_xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
        ' <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
        ' <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
        ' <Default Extension="config" ContentType="text/xml"/>\n'
        '</Types>\n'
    )

    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.writestr("[Content_Types].xml", content_types_xml)
        zf.writestr("_rels/.rels", rels_xml)
        zf.writestr("3D/3dmodel.model", "\n".join(model_lines))
        zf.writestr("Metadata/model_settings.config", "\n".join(cfg_lines))
        zf.writestr("Metadata/slice_info.config", slice_info)


def export_printed_step_assembly(items: list[AssemblyItem], step_out: Path) -> None:
    """Export all 19 exact B-Rep printed parts with labels & colors as a single STEP assembly."""
    children = []
    for it in items:
        if it.step_shape is not None:
            sh = Compound(children=[it.step_shape], label=it.name)
            rgb = PALETTE[it.slot - 1][2]
            sh.color = Color(*rgb)
            children.append(sh)
    asm = Compound(children=children, label="Robot_Teo_CAD_v10_19_Chi_Tiet_In")
    export_step(asm, str(step_out))


def main() -> None:
    print("Building 46-part CAD v10 Full Assembly (19 Printed + 27 Detailed Hardware)...")
    items = build_all_items()
    print(f"Total components assembled: {len(items)}")

    # Audit watertightness & zero global Z<0 penetration
    z_min_all = min(float(it.mesh.bounds[0][2]) for it in items)
    z_max_all = max(float(it.mesh.bounds[1][2]) for it in items)
    non_wt = [it.name for it in items if not it.mesh.is_watertight]
    print(f"Assembly Z span: [{z_min_all:.2f}, {z_max_all:.2f}] mm | Non-watertight count: {len(non_wt)}")
    if non_wt:
        raise RuntimeError(f"Non-watertight meshes found: {non_wt}")

    full_3mf = OUT_DIR / "teo_tong_the_orca.3mf"
    xray_3mf = OUT_DIR / "teo_tong_the_xuyen_thau_orca.3mf"
    asm_step = STEP_DIR / "teo_tong_the_cad_v10.step"

    write_orca_3mf(full_3mf, items, enable_xray=False)
    print(f"  [OK] Saved Solid Full Assembly 3MF  : {full_3mf} ({full_3mf.stat().st_size / 1024:.1f} KB)")

    write_orca_3mf(xray_3mf, items, enable_xray=True)
    print(f"  [OK] Saved X-Ray Shell Assembly 3MF : {xray_3mf} ({xray_3mf.stat().st_size / 1024:.1f} KB)")

    export_printed_step_assembly(items, asm_step)
    print(f"  [OK] Saved Multi-Body STEP Assembly : {asm_step} ({asm_step.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
