"""Parametric 3D CAD Generator for Robot AI Assistant 'Teo' (CAD v10).

Generates 11 watertight B-Rep mechanical parts (.step and .stl) engineered for:
- Nexus 14108 48x25.5mm Double-Row Omni Wheels (LeKiwi 120-deg holonomic base)
- Custom 3D-printed MG90S cross-horn to Nexus 14108 wheel couplers
- T-slot + vertical screw-clamp mounts for all 5 MG90S servos (zero glue)
- ESP32-CAM (OV3660) horizontal forehead mount behind curved SLA visor
- Pin-up top electronics tray (ESP32-S3 DevKitC-1 + PCA9685) with full Dupont clearance
- Sealed 3W speaker chamber with removable gasketed back cap (Part 7)
- Symmetric 120-deg TCRT5000 IR cliff sensors, HLK-LD2410C radar, INMP441 mic, TTP223 touch
"""

from __future__ import annotations

import math
from pathlib import Path
import build123d as bd
from build123d import (
    Align,
    Axis,
    Box,
    Cone,
    Cylinder,
    Location,
    Plane,
    Polygon,
    Pos,
    RectangleRounded,
    Rot,
    export_step,
    export_stl,
    extrude,
    fillet,
)

OUT_DIR = Path(__file__).resolve().parent
STEP_DIR = OUT_DIR / "step"

# === Master Envelope Parameters (mm) ===
SHELL_X = 116.0          # [-58.0, +58.0] Front (+X) to Rear (-X)
SHELL_Y = 120.0          # [-60.0, +60.0] Left (+Y) to Right (-Y)
Z_BOT = 7.0              # Chassis underside ground clearance
Z_TOP = 142.0            # Top of dome
Z_WAIST = 58.0           # Lower/Upper split plane
Z_NECK = 122.0           # Upper/Head snap-fit dome split plane
WALL = 2.0               # Nominal shell wall thickness
R_CORNER = 24.0          # Horizontal rounded corner radius (> R_DOME to avoid fillet pinch)
R_BOT = 6.0              # Bottom skirt fillet
R_DOME = 21.5            # Top 3D capsule dome fillet (< R_CORNER for C1 manifold geometry)

# === LeKiwi Drive Parameters ===
WHEEL_ANGLES = (60.0, -60.0, 180.0)
R_WHEEL = 58.0           # Wheel center plane radial distance
Z_AXLE = 24.0            # Omni wheel Ø48mm -> axle at Z = 24.0mm
R_ARCH = 28.0            # 4mm radial clearance around Ø48mm wheel
U_ARCH_IN = 40.0         # Inner dry face of wheel arch wall
U_ARCH_OUT = 42.0        # Outer wet face of wheel arch wall (wheel inner face at 45.25mm)

# === 4x M2.5x55mm Waist Corner Pillars ===
BOSS_XY = [
    (-43.5, 45.5),
    (-43.5, -45.5),
    (-6.0, 52.5),
    (-6.0, -52.5),
]

# === 4x Symmetric Side Snap-Fit Clip X-Centers (on Y = +-58.0mm flat walls) ===
SNAP_X = (-16.0, 16.0)

# === Front Face Optical Centers ===
Z_LCD = 75.0             # ST7789 2.0" center (PCB Z = 57.5..92.5)
Z_CAM = 108.0            # ESP32-CAM OV3660 lens center (PCB Z = 94.5..121.5)


def make_pod_solid(sx: float, sy: float, r_xy: float, z0: float, z1: float, r_bot: float, r_top: float):
    """Create a smooth 3D rounded capsule pod solid from z0 to z1."""
    sk = Pos(0, 0, z0) * RectangleRounded(sx, sy, r_xy)
    solid = extrude(sk, amount=z1 - z0)
    top_edges = solid.edges().filter_by_position(Axis.Z, z1 - 0.15, z1 + 0.15)
    solid = fillet(top_edges, radius=r_top)
    bot_edges = solid.edges().filter_by_position(Axis.Z, z0 - 0.15, z0 + 0.15)
    solid = fillet(bot_edges, radius=r_bot)
    return solid


def build_master_shells():
    """Construct master outer solid, inner cavity, and 2mm hollow shell."""
    outer = make_pod_solid(
        SHELL_X, SHELL_Y, R_CORNER, Z_BOT, Z_TOP, R_BOT, R_DOME
    )
    inner = make_pod_solid(
        SHELL_X - 2 * WALL,
        SHELL_Y - 2 * WALL,
        R_CORNER - WALL,
        Z_BOT + WALL,
        Z_TOP - WALL,
        R_BOT - WALL,
        R_DOME - WALL,
    )
    return outer, inner, outer - inner


def build_lower_chassis(outer, inner, shell):
    """Build Part 4: Lower Chassis (teo_than_duoi)."""
    # Slice Z = 7.0 .. 58.0
    part = shell & Pos(0, 0, Z_BOT) * Box(
        200, 200, Z_WAIST - Z_BOT, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )

    # 1. Add 3 wheel arch housings & subtract wheel arch cutouts
    for idx, ang in enumerate(WHEEL_ANGLES):
        # Eccentric servo offset so front servos lean toward +X (away from rear servo)
        v_mid = -5.6 if ang == 60.0 else 5.6

        # Solid arch wall block before cutting wheel space
        arch_housing = Pos(U_ARCH_IN, 0, Z_AXLE) * Rot(0, 90, 0) * Cylinder(
            R_ARCH + WALL, 30.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        arch_housing += Pos(U_ARCH_IN, 0, Z_BOT) * Box(
            30.0, 2 * (R_ARCH + WALL), Z_AXLE - Z_BOT,
            align=(Align.MIN, Align.CENTER, Align.MIN),
        )
        part += (Rot(0, 0, ang) * arch_housing) & outer

        # Subtract wheel arch void (u >= 42.5mm, R = 28.0mm)
        arch_void = Pos(U_ARCH_OUT, 0, Z_AXLE) * Rot(0, 90, 0) * Cylinder(
            R_ARCH, 40.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        arch_void += Pos(U_ARCH_OUT, 0, 0.0) * Box(
            40.0, 2 * R_ARCH, Z_AXLE,
            align=(Align.MIN, Align.CENTER, Align.MIN),
        )
        part -= Rot(0, 0, ang) * arch_void

        # Add T-slot servo cradle inside dry chassis
        cradle = Pos(23.0, v_mid, Z_BOT + 1.5) * Box(
            U_ARCH_IN + 0.5 - 23.0,
            37.2,
            30.2 - (Z_BOT + 1.5),
            align=(Align.MIN, Align.CENTER, Align.MIN),
        )
        part += (Rot(0, 0, ang) * cradle) & outer

        # Subtract servo case channel (23.2mm wide, bottom at Z=17.8, nose pocket to u=40.8)
        servo_cut = Pos(10.0, v_mid, 17.8) * Box(
            40.8 - 10.0, 23.2, 20.0,
            align=(Align.MIN, Align.CENTER, Align.MIN),
        )
        # Subtract ear T-slots (u = 30.8..34.0, span 33.2mm -> MG90S front at u=40.1)
        ear_cut = Pos(30.8, v_mid, 17.8) * Box(
            3.2, 33.2, 20.0,
            align=(Align.MIN, Align.CENTER, Align.MIN),
        )
        # Subtract Ø12.8mm MG90S gear boss hole + secondary gear bump slot through arch wall
        shaft_cut = Pos(37.5, 0, Z_AXLE) * Rot(0, 90, 0) * Cylinder(
            6.4, 10.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        aux_boss_cut = Pos(37.5, 0.5 * v_mid, Z_AXLE) * Box(
            10.0, 7.0, 6.8, align=(Align.MIN, Align.CENTER, Align.CENTER)
        )
        # Subtract 2 vertical M2.5 clamp pilot holes (30.0mm spacing at u = 27.0)
        clamp_h1 = Pos(27.0, v_mid - 15.0, 20.0) * Cylinder(
            1.08, 12.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        clamp_h2 = Pos(27.0, v_mid + 15.0, 20.0) * Cylinder(
            1.08, 12.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        part -= Rot(0, 0, ang) * (servo_cut + ear_cut + shaft_cut + aux_boss_cut + clamp_h1 + clamp_h2)

    # 2. Add 4 corner M2.5 screw pillars + side bulkhead support tabs
    for bx, by in BOSS_XY:
        pillar = Pos(bx, by, Z_BOT + 1.0) * Cylinder(
            5.6, Z_WAIST - (Z_BOT + 1.0), align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        # Web connecting pillar to nearest outer wall to eliminate islands/cantilevers
        sy_sign = 1.0 if by > 0 else -1.0
        web = Pos(bx, by + sy_sign * 3.5, Z_BOT + 1.0) * Box(
            8.0, 8.0, Z_WAIST - (Z_BOT + 1.0),
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        part += (pillar + web) & outer

    # Side support ribs at Z=58.0 for bulkhead
    for sy_sign in (-1.0, 1.0):
        rib = Pos(-24.0, sy_sign * 55.5, 49.0) * Box(
            14.0, 6.0, 9.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        part += rib & outer

    # 3. Add 3 symmetric 120-deg TCRT5000 IR cliff sensor mounts (0, +120, -120 deg)
    for ir_ang in (0.0, 120.0, -120.0):
        ir_boss = Pos(29.0, 0, Z_BOT + 1.5) * Cylinder(
            4.0, 2.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        part += Rot(0, 0, ir_ang) * ir_boss
        ir_hole = Pos(29.0, 0, Z_BOT + 0.8) * Cylinder(
            1.35, 4.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        opt_cut = Pos(45.0, 0, 0.0) * Box(
            7.2, 11.2, 14.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        part -= Rot(0, 0, ir_ang) * (ir_hole + opt_cut)

    # 4. Front internal Radar HLK-LD2410C (Z=33.5) & Mic INMP441 (Z=49.5) pockets
    # Radar frame + 1.4mm thinned front window
    radar_frame = Pos(52.2, 0, 23.8) * Box(
        5.0, 26.0, 18.2, align=(Align.MIN, Align.CENTER, Align.MIN)
    )
    mic_frame = Pos(52.2, 0, 42.0) * Box(
        5.0, 18.0, 14.2, align=(Align.MIN, Align.CENTER, Align.MIN)
    )
    part += (radar_frame + mic_frame) & outer

    radar_slot = Pos(53.5, 0, 25.2) * Box(
        3.1, 22.6, 17.5, align=(Align.MIN, Align.CENTER, Align.MIN)
    )
    radar_back_open = Pos(49.0, 0, 26.5) * Box(
        5.0, 19.0, 16.5, align=(Align.MIN, Align.CENTER, Align.MIN)
    )
    mic_slot = Pos(53.4, 0, 42.4) * Box(
        2.3, 14.6, 14.8, align=(Align.MIN, Align.CENTER, Align.MIN)
    )
    mic_back_open = Pos(49.0, 0, 43.5) * Box(
        5.0, 11.5, 13.5, align=(Align.MIN, Align.CENTER, Align.MIN)
    )
    mic_foam = Pos(55.0, 0, 49.5) * Rot(0, 90, 0) * Cylinder(
        3.2, 1.2, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    mic_port = Pos(54.0, 0, 49.5) * Rot(0, 90, 0) * Cylinder(
        1.0, 8.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    part -= radar_slot + radar_back_open + mic_slot + mic_back_open + mic_foam + mic_port

    # 5. Dual rear anti-tip pad seats on underside (-42.0, +-36.0) outside 180-deg wheel arch!
    for sy_sign in (-1.0, 1.0):
        pad_boss = Pos(-42.0, sy_sign * 36.0, 5.5) * Cylinder(
            7.5, 3.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        pad_recess = Pos(-42.0, sy_sign * 36.0, 5.0) * Cylinder(
            6.0, 1.5, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        part += pad_boss
        part -= pad_recess

    # 6. Waist inner rabbet groove (Z=56.0..58.1) leaving 1.0mm outer cosmetic wall
    rabbet_outer = extrude(
        Pos(0, 0, 56.0) * RectangleRounded(SHELL_X - 2.0, SHELL_Y - 2.0, R_CORNER - 1.0),
        amount=2.2,
    )
    rabbet_inner = extrude(
        Pos(0, 0, 55.9) * RectangleRounded(SHELL_X - 6.0, SHELL_Y - 6.0, R_CORNER - 3.0),
        amount=2.4,
    )
    rabbet_ring = rabbet_outer - rabbet_inner
    for bx, by in BOSS_XY:
        rabbet_ring -= Pos(bx, by, 55.0) * Cylinder(
            8.0, 4.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
    rabbet_ring -= Pos(55.0, 0, 55.0) * Box(12.0, 22.0, 4.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    rabbet_ring -= Pos(-55.0, 0, 55.0) * Box(12.0, 26.0, 4.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    part -= rabbet_ring

    # 7. Drill 4 bottom counterbores (Ø5.6mm, Z=7..15) + M2.5 clearance bores (Ø2.9mm, Z=14..59)
    for bx, by in BOSS_XY:
        cbore = Pos(bx, by, 5.0) * Cylinder(
            2.8, 10.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        thru = Pos(bx, by, 14.0) * Cylinder(
            1.45, 46.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        part -= cbore + thru

    return part


def build_bulkhead():
    """Build Part 3: Mid-Deck Bulkhead (teo_vach_ngan, Z = 58.0..70.0mm)."""
    plate = extrude(
        Pos(0, 0, Z_WAIST) * RectangleRounded(106.8, 110.8, R_CORNER - 4.6),
        amount=2.0,
    )
    for bx, by in BOSS_XY:
        plate += Pos(bx, by, Z_WAIST) * Cylinder(
            5.2, 2.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
    # Rear notch for IP2326 bottom rail + Front notch for LCD ST7789 bottom edge & bezel pad
    plate -= Pos(-56.0, 0, Z_WAIST - 0.5) * Box(
        33.5, 24.0, 3.0, align=(Align.MIN, Align.CENTER, Align.MIN)
    )
    plate -= Pos(47.2, 0, Z_WAIST - 0.5) * Box(
        10.0, 76.4, 3.0, align=(Align.MIN, Align.CENTER, Align.MIN)
    )

    # Central 2S Battery Pack (67.0 x 37.0 x 18.5mm) retaining frame: X in [-9.0, +28.0], Y in [-33.8, +33.8]
    bat_cx = 9.5
    bat_outer = Pos(bat_cx, 0, Z_WAIST + 2.0) * Box(
        41.0, 71.0, 10.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    bat_inner = Pos(bat_cx, 0, Z_WAIST + 2.0) * Box(
        37.6, 67.6, 12.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    # Lightening / finger-grip + SM-2P cable exit slots on battery frame
    bat_slots = Pos(bat_cx, 0, Z_WAIST + 4.5) * Box(
        45.0, 36.0, 7.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    bat_slots += Pos(bat_cx + 6.0, 34.0, Z_WAIST + 2.0) * Box(
        18.0, 8.0, 12.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    part = plate + (bat_outer - bat_inner - bat_slots)

    # 2x CH-2 spring connector M2.5 standoffs on rear-side bays (X=-32.5, Y=+-28.5, 100% clear of Arm gussets!)
    for sy_sign in (-1.0, 1.0):
        ch2_post = Pos(-32.5, sy_sign * 28.5, Z_WAIST + 2.0) * Cylinder(
            4.2, 4.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        ch2_hole = Pos(-32.5, sy_sign * 28.5, Z_WAIST + 0.8) * Cylinder(
            1.08, 6.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        part = part + ch2_post - ch2_hole

        # 2x MINI560 (29.0 x 18.0 mm) snap cradles on front-side wings (X=27.0, Y=+-44.8, 39mm open headroom!)
        m_cx, m_cy = 27.0, sy_sign * 44.8
        m_outer = Pos(m_cx, m_cy, Z_WAIST + 2.0) * Box(
            32.6, 21.6, 4.2, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        m_inner = Pos(m_cx, m_cy, Z_WAIST + 2.0) * Box(
            29.6, 18.6, 5.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        # Open ends slightly for pin header solder joints
        m_open = Pos(m_cx, m_cy, Z_WAIST + 2.0) * Box(
            34.0, 11.0, 5.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        part += (m_outer - m_inner - m_open) & extrude(
            Pos(0, 0, Z_WAIST) * RectangleRounded(106.8, 110.8, R_CORNER - 4.6),
            amount=12.0,
        )

    # 3x Cable pass-through slots + 4x M2.5 corner screw holes
    front_cable = extrude(
        Pos(38.5, 0, Z_WAIST - 0.5) * RectangleRounded(7.5, 28.0, 3.0),
        amount=3.0,
    )
    part -= front_cable
    for sy_sign in (-1.0, 1.0):
        side_cable = extrude(
            Pos(-18.5, sy_sign * 16.0, Z_WAIST - 0.5) * RectangleRounded(9.5, 15.0, 3.0),
            amount=3.0,
        )
        part -= side_cable

    for bx, by in BOSS_XY:
        part -= Pos(bx, by, Z_WAIST - 0.5) * Cylinder(
            1.45, 4.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )

    return part


def build_upper_shell(outer, inner, shell):
    """Build Part 1: Upper Shell (teo_than_tren, Z = 56.2..122.0mm)."""
    part = shell & Pos(0, 0, Z_WAIST) * Box(
        200, 200, Z_NECK - Z_WAIST, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )

    # 1. Notched waist alignment lip (Z = 56.3..59.2) fused into Upper Shell wall
    lip_outer = extrude(
        Pos(0, 0, 56.3) * RectangleRounded(SHELL_X - 2.5, SHELL_Y - 2.5, R_CORNER - 1.25),
        amount=2.9,
    )
    lip_inner = extrude(
        Pos(0, 0, 56.2) * RectangleRounded(SHELL_X - 4.4, SHELL_Y - 4.4, R_CORNER - 2.2),
        amount=3.1,
    )
    lip = lip_outer - lip_inner
    for bx, by in BOSS_XY:
        lip -= Pos(bx, by, 55.5) * Cylinder(
            8.4, 4.5, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
    lip -= Pos(55.0, 0, 55.5) * Box(14.0, 24.0, 4.5, align=(Align.CENTER, Align.CENTER, Align.MIN))
    lip -= Pos(-55.0, 0, 55.5) * Box(14.0, 28.0, 4.5, align=(Align.CENTER, Align.CENTER, Align.MIN))
    part += lip & outer

    # 2. 4x Upper M2.5 screw pillars starting at Z = 60.1mm (clamping bulkhead at Z=58..60!)
    for bx, by in BOSS_XY:
        sy_sign = 1.0 if by > 0 else -1.0
        sx_off = -5.5 if bx < -20.0 else 0.0
        up_pil = Pos(bx, by, 60.1) * Cylinder(
            5.3, 14.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        # 45-deg printable taper at top
        up_cone = Pos(bx, by, 74.1) * Cone(
            5.3, 1.2, 5.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        up_web = Pos(bx + sx_off, by + sy_sign * 5.0, 60.1) * Box(
            12.0, 12.0, 16.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        part += (up_pil + up_cone + up_web) & outer
        part -= Pos(bx, by, 59.8) * Cylinder(
            1.08, 13.5, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )

    # 3. Front SLA Visor Bezel + LCD ST7789 + ESP32-CAM (OV3660) Mounts
    # Internal front reinforcement pad (X = 52.5..58.0, Z = 58.2..122.0)
    front_pad = Pos(52.5, 0, 58.2) * Box(
        6.0, 74.0, 63.8, align=(Align.MIN, Align.CENTER, Align.MIN)
    )
    part += front_pad & outer

    # Curved exterior SLA Visor recess (1.9mm deep along +X, 70.4 x 60.4 mm in YZ: Z = 58.3..118.7)
    visor_prism = Rot(0, 90, 0) * extrude(
        Pos(-(58.3 + 60.4 / 2), 0, 45.0) * RectangleRounded(60.4, 70.4, 9.0),
        amount=20.0,
    )
    visor_recess_cut = (outer - Pos(-1.9, 0, 0) * outer) & visor_prism
    part -= visor_recess_cut

    # LCD ST7789 2.0" window (42.0 x 32.0 mm centered at Z_LCD = 75.0)
    lcd_win = Pos(48.0, 0, Z_LCD) * Box(
        15.0, 42.0, 32.0, align=(Align.MIN, Align.CENTER, Align.CENTER)
    )
    # LCD glass seat pocket leaving 4 corner M2 pads at (Y=+-26.5, Z=Z_LCD+-15.0)
    lcd_glass_seat = Pos(50.0, 0, Z_LCD) * Box(
        4.3, 47.0, 35.8, align=(Align.MIN, Align.CENTER, Align.CENTER)
    )
    lcd_mid_relief = Pos(50.0, 0, Z_LCD) * Box(
        4.3, 59.2, 23.0, align=(Align.MIN, Align.CENTER, Align.CENTER)
    )
    part -= lcd_win + lcd_glass_seat + lcd_mid_relief

    # ESP32-CAM + OV3660 Pinhole (Ø6.6mm at Y=0, Z=Z_CAM=108.0) & Slide-in Bracket
    # Shift PCB center to Y = +9.5mm so folded OV3660 lens aligns at Y = 0!
    cam_hole = Pos(48.0, 0, Z_CAM) * Rot(0, 90, 0) * Cylinder(
        3.3, 15.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    # Lens barrel & MicroSD slot relief pocket (X = 52.5..55.2)
    cam_lens_relief = Pos(52.4, 2.0, Z_CAM) * Box(
        2.8, 20.0, 16.0, align=(Align.MIN, Align.CENTER, Align.CENTER)
    )
    part -= cam_hole + cam_lens_relief

    # Horizontal U-rail for ESP32-CAM (PCB Z = 94.5..121.5 -> bot_rail at Z = 92.7..94.4 clears LCD top Z=92.5!)
    cam_bot_rail = Pos(48.2, 10.0, 92.7) * Box(
        7.5, 44.0, 1.7, align=(Align.MIN, Align.CENTER, Align.MIN)
    )
    cam_top_clips = Pos(48.2, -7.0, Z_CAM + 11.9) * Box(
        7.5, 10.0, 1.8, align=(Align.MIN, Align.CENTER, Align.MIN)
    ) + Pos(48.2, 24.0, Z_CAM + 11.9) * Box(
        7.5, 10.0, 1.8, align=(Align.MIN, Align.CENTER, Align.MIN)
    )
    cam_end_stop = Pos(48.2, 31.0, 92.7) * Box(
        7.5, 2.2, 29.2, align=(Align.MIN, Align.CENTER, Align.MIN)
    )
    cam_pcb_groove = Pos(48.4, 9.5, Z_CAM) * Box(
        4.1, 42.0, 27.3, align=(Align.MIN, Align.CENTER, Align.CENTER)
    )
    # Add top bridge behind PCB so cam_top_clips fuse solidly into front_pad
    cam_top_bridge = Pos(48.2, 9.5, 121.65) * Box(
        7.5, 42.0, 0.35, align=(Align.MIN, Align.CENTER, Align.MIN)
    )
    part += (cam_bot_rail + cam_top_clips + cam_end_stop) & outer
    part -= cam_pcb_groove
    part += cam_top_bridge & outer

    # Drill 4x M2 LCD pilot holes AFTER camera rails so no hole gets covered!
    for ly in (-26.5, 26.5):
        for lz in (Z_LCD - 15.0, Z_LCD + 15.0):
            part -= Pos(45.0, ly, lz) * Rot(0, 90, 0) * Cylinder(
                2.3, 7.5, align=(Align.CENTER, Align.CENTER, Align.MIN)
            )
            part -= Pos(52.0, ly, lz) * Rot(0, 90, 0) * Cylinder(
                0.88, 3.3, align=(Align.CENTER, Align.CENTER, Align.MIN)
            )

    # 4. Left & Right Arm Servo T-Slot Cradles (Z = 86.5, X = 0.0, eccentric X_mid = -5.6)
    z_arm = 86.5
    for sy_sign in (-1.0, 1.0):
        # Rotate local frame so +u points outward along +-Y!
        rot_arm = Rot(0, 0, 90.0 if sy_sign > 0 else -90.0)
        v_arm_mid = 5.6 if sy_sign > 0 else -5.6  # both map to global X = -5.6!

        # Exact 45-deg self-supporting profile in local (u, z), extruded explicitly along +v!
        arm_prof = Polygon(
            [(40.5, 78.5), (59.0, 60.0), (59.0, 92.7), (40.5, 92.7)],
            align=None,
        )
        arm_plane = Plane(origin=(0, v_arm_mid - 17.8, 0), x_dir=(1, 0, 0), z_dir=(0, 1, 0))
        arm_blk = extrude(arm_plane * arm_prof, amount=35.6)
        part += (rot_arm * arm_blk) & outer

        # Exterior Ø14.2mm x 1.5mm shoulder recess + Ø12.8mm MG90S boss hole + servo T-slot
        sh_recess = Pos(58.5, 0, z_arm) * Rot(0, 90, 0) * Cylinder(
            7.1, 4.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        sh_shaft = Pos(54.0, 0, z_arm) * Rot(0, 90, 0) * Cylinder(
            6.4, 8.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        sh_aux = Pos(54.0, 0.5 * v_arm_mid, z_arm) * Box(
            5.0, 7.0, 6.8, align=(Align.MIN, Align.CENTER, Align.CENTER)
        )
        arm_servo_cut = Pos(26.0, v_arm_mid, z_arm - 6.2) * Box(
            57.0 - 26.0, 23.2, 18.0, align=(Align.MIN, Align.CENTER, Align.MIN)
        )
        arm_ear_cut = Pos(47.2, v_arm_mid, z_arm - 6.2) * Box(
            3.2, 33.2, 18.0, align=(Align.MIN, Align.CENTER, Align.MIN)
        )
        arm_h1 = Pos(44.0, v_arm_mid - 15.0, z_arm - 4.0) * Cylinder(
            1.08, 12.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        arm_h2 = Pos(44.0, v_arm_mid + 15.0, z_arm - 4.0) * Cylinder(
            1.08, 12.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        part -= rot_arm * (sh_recess + sh_shaft + sh_aux + arm_servo_cut + arm_ear_cut + arm_h1 + arm_h2)

    # 5. Rear Panel: IP2326 Type-C Charger (Z=64.0), Sealed 3W Speaker Chamber (Z=93.0), Louvers
    # IP2326 rails (X = -56.5..-23.5, inner pocket X = -54.8..-23.0, inner width 18.6mm)
    ip_outer = Pos(-56.5, 0, 60.3) * Box(
        33.0, 22.6, 6.8, align=(Align.MIN, Align.CENTER, Align.MIN)
    )
    ip_inner = Pos(-54.9, 0, 61.7) * Box(
        32.5, 18.6, 4.8, align=(Align.MIN, Align.CENTER, Align.MIN)
    )
    ip_top_open = Pos(-52.5, 0, 63.0) * Box(
        30.5, 15.0, 6.0, align=(Align.MIN, Align.CENTER, Align.MIN)
    )
    part += (ip_outer - ip_inner - ip_top_open) & outer

    # Type-C port cutout (9.8 x 4.3mm rounded) + 2x Ø1.5mm LED peepholes at Z=68.5
    usbc_cut = Rot(0, 90, 0) * extrude(
        Pos(-64.0, 0, -62.0) * RectangleRounded(4.3, 9.8, 1.8),
        amount=10.0,
    )
    led_h1 = Pos(-62.0, -1.5, 68.5) * Rot(0, 90, 0) * Cylinder(0.75, 10.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    led_h2 = Pos(-62.0, 1.5, 68.5) * Rot(0, 90, 0) * Cylinder(0.75, 10.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    part -= usbc_cut + led_h1 + led_h2

    # Sealed 3W Speaker Cylinder (Z = 93.0, X = -56.5..-29.0, OD Ø36.4, ID Ø32.0)
    z_spk = 93.0
    spk_cyl = Pos(-56.5, 0, z_spk) * Rot(0, 90, 0) * Cylinder(
        18.2, 27.5, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    # 45-deg printable support fin under speaker cylinder (clears IP2326 LEDs!)
    spk_rib = Pos(-56.5, 0, 70.5) * Box(
        20.0, 4.0, z_spk - 70.5, align=(Align.MIN, Align.CENTER, Align.MIN)
    )
    spk_rib -= (
        Pos(-36.5, 0, 70.5)
        * Rot(0, -40, 0)
        * Box(25.0, 8.0, 25.0, align=(Align.MIN, Align.CENTER, Align.MAX))
    )
    part += (spk_cyl + spk_rib) & outer

    spk_bore = Pos(-54.0, 0, z_spk) * Rot(0, 90, 0) * Cylinder(
        16.0, 26.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    spk_seat = Pos(-54.8, 0, z_spk) * Rot(0, 90, 0) * Cylinder(
        15.9, 2.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    spk_cap_step = Pos(-31.0, 0, z_spk) * Rot(0, 90, 0) * Cylinder(
        16.9, 3.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    part -= spk_bore + spk_seat + spk_cap_step

    # 19x Ø2.5mm hex-grid acoustic grille holes through rear wall
    grille_pts = [(0.0, 0.0)]
    for k in range(6):
        a = math.radians(k * 60.0)
        grille_pts.append((5.5 * math.cos(a), 5.5 * math.sin(a)))
    for k in range(12):
        a = math.radians(k * 30.0)
        grille_pts.append((10.8 * math.cos(a), 10.8 * math.sin(a)))
    for gy, gz in grille_pts:
        part -= Pos(-62.0, gy, z_spk + gz) * Rot(0, 90, 0) * Cylinder(
            1.25, 10.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )

    # 3x 45-deg downward-sloped rear cooling louvers (Z = 113.5, 116.3, 119.1)
    for lz in (113.5, 116.3, 119.1):
        louver = (
            Pos(-57.0, 0, lz)
            * Rot(0, 35, 0)
            * Box(8.0, 26.0, 1.8, align=(Align.CENTER, Align.CENTER, Align.CENTER))
        )
        part -= louver

    # 6. 4x Tray Corner Support Pads at Z = 99.0mm (rear pad at X=-23.5 clearing MG90S X=-17.0!)
    for sy_sign in (-1.0, 1.0):
        y_in = sy_sign * 48.5
        y_out = sy_sign * 59.0
        tri_yz = Polygon([(y_in, 99.0), (y_out, 99.0), (y_out, 88.5)], align=None)
        for px, dx in ((22.0, 10.0), (-23.5, 8.0)):
            t_pad = extrude(Plane.YZ.offset(px - dx / 2.0) * tri_yz, amount=dx)
            part += t_pad & outer
        # M2.5 pilot hole on front tray pads (X = +22.0, Y = +-51.5)
        part -= Pos(22.0, sy_sign * 51.5, 92.5) * Cylinder(
            1.08, 7.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )

    # Ensure crisp Z_NECK = 122.0 top plane first
    part &= Pos(0, 0, 55.0) * Box(200, 200, Z_NECK - 55.0, align=(Align.CENTER, Align.CENTER, Align.MIN))

    # 7. 4x Internal 45-deg Snap-Fit Catch Grooves (X = +-16.0, Y = +-58.0) + Rear Fingernail Pry Slot
    for sx_c in SNAP_X:
        for sy_sign in (-1.0, 1.0):
            groove_poly = Polygon(
                [
                    (sy_sign * 57.20, 117.20),
                    (sy_sign * 58.60, 118.60),
                    (sy_sign * 58.60, 120.15),
                    (sy_sign * 57.20, 121.55),
                ],
                align=None,
            )
            lead_in_poly = Polygon(
                [
                    (sy_sign * 57.20, 121.45),
                    (sy_sign * 58.35, 122.05),
                    (sy_sign * 57.20, 122.05),
                ],
                align=None,
            )
            groove_cut = extrude(Plane.YZ.offset(sx_c) * groove_poly, amount=7.0, both=True)
            lead_in_cut = extrude(Plane.YZ.offset(sx_c) * lead_in_poly, amount=7.0, both=True)
            part -= groove_cut + lead_in_cut

    # Rear fingernail pry slot (lower chamfer bevel at X = -58.0, Y in [-8, +8], Z = 121.3..122.0)
    part -= (
        Pos(-58.2, 0, 122.0)
        * Rot(0, 45, 0)
        * Box(1.6, 16.0, 1.6, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    )

    return part


def build_tray():
    """Build Part 6: Top Drop-In Electronics Tray (teo_khay_linh_kien, Z = 99.0..107.5mm)."""
    z0 = 99.0
    # Main deck X in [-25.0, +32.5] (57.5mm, clearing Speaker Cap at X=-27.2!), Y in [-41.5, +41.5]
    deck = extrude(
        Pos(3.75, 0, z0) * RectangleRounded(57.5, 83.0, 5.0),
        amount=2.2,
    )
    # 4 corner mounting ears reaching |Y| = 54.5 at X = +22.0 and X = -23.5 (with bridge at |Y|>=36)
    for sy_sign in (-1.0, 1.0):
        deck += extrude(
            Pos(22.0, sy_sign * 47.0, z0) * RectangleRounded(10.0, 15.0, 3.0),
            amount=2.2,
        )
        deck += extrude(
            Pos(-23.5, sy_sign * 45.5, z0) * RectangleRounded(8.0, 18.0, 3.0),
            amount=2.2,
        )
        deck += extrude(
            Pos(-20.0, sy_sign * 39.5, z0) * RectangleRounded(10.0, 8.0, 2.0),
            amount=2.2,
        )
        deck -= Pos(22.0, sy_sign * 51.5, z0 - 0.5) * Cylinder(
            1.45, 4.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )

    # 1. Rear Bay: ESP32-S3 DevKitC-1 Pin-Up Cradle (X in [-24.0, +4.4], Y in [-32.8, +32.8])
    esp_cx = -9.8
    esp_frame = Pos(esp_cx, 0, z0 + 2.2) * Box(
        31.2, 68.4, 6.2, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    # Trough for USB-C & buttons underneath (Z = 101.2..105.8, leaving end/corner ledges at Z=105.8)
    esp_trough = Pos(esp_cx, 0, z0 + 2.2) * Box(
        24.0, 66.0, 4.6, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    # PCB seat (28.5 x 65.8 mm at Z = 105.8..108.0)
    esp_pcb_seat = Pos(esp_cx, 0, z0 + 6.8) * Box(
        28.5, 65.8, 3.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    # Open +Y end for USB-C cable access & open middle walls for finger grip
    esp_usbc_open = Pos(esp_cx, 32.0, z0 + 2.2) * Box(
        22.0, 10.0, 7.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    part = deck + (esp_frame - esp_trough - esp_pcb_seat - esp_usbc_open)

    # 2. Front Bay: PCA9685 Flat Pin-Up Cradle (X in [+5.8, +31.6], Y in [-31.5, +31.5])
    pca_cx = 18.7
    pca_frame = Pos(pca_cx, 0, z0 + 2.2) * Box(
        28.2, 65.4, 3.2, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    pca_inner = Pos(pca_cx, 0, z0 + 2.2) * Box(
        25.8, 63.2, 4.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    # Open BOTH Y ends so right-angle I2C 6-pin header + Dupont plug pass freely!
    pca_open_ends = Pos(pca_cx, 0, z0 + 2.2) * Box(
        19.0, 70.0, 4.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    part += pca_frame - pca_inner - pca_open_ends

    # 3. Underside MAX98357A I2S Amp Clip Frame (grips X edges, open along +-Y for Dupont & speaker wires!)
    amp_outer = Pos(pca_cx, 0, z0 - 4.0) * Box(
        22.4, 20.6, 4.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    amp_inner = Pos(pca_cx, 0, z0 - 4.5) * Box(
        19.6, 18.1, 5.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    amp_open = Pos(pca_cx, 0, z0 - 4.5) * Box(
        15.2, 24.0, 5.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    part += amp_outer - amp_inner - amp_open

    # 4. Top SM-2P Battery Quick-Disconnect Parking Clip at (X = +18.0, Y = +37.2)
    sm_outer = Pos(18.0, 37.2, z0 + 2.2) * Box(
        14.0, 7.6, 5.5, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    sm_inner = Pos(18.0, 37.2, z0 + 2.2) * Box(
        15.0, 4.8, 6.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    part += sm_outer - sm_inner

    # 5. Generous Cable Pass-Through Slots through Deck (Left, Right, & ESP32 center slot)
    part -= extrude(
        Pos(esp_cx, 0, z0 - 0.5) * RectangleRounded(12.0, 44.0, 4.0),
        amount=3.5,
    )
    part -= extrude(
        Pos(-8.0, 37.2, z0 - 0.5) * RectangleRounded(24.0, 6.5, 2.5),
        amount=3.5,
    )
    part -= extrude(
        Pos(3.0, -37.2, z0 - 0.5) * RectangleRounded(44.0, 6.5, 2.5),
        amount=3.5,
    )

    return part


def build_head_dome(outer, inner, shell):
    """Build Part 8: Snap-Fit Top Dome Cap (teo_mu_dau, Z = 117.85..142.0mm)."""
    part = shell & Pos(0, 0, Z_NECK) * Box(
        200, 200, Z_TOP - Z_NECK + 2.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )

    # Inner alignment skirt (Z = 120.4..122.1) + upper fusion bridge (Z = 122.1..123.6)
    lip_low_out = extrude(
        Pos(0, 0, 120.4) * RectangleRounded(SHELL_X - 5.4, SHELL_Y - 5.4, R_CORNER - 2.7),
        amount=1.8,
    )
    lip_low_in = extrude(
        Pos(0, 0, 120.3) * RectangleRounded(SHELL_X - 7.8, SHELL_Y - 7.8, R_CORNER - 3.9),
        amount=3.5,
    )
    lip_bridge_out = extrude(
        Pos(0, 0, 122.1) * RectangleRounded(SHELL_X - 2.4, SHELL_Y - 2.4, R_CORNER - 1.2),
        amount=1.5,
    )
    skirt = ((lip_low_out + lip_bridge_out) - lip_low_in) & outer
    # Front camera forehead & Rear louver clearance notches on lower skirt
    skirt -= Pos(52.0, 0.0, 119.8) * Box(14.0, 76.0, 4.5, align=(Align.CENTER, Align.CENTER, Align.MIN))
    skirt -= Pos(-54.0, 0.0, 119.8) * Box(12.0, 38.0, 4.5, align=(Align.CENTER, Align.CENTER, Align.MIN))

    # Cut 1.0mm U-slot flex reliefs on either side of each snap-fit clip
    for sx_c in SNAP_X:
        for sy_sign in (-1.0, 1.0):
            for dx_slot in (-6.3, 6.3):
                skirt -= Pos(sx_c + dx_slot, sy_sign * 56.8, 120.2) * Box(
                    1.0, 3.0, 1.9, align=(Align.CENTER, Align.CENTER, Align.MIN)
                )
    part += skirt

    # 4x Hidden Cantilever Snap-Fit Clips (X = +-16.0, Y = +-57.3 -> bead crest at |Y| = 58.35)
    for sx_c in SNAP_X:
        for sy_sign in (-1.0, 1.0):
            clip_pts = [
                (sy_sign * 56.10, 117.85),
                (sy_sign * 57.10, 117.85),
                (sy_sign * 58.35, 119.10),
                (sy_sign * 58.35, 119.55),
                (sy_sign * 57.30, 120.60),
                (sy_sign * 57.30, 122.10),
                (sy_sign * 58.60, 122.10),
                (sy_sign * 58.60, 123.50),
                (sy_sign * 56.10, 123.50),
            ]
            clip_poly = Polygon(clip_pts, align=None)
            clip_solid = extrude(Plane.YZ.offset(sx_c) * clip_poly, amount=5.8, both=True)
            part += clip_solid & outer

    # Rear fingernail pry slot (upper chamfer bevel at X = -58.0, Y in [-8, +8], Z = 122.0..122.7)
    part -= (
        Pos(-58.2, 0, 122.0)
        * Rot(0, 45, 0)
        * Box(1.6, 16.0, 1.6, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    )

    # Thin apex Ø22mm circular zone to exact 1.0mm thickness (Z = 141.0..142.0) for TTP223 touch!
    part -= Pos(0, 0, 137.0) * Cylinder(
        11.0, 4.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    # Locating rim for TTP223 (15.0 x 11.0 mm) at Z = 139.6..141.2 fused to roof
    ttp_outer = Pos(0, 0, 139.6) * Box(
        18.0, 14.0, 1.6, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    ttp_inner = Pos(0, 0, 139.4) * Box(
        15.6, 11.6, 1.6, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    part += (ttp_outer - ttp_inner) & outer

    return part


def build_sla_visor(outer):
    """Build Part 2: Curved 3D SLA Clear Resin Visor (teo_kinh_sla, 1.8mm uniform)."""
    visor_prism = Rot(0, 90, 0) * extrude(
        Pos(-(58.5 + 60.0 / 2), 0, 45.0) * RectangleRounded(60.0, 70.0, 8.8),
        amount=20.0,
    )
    visor = (outer - Pos(-1.8, 0, 0) * outer) & visor_prism
    # 45-deg chamfered Ø6.5mm camera aperture at (Y=0, Z=Z_CAM)
    cam_hole = Pos(50.0, 0, Z_CAM) * Rot(0, 90, 0) * Cylinder(
        3.25, 12.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    cam_chamfer = Pos(56.5, 0, Z_CAM) * Rot(0, 90, 0) * Cone(
        3.25, 5.05, 1.8, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    return visor - cam_hole - cam_chamfer


def build_speaker_cap():
    """Build Part 7: Sealed 3W Speaker Chamber Back Cap (teo_nap_hop_loa)."""
    flange = Cylinder(18.0, 1.8, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # Anti-rotation bottom flat D-cut clearing IP2326 wires below!
    flange -= Pos(0, -19.0, -0.5) * Box(36.0, 7.0, 3.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    plug = Pos(0, 0, 1.8) * Cylinder(16.65, 2.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    cap = flange + plug
    # 1.0mm EVA foam gasket groove
    gasket = Pos(0, 0, 1.8) * (
        Cylinder(15.6, 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
        - Cylinder(13.6, 1.1, align=(Align.CENTER, Align.CENTER, Align.MIN))
    )
    # Notched wire grommet channel at top edge
    wire_notch = Pos(0, 15.5, -0.2) * Box(
        3.6, 6.0, 4.5, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    return cap - gasket - wire_notch


def build_arm():
    """Build Part 5: Minimalist Rounded Paddle Arm (teo_tay_robot, print x2)."""
    # Smooth fin along Z in [-44.0, +8.5], X in [-8.5, +8.5], Y in [0.0, 8.0]
    sk = Pos(0, 0, 0) * Rot(90, 0, 0) * Pos(0, -17.75, -8.0) * RectangleRounded(17.0, 52.5, 8.4)
    arm = extrude(sk, amount=8.0)
    outer_edges = arm.edges().filter_by_position(Axis.Y, 7.8, 8.2)
    arm = fillet(outer_edges, radius=2.8)

    # Inner MG90S single-arm servo horn pocket (Y = 0..3.2mm)
    hub_rec = Pos(0, -0.1, 0) * Rot(-90, 0, 0) * Cylinder(
        4.0, 3.3, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    horn_slot = Pos(0, 1.5, -8.5) * Box(
        4.5, 3.2, 17.0, align=(Align.CENTER, Align.CENTER, Align.CENTER)
    )
    m2_thru = Pos(0, -0.5, 0) * Rot(-90, 0, 0) * Cylinder(
        1.25, 10.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    cap_seat = Pos(0, 5.6, 0) * Rot(-90, 0, 0) * Cylinder(
        5.45, 3.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    return arm - hub_rec - horn_slot - m2_thru - cap_seat


def build_arm_cap():
    """Build Part 9: Shoulder Screw Cap (teo_nap_chup_tay, print x2)."""
    cap = Cylinder(5.3, 1.2, align=(Align.CENTER, Align.CENTER, Align.MIN))
    plug = Pos(0, 0, 1.2) * Cylinder(5.1, 1.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    top_e = cap.edges().filter_by_position(Axis.Z, -0.1, 0.1)
    cap = fillet(top_e, radius=0.5)
    return cap + plug


def build_omni_hub():
    """Build Part 10: MG90S Cross-Horn to Nexus 14108 Omni Wheel Hub (teo_hub_banh_omni, print x3)."""
    # Inner flange (Ø21.0 x 2.45mm, u=42.8..45.25) + Barrel (Ø13.80 x 23.5mm, u=45.25..68.75) -> Wheel center u=58.00!
    flange = Cylinder(10.5, 2.45, align=(Align.CENTER, Align.CENTER, Align.MIN))
    barrel = Pos(0, 0, 2.45) * Cylinder(6.90, 23.5, align=(Align.CENTER, Align.CENTER, Align.MIN))
    hub = flange + barrel
    for k in range(6):
        ang = k * 60.0
        rib = Rot(0, 0, ang) * Pos(6.85, 0, 2.45) * Cylinder(
            0.20, 21.5, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        hub += rib

    # Female MG90S 4-arm cross-horn lock pocket on bottom face (Z = 0..1.8mm)
    cross_1 = Pos(0, 0, -0.1) * Box(20.0, 4.3, 1.9, align=(Align.CENTER, Align.CENTER, Align.MIN))
    cross_2 = Pos(0, 0, -0.1) * Box(4.3, 20.0, 1.9, align=(Align.CENTER, Align.CENTER, Align.MIN))
    boss_clear = Pos(0, 0, -0.1) * Cylinder(4.1, 2.4, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # Ø6.2mm screwdriver tunnel all the way through for M2 center shaft screw!
    driver_bore = Pos(0, 0, -0.5) * Cylinder(3.1, 27.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # 4x Ø1.7mm pilot holes on cross arms (R = 7.0mm) for optional M1.7/M2 horn locking screws
    lock_holes = None
    for k in range(4):
        rad = math.radians(k * 90.0)
        h = Pos(7.0 * math.cos(rad), 7.0 * math.sin(rad), 1.5) * Cylinder(
            0.85, 6.0, align=(Align.CENTER, Align.CENTER, Align.MIN)
        )
        lock_holes = h if lock_holes is None else (lock_holes + h)

    return hub - cross_1 - cross_2 - boss_clear - driver_bore - lock_holes


def build_servo_clamp():
    """Build Part 11: Universal MG90S Vertical Top-Clamp Strap (teo_nep_giu_servo, print x5)."""
    strap = extrude(RectangleRounded(36.0, 7.6, 3.2), amount=3.0)
    for sx in (-15.0, 15.0):
        strap -= Pos(sx, 0, -0.5) * Cylinder(1.45, 4.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return strap


def save_part(part, stem: str):
    """Export both STEP and high-precision binary STL, and report volume/solids."""
    STEP_DIR.mkdir(parents=True, exist_ok=True)
    stl_path = OUT_DIR / f"{stem}.stl"
    step_path = STEP_DIR / f"{stem}.step"
    export_stl(part, str(stl_path), tolerance=0.025, angular_tolerance=0.12)
    export_step(part, str(step_path))
    n_solids = len(part.solids())
    vol_cm3 = part.volume / 1000.0
    bb = part.bounding_box()
    print(
        f"  [OK] {stem:22s} | solids={n_solids} | vol={vol_cm3:6.2f} cm^3 | "
        f"X=[{bb.min.X:6.1f},{bb.max.X:6.1f}] Y=[{bb.min.Y:6.1f},{bb.max.Y:6.1f}] Z=[{bb.min.Z:5.1f},{bb.max.Z:5.1f}]"
    )


def main():
    print("Building Master B-Rep Pod Shells...")
    outer, inner, shell = build_master_shells()

    parts = [
        ("teo_than_duoi", build_lower_chassis(outer, inner, shell)),
        ("teo_vach_ngan", build_bulkhead()),
        ("teo_than_tren", build_upper_shell(outer, inner, shell)),
        ("teo_khay_linh_kien", build_tray()),
        ("teo_mu_dau", build_head_dome(outer, inner, shell)),
        ("teo_kinh_sla", build_sla_visor(outer)),
        ("teo_nap_hop_loa", build_speaker_cap()),
        ("teo_tay_robot", build_arm()),
        ("teo_nap_chup_tay", build_arm_cap()),
        ("teo_hub_banh_omni", build_omni_hub()),
        ("teo_nep_giu_servo", build_servo_clamp()),
    ]

    print("Exporting 11 STL + 11 STEP CAD files...")
    for stem, p in parts:
        save_part(p, stem)
    print("All 11 CAD v10 parts generated successfully!")


if __name__ == "__main__":
    main()
