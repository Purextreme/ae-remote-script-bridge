import datetime as dt
import json
import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import capture_preview
import send_to_ae
from run_context import create_run_context, prune_run_contexts


class BridgeClientTests(unittest.TestCase):
    def test_run_context_uses_unique_directories(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            first = create_run_context(temp_dir)
            second = create_run_context(temp_dir)

            self.assertNotEqual(first.run_id, second.run_id)
            self.assertNotEqual(first.run_dir, second.run_dir)
            self.assertTrue(first.temp_dir.is_dir())
            self.assertTrue(second.temp_dir.is_dir())

    def test_wait_for_result_rejects_mismatched_run_id(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result_path = Path(temp_dir) / "result.json"
            result_path.write_text('{"runId":"stale"}', encoding="utf-8")

            with patch("send_to_ae.time.sleep"):
                with self.assertRaisesRegex(RuntimeError, "did not match"):
                    send_to_ae.wait_for_result(
                        result_path,
                        time.monotonic() + 0.01,
                        "current",
                    )

    def test_subprocess_timeout_is_reported(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result_path = Path(temp_dir) / "result.json"
            with patch(
                "send_to_ae.subprocess.run",
                side_effect=subprocess.TimeoutExpired(["AfterFX.com"], 1),
            ):
                with self.assertRaisesRegex(RuntimeError, "timed out during test"):
                    send_to_ae.run_afterfx_script(
                        Path("AfterFX.com"),
                        Path("test.jsx"),
                        result_path,
                        "test",
                        timeout_seconds=1,
                    )

    def test_expired_operation_state_is_removed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "protection_state.json"
            state_path.write_text(
                json.dumps(
                    {
                        "expired": {
                            "createdAt": (
                                dt.datetime.now() - dt.timedelta(days=2)
                            ).isoformat(timespec="seconds")
                        },
                        "current": {
                            "createdAt": dt.datetime.now().isoformat(
                                timespec="seconds"
                            )
                        },
                    }
                ),
                encoding="utf-8",
            )

            with patch.object(send_to_ae, "PROTECTION_STATE_PATH", state_path):
                state = send_to_ae.load_protection_state()

            self.assertNotIn("expired", state)
            self.assertIn("current", state)
            persisted = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(["current"], list(persisted))

    def test_prune_run_contexts_keeps_requested_count(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            for _ in range(4):
                create_run_context(temp_dir)

            prune_run_contexts(temp_dir, keep_runs=2)

            runs_root = Path(temp_dir) / "logs" / "runs"
            self.assertEqual(2, len([path for path in runs_root.iterdir()]))

    def test_ffmpeg_timeout_becomes_warning(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "preview.mp4"
            with patch("capture_preview.shutil.which", return_value="ffmpeg"):
                with patch(
                    "capture_preview.subprocess.run",
                    side_effect=subprocess.TimeoutExpired(["ffmpeg"], 1),
                ):
                    warning = capture_preview.assemble_preview_video(
                        video_path,
                        4,
                        timeout_seconds=1,
                    )

            self.assertIn("timed out after 1 seconds", warning)

    def test_render_queue_capture_restores_comp_time(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            jsx = capture_preview.build_render_queue_capture_jsx(
                "capture",
                "middle",
                None,
                temp_path / "result.json",
                temp_path,
            )

            self.assertIn("originalTime = comp.time", jsx)
            self.assertGreaterEqual(jsx.count("comp.time = originalTime"), 2)

    def test_negative_preview_edges_are_rejected(self):
        arguments = [
            ["send_to_ae.py", "test.jsx", "--capture-max-edge", "-1"],
            ["send_to_ae.py", "test.jsx", "--capture-video-max-edge", "-1"],
        ]
        for argv in arguments:
            with self.subTest(option=argv[2]):
                with patch("send_to_ae.sys.argv", argv):
                    with patch("send_to_ae.resolve_afterfx_path") as resolve:
                        self.assertEqual(1, send_to_ae.main())
                        resolve.assert_not_called()


if __name__ == "__main__":
    unittest.main()
