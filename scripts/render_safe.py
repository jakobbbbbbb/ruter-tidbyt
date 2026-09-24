#!/usr/bin/env python3
"""Render departures with an atomic output and persistent offline fallback."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

APP = Path(__file__).resolve().parents[1] / "apps/collettsbus/collettsbus.star"
SNAPSHOT_PREFIX = "COLLETTS_SNAPSHOT="


def read_snapshot(path):
    try:
        value = json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def exported_snapshot(output):
    for line in output.splitlines():
        if SNAPSHOT_PREFIX in line:
            try:
                value = json.loads(line.partition(SNAPSHOT_PREFIX)[2])
            except ValueError:
                continue
            if isinstance(value, dict) and isinstance(value.get("data"), dict):
                return value
    return None


def render_safe(config, output, snapshot_path, pixlet="pixlet", timeout=20):
    config = {key: value for key, value in config.items() if not key.startswith("debug_")}
    output = Path(output).resolve()
    snapshot_path = Path(snapshot_path).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ, PIXLET_HTTP_TIMEOUT="8s")
    with tempfile.TemporaryDirectory(prefix=".colletts-", dir=output.parent) as directory:
        temporary = Path(directory)
        image = temporary / "render.webp"
        config_path = temporary / "config.json"

        def run(values):
            config_path.write_text(json.dumps(values))
            image.unlink(missing_ok=True)
            result = subprocess.run(
                [pixlet, "render", str(APP), "-c", str(config_path), "-o", str(image)],
                capture_output=True, text=True, timeout=timeout, env=environment,
                check=True,
            )
            if not image.is_file() or image.stat().st_size == 0:
                raise RuntimeError("Pixlet did not produce an image")
            return result.stdout

        fresh = None
        try:
            fresh = exported_snapshot(run(dict(config, debug_export="true")))
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, RuntimeError) as error:
            print(f"Live render failed ({type(error).__name__}); rendering offline.", file=sys.stderr)
        if fresh is None:
            snapshot = read_snapshot(snapshot_path)
            run(dict(config, debug_snapshot=json.dumps(snapshot), debug_offline="true"))
            outcome = "fallback"
        else:
            snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path = None
            try:
                with tempfile.NamedTemporaryFile(mode="w", dir=snapshot_path.parent, delete=False) as cache_file:
                    cache_path = Path(cache_file.name)
                    json.dump(fresh, cache_file)
                cache_path.replace(snapshot_path)
            finally:
                if cache_path is not None:
                    cache_path.unlink(missing_ok=True)
            outcome = "live"
        image.replace(output)
    return outcome


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, help="Pixlet JSON configuration")
    parser.add_argument("--output", type=Path, default=Path(".cache/departures.webp"))
    parser.add_argument("--snapshot", type=Path, default=Path(".cache/departures.json"))
    parser.add_argument("--pixlet", default="pixlet")
    args = parser.parse_args()
    try:
        config = json.loads(args.config.read_text()) if args.config else {}
        if not isinstance(config, dict):
            raise ValueError("Configuration must be a JSON object")
        outcome = render_safe(config, args.output, args.snapshot, pixlet=args.pixlet)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"Render failed; existing output was not replaced: {error}", file=sys.stderr)
        return 1
    print(f"Rendered {outcome} image: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())