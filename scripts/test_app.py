"""Execute assertions against app helpers in the real Starlark runtime."""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class AppLogicTests(unittest.TestCase):
    def test_starlark_logic(self):
        source = (ROOT / "apps/collettsbus/collettsbus.star").read_text()
        anchor = "def main(config):\n"
        self.assertEqual(source.count(anchor), 1)
        source = source.replace(anchor, anchor + "    return run_logic_tests()\n", 1)
        assertions = (ROOT / "scripts/logic_test.star").read_text()
        with tempfile.TemporaryDirectory() as directory:
            app = Path(directory) / "logic.star"
            app.write_text(source + "\n" + assertions)
            result = subprocess.run(
                [os.environ.get("PIXLET", "pixlet"), "render", str(app), "-o", str(Path(directory) / "test.webp")],
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()