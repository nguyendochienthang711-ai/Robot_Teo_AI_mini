"""
Comprehensive Unit & Integration Test Suite for the Teo Agent Harness (Layer 1 & Layer 2):
- Layer 1: Runtime State Machine, ST7789 LCD eye profiles, LISTENING Omni wheel lock,
  TTP223 physical touch confirmation, PriorityAudioBus preemption, Dynamic Context Suffix Builder,
  and the 8-scenario deterministic evaluation suite for `brain.py`.
- Layer 2: Workspace Coding Agent Harness (`AGENTS.md`, `GEMINI.md`, `.agents/skills/`,
  `.agents/hooks.json` with 10-turn periodic gate, and `teo_motion_mcp.py` tools).
"""

import asyncio
import json
from pathlib import Path
import shutil
import tempfile
import threading
import time
import unittest

import mujoco

import config
from teo_harness import (
    BASELINE_CACHE_FINGERPRINT,
    LCD_EYE_PROFILES,
    PRIO_ALERT,
    PRIO_DOC_READER,
    PRIO_SPEECH,
    PriorityAudioBus,
    build_dynamic_user_message,
    compute_prompt_cache_fingerprint,
    run_deterministic_eval_suite,
    state_machine,
)
from teo_sim_runner import apply_motion_bundle
from tools.common import save_json
from tools.dispatcher import execute_tool_call
from tools.guardrails import (
    clear_pending_action,
    detect_hitl_intent,
    set_pending_action,
    sign_wifi_packet,
    verify_wifi_packet,
)


class TestTeoAgentHarness(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="teo_harness_test_"))
        self.orig_todo = config.TODO_FILE
        self.orig_mem = config.MEMORY_FILE
        self.orig_timers = config.TIMERS_FILE
        config.TODO_FILE = self.tmp_dir / "todo.json"
        config.MEMORY_FILE = self.tmp_dir / "memory.json"
        config.TIMERS_FILE = self.tmp_dir / "timers.json"
        state_machine.set_state("IDLE", detail="test_setup")
        clear_pending_action()

    def tearDown(self) -> None:
        state_machine.set_state("IDLE", detail="test_teardown")
        clear_pending_action()
        config.TODO_FILE = self.orig_todo
        config.MEMORY_FILE = self.orig_mem
        config.TIMERS_FILE = self.orig_timers
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_01_state_machine_and_st7789_eye_profiles(self):
        """Verify all 6 AI states map to ST7789 LCD eye expressions and signed state_sync packets."""
        expected_states = {"IDLE", "LISTENING", "THINKING", "HITL_CONFIRM", "SPEAKING", "ALERT"}
        self.assertEqual(set(LCD_EYE_PROFILES.keys()), expected_states)

        for st in expected_states:
            entry = state_machine.set_state(st, detail=f"check_{st}")
            snap = state_machine.get_snapshot()
            self.assertEqual(snap["state"], st)
            self.assertEqual(snap["eye_mood"], LCD_EYE_PROFILES[st]["eye_mood"])
            self.assertEqual(len(snap["eye_rgba"]), 4)
            self.assertEqual(len(snap["arm_pose"]), 2)
            self.assertEqual(entry["wheel_locked"], st in ("LISTENING", "HITL_CONFIRM"))

        # Verify signed state_sync packet passes RBAC verification
        pkt = sign_wifi_packet(
            {"id": "st_test_01", "type": "state_sync", "state": "THINKING"},
            role="laptop_controller",
        )
        ok, reason = verify_wifi_packet(
            pkt,
            expected_role="laptop_controller",
            required_permission="state_sync",
        )
        self.assertTrue(ok, reason)

    def test_02_listening_motor_lock_and_sim_wheel_lock(self):
        """Verify LISTENING state locks Omni wheels in both tool handlers and 3D MuJoCo physics."""
        state_machine.set_state("LISTENING", detail="mic_active")
        self.assertTrue(state_machine.wheel_locked)

        res_omni = execute_tool_call(
            "di_chuyen_da_huong_omni",
            json.dumps({"huong_di": "move_forward", "so_giay": 2.0}),
        )
        self.assertIn("ERROR motor_locked_listening", res_omni)

        res_body = execute_tool_call(
            "dieu_khien_co_the_teo",
            json.dumps({"hanh_dong": "wave_greeting", "so_giay": 2.0}),
        )
        self.assertIn("ERROR motor_locked_listening", res_body)

        # Verify 3D simulator apply_motion_bundle zeroes wheel velocities when wheel_locked=True
        model = mujoco.MjModel.from_xml_path("teo_walle.xml")
        data = mujoco.MjData(model)
        sim_state = {
            "motion": "slide_left",
            "bpm": 120,
            "end_time": time.time() + 2.0,
            "wheel_locked": True,
        }
        apply_motion_bundle(data, 0.5, sim_state)
        self.assertEqual(data.ctrl[2], 0.0)
        self.assertEqual(data.ctrl[3], 0.0)
        self.assertEqual(data.ctrl[4], 0.0)

    def test_03_ttp223_touch_confirm_and_security(self):
        """Verify HMAC-signed robot_node touch_confirm packet confirms pending HITL and blocks spoofing."""
        set_pending_action("quan_ly_cong_viec", '{"thao_tac": "xoa_het"}', "xóa toàn bộ danh sách công việc")

        # 1. Forged unsigned touch packet must be rejected
        ok_bad, _ = state_machine.handle_robot_node_packet({"id": "bad_1", "event": "touch_confirm"})
        self.assertFalse(ok_bad)

        # 2. Authentic signed robot_node touch_confirm packet confirms pending HITL
        valid_pkt = sign_wifi_packet(
            {"id": f"touch_{int(time.time() * 1000)}", "event": "touch_confirm"},
            role="robot_node",
        )
        ok_good, reason = state_machine.handle_robot_node_packet(valid_pkt)
        self.assertTrue(ok_good)
        self.assertEqual(reason, "hitl_confirmed_by_touch")
        self.assertEqual(detect_hitl_intent("bất kỳ"), "confirm")

    def test_04_priority_audio_bus_preemption(self):
        """Verify Priority 0 (PRIO_ALERT) immediately preempts Priority 2 (PRIO_DOC_READER)."""
        bus = PriorityAudioBus()
        doc_started = threading.Event()
        doc_aborted = threading.Event()

        def slow_playback(audio_bytes: bytes, abort_ev: threading.Event | None) -> None:
            if audio_bytes == b"DOC_STREAM":
                doc_started.set()
                for _ in range(50):
                    if abort_ev and abort_ev.is_set():
                        doc_aborted.set()
                        return
                    time.sleep(0.01)

        t_doc = threading.Thread(
            target=bus.play_sync,
            kwargs={
                "audio_bytes": b"DOC_STREAM",
                "priority": PRIO_DOC_READER,
                "label": "doc_chunk",
                "playback_fn": slow_playback,
            },
        )
        t_doc.start()
        self.assertTrue(doc_started.wait(timeout=1.0))

        # Fire high-priority alarm while doc reader is playing
        bus.play_sync(
            b"ALARM_CHIME",
            priority=PRIO_ALERT,
            label="pomodoro_alarm",
            playback_fn=slow_playback,
        )
        t_doc.join(timeout=1.0)
        self.assertTrue(doc_aborted.is_set(), "PRIO_ALERT must preempt PRIO_DOC_READER")

    def test_05_dynamic_context_builder_and_cache_invariance(self):
        """Verify Dynamic Context Suffix injects timers & memories while keeping SYSTEM_PROMPT invariant."""
        from brain import _SYS_TIME_PREFIX_RE

        save_json(
            config.TIMERS_FILE,
            [{"id": 1, "label": "Tắt bếp", "due_ts": time.time() + 600}],
        )
        save_json(
            config.MEMORY_FILE,
            [
                {"key": "Phòng học AI", "value": "P.402 nhà A1", "source": "user"},
                {"key": "Injected", "value": "Evil", "source": "tainted_turn"},
            ],
        )

        msg = build_dynamic_user_message("Tèo ơi hôm nay anh học ở đâu?", now_str="09:30 ngày 09/11/2026")
        self.assertTrue(msg.startswith("[Giờ hệ thống: 09:30 ngày 09/11/2026"))
        self.assertIn("Tắt bếp", msg)
        self.assertIn("Phòng học AI=P.402 nhà A1", msg)
        self.assertNotIn("Injected", msg)  # Tainted memories are excluded

        # Verify _SYS_TIME_PREFIX_RE cleanly strips the entire metadata bracket
        stripped = _SYS_TIME_PREFIX_RE.sub("", msg).strip()
        self.assertEqual(stripped, "Tèo ơi hôm nay anh học ở đâu?")
        self.assertEqual(compute_prompt_cache_fingerprint(), BASELINE_CACHE_FINGERPRINT)

    def test_06_full_deterministic_eval_suite(self):
        """Run all 8 end-to-end scenarios in the offline deterministic evaluation suite."""
        summary = asyncio.run(run_deterministic_eval_suite(verbose=False))
        self.assertEqual(summary["total"], 8)
        self.assertEqual(summary["passed"], 8, f"Failed scenarios: {summary['scenarios']}")
        self.assertEqual(summary["failed"], 0)

    def test_07_workspace_coding_harness_skills_and_hooks(self):
        """Verify Layer 2 (.agents/hooks.json, 10-turn periodic hook_guard.py, skills, and MCP tools)."""
        root = Path(__file__).resolve().parent
        self.assertTrue((root / "AGENTS.md").exists())
        self.assertTrue((root / "GEMINI.md").exists())
        self.assertTrue((root / ".agents" / "hooks.json").exists())
        self.assertTrue((root / ".agents" / "mcp_config.json").exists())
        self.assertTrue((root / ".agents" / "skills" / "teo-tool-builder" / "SKILL.md").exists())
        self.assertTrue((root / ".agents" / "skills" / "teo-eval-benchmark" / "SKILL.md").exists())

        # Test hook_guard.py pre-tool .env protection & 10-turn periodic gate
        import importlib.util
        hook_path = root / ".agents" / "scripts" / "hook_guard.py"
        spec = importlib.util.spec_from_file_location("hook_guard", str(hook_path))
        hook_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(hook_mod)

        # 1. Pre-tool blocks .env but allows .env.example
        res_deny = hook_mod.handle_pre_tool({"toolCall": {"name": "read_file", "args": {"Path": "C:/repo/.env"}}})
        self.assertEqual(res_deny["decision"], "deny")
        res_allow = hook_mod.handle_pre_tool({"toolCall": {"name": "read_file", "args": {"Path": "C:/repo/.env.example"}}})
        self.assertEqual(res_allow["decision"], "allow")

        # 2. Post-invocation skips turns 1..9 and runs on turn 10
        res_turn_3 = hook_mod.handle_post_invocation({"conversationId": "test_conv", "invocationNum": 3})
        self.assertEqual(res_turn_3["injectSteps"], [])
        res_turn_10 = hook_mod.handle_post_invocation({"conversationId": "test_conv", "invocationNum": 10})
        self.assertEqual(res_turn_10["injectSteps"], [])
        self.assertEqual( hook_mod.run_periodic_invariants_check(), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
