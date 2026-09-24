#!/usr/bin/env python3
"""Render fresh departures and send a one-off test to an original Tidbyt."""

import argparse
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.parse import quote

import requests

from render_safe import render_safe


def push_image(device_id, image, api_key):
    response = requests.post(
        "https://api.tidbyt.com/v0/devices/%s/push" % quote(device_id, safe=""),
        headers={"Authorization": "Bearer " + api_key},
        json={
            "deviceID": device_id,
            "image": base64.b64encode(image).decode("ascii"),
            "installationID": "",
            "background": False,
        },
        timeout=20,
        allow_redirects=False,
    )
    if response.status_code != 200:
        detail = "Check the API key and device ID." if response.status_code in (401, 403, 404) else "Try again later."
        raise RuntimeError(f"Tidbyt returned HTTP {response.status_code}. {detail}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("device_id")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--dry-run", action="store_true", help="Render only; do not contact Tidbyt")
    args = parser.parse_args()
    api_key = os.environ.get("TIDBYT_API_KEY", "").strip()
    if not args.dry_run and not api_key:
        print("No API key found. Run this in the terminal where you entered TIDBYT_API_KEY.", file=sys.stderr)
        return 1
    try:
        config = json.loads(args.config.read_text()) if args.config else {}
        if not isinstance(config, dict):
            raise ValueError("Configuration must be a JSON object")
        output = Path(".cache/tidbyt-test.webp")
        outcome = render_safe(config, output, Path(".cache/departures.json"))
        if outcome != "live":
            raise RuntimeError("Live departures are unavailable. Nothing was sent; please retry.")
        if args.dry_run:
            print(f"Fresh test image rendered: {output}. Nothing sent to Tidbyt.")
            return 0
        push_image(args.device_id, output.read_bytes(), api_key)
    except requests.RequestException:
        print("Could not confirm the Tidbyt upload. Check connectivity before retrying.", file=sys.stderr)
        return 1
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"Test failed: {error}", file=sys.stderr)
        return 1
    print("Tidbyt accepted the one-off test. Your saved app rotation was not changed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())