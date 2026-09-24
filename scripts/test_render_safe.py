import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from render_safe import render_safe
from push_test import push_image


class SafeRenderTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.output = Path(self.directory.name) / "display.webp"
        self.snapshot = Path(self.directory.name) / "snapshot.json"
        self.output.write_bytes(b"previous display")
        self.calls = []

    def fake_run(self, command, **kwargs):
        values = json.loads(Path(command[command.index("-c") + 1]).read_text())
        self.calls.append(values)
        Path(command[command.index("-o") + 1]).write_bytes(b"rendered display")
        self.assertEqual(kwargs["env"]["PIXLET_HTTP_TIMEOUT"], "8s")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    def run_fallback(self, failure):
        def run(command, **kwargs):
            values = json.loads(Path(command[command.index("-c") + 1]).read_text())
            if "debug_offline" not in values:
                raise failure
            return self.fake_run(command, **kwargs)

        with patch("render_safe.subprocess.run", side_effect=run):
            return render_safe({"lang": "en"}, self.output, self.snapshot)

    def test_timeout_uses_snapshot_without_refreshing_it(self):
        original = {"data": {"stopPlace": {"id": "test"}}, "saved": 123}
        self.snapshot.write_text(json.dumps(original))
        self.assertEqual(self.run_fallback(subprocess.TimeoutExpired("pixlet", 20)), "fallback")
        self.assertEqual(json.loads(self.calls[0]["debug_snapshot"]), original)
        self.assertEqual(json.loads(self.snapshot.read_text()), original)
        self.assertEqual(self.calls[0]["lang"], "en")

    def test_first_run_failure_renders_no_data(self):
        self.assertEqual(self.run_fallback(subprocess.CalledProcessError(1, "pixlet")), "fallback")
        self.assertEqual(json.loads(self.calls[0]["debug_snapshot"]), {})
        self.assertEqual(self.calls[0]["debug_offline"], "true")
        self.assertEqual(self.output.read_bytes(), b"rendered display")

    def test_corrupt_cache_renders_no_data(self):
        self.snapshot.write_text("invalid JSON")
        self.run_fallback(subprocess.CalledProcessError(1, "pixlet"))
        self.assertEqual(json.loads(self.calls[0]["debug_snapshot"]), {})

    def test_http_error_screen_without_export_uses_disk_fallback(self):
        with patch("render_safe.subprocess.run", side_effect=self.fake_run):
            self.assertEqual(render_safe({}, self.output, self.snapshot), "fallback")
        self.assertEqual(len(self.calls), 2)

    def test_success_persists_snapshot_and_image(self):
        snapshot = {"saved": 123, "data": {"stopPlace": {}}}

        def run(command, **kwargs):
            result = self.fake_run(command, **kwargs)
            result.stdout = "[collettsbus.star] COLLETTS_SNAPSHOT=" + json.dumps(snapshot)
            return result

        with patch("render_safe.subprocess.run", side_effect=run):
            self.assertEqual(render_safe({}, self.output, self.snapshot), "live")
        self.assertEqual(json.loads(self.snapshot.read_text()), snapshot)
        self.assertEqual(self.output.read_bytes(), b"rendered display")

    def test_failed_offline_render_preserves_output(self):
        with patch("render_safe.subprocess.run", side_effect=subprocess.CalledProcessError(1, "pixlet")):
            with self.assertRaises(subprocess.CalledProcessError):
                render_safe({}, self.output, self.snapshot)
        self.assertEqual(self.output.read_bytes(), b"previous display")

    def test_external_debug_keys_are_not_forwarded(self):
        with patch("render_safe.subprocess.run", side_effect=self.fake_run):
            render_safe({"debug_fixture": "normal", "debug_snapshot": "bad"}, self.output, self.snapshot)
        self.assertNotIn("debug_fixture", self.calls[0])
        self.assertNotIn("debug_snapshot", self.calls[0])


class PushTests(unittest.TestCase):
    def test_one_off_push_has_no_installation(self):
        with patch("push_test.requests.post") as post:
            post.return_value.status_code = 200
            push_image("test-device", b"image", "test-token")
        arguments = post.call_args.kwargs
        self.assertEqual(post.call_args.args[0], "https://api.tidbyt.com/v0/devices/test-device/push")
        self.assertEqual(arguments["json"]["installationID"], "")
        self.assertFalse(arguments["json"]["background"])
        self.assertEqual(arguments["json"]["image"], "aW1hZ2U=")
        self.assertFalse(arguments["allow_redirects"])

    def test_api_failure_does_not_expose_response_or_key(self):
        with patch("push_test.requests.post") as post:
            post.return_value.status_code = 401
            post.return_value.text = "sensitive response"
            with self.assertRaises(RuntimeError) as caught:
                push_image("test-device", b"image", "test-token")
        self.assertIn("401", str(caught.exception))
        self.assertNotIn("test-token", str(caught.exception))
        self.assertNotIn("sensitive response", str(caught.exception))


if __name__ == "__main__":
    unittest.main()