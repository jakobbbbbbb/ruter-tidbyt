#!/usr/bin/env python3
"""Render the font study and validate the real app's pixel/animation bounds."""

import subprocess
from pathlib import Path
import shutil
import tempfile

from PIL import Image, ImageDraw, ImageSequence

ROOT = Path(__file__).resolve().parents[1]
SCREENSHOTS = ROOT / "apps/collettsbus/screenshots"
DESIGNS = [
    ("compact", "01  Compact / tom-thumb"),
    ("mono", "02  Compact / CG 3x5 mono"),
    ("board", "03  Board / tb-8"),
    ("quiet", "04  Quiet board / 5x8"),
    ("two_rows", "05  Two rows / 6x10"),
    ("focus", "06  Focus / tb-8 + 6x13"),
    ("rounded", "07  Focus / 6x10 rounded"),
    ("large", "08  Focus / 6x13"),
    ("platform", "09  Full-width / tb-8 [selected]"),
    ("platform_mono", "10  Full-width / 5x8"),
    ("platform_large", "11  Full-width / 6x10"),
]


def contact_sheet(items, output):
    sheet = Image.new("RGB", (1080, ((len(items) + 2) // 3) * 200), "#242827")
    draw = ImageDraw.Draw(sheet)
    for index, (path, caption) in enumerate(items):
        left, top = (index % 3) * 360, (index // 3) * 200
        draw.text((left + 12, top + 8), caption, fill="#f2f2e8")
        with Image.open(path) as image:
            frame = image.convert("RGB")
            sheet.paste(frame.resize((256, 128), Image.Resampling.NEAREST), (left + 12, top + 30))
            sheet.paste(frame, (left + 280, top + 78))
    sheet.save(output)


def validate_states():
    paths = sorted(SCREENSHOTS.glob("*.webp"))
    if not paths:
        raise RuntimeError("Run bash scripts/render_states.sh first")
    normal = (SCREENSHOTS / "normal.webp").read_bytes()
    for name in ("disruption", "disruption_en"):
        if (SCREENSHOTS / f"{name}.webp").read_bytes() != normal:
            raise AssertionError(f"{name}: advisories must not change departure pages")
    for path in paths:
        duration = 0
        with Image.open(path) as image:
            for index, frame in enumerate(ImageSequence.Iterator(image)):
                rgb = frame.convert("RGB")
                if rgb.size != (64, 32):
                    raise AssertionError(f"{path.name}, frame {index}: incorrect dimensions")
                if not rgb.getbbox():
                    raise AssertionError(f"{path.name}, frame {index}: blank display")
                for column in (0, 63):
                    if rgb.crop((column, 0, column + 1, 32)).getbbox():
                        raise AssertionError(f"{path.name}, frame {index}: missing side margin")
                duration += frame.info.get("duration", 0)
        if duration > 15000:
            raise AssertionError(f"{path.name}: animation exceeds 15 seconds ({duration} ms)")
        print(f"PASS {path.name}: 64x32, visible, side margins, {duration} ms")
    contact_sheet([(path, path.stem) for path in paths], SCREENSHOTS / "states.png")


def main():
    output = SCREENSHOTS / "designs"
    output.mkdir(parents=True, exist_ok=True)
    items = []
    with tempfile.TemporaryDirectory() as directory:
        study = Path(directory) / "design_study.star"
        shutil.copyfile(ROOT / "scripts/design_study.star", study)
        for name, caption in DESIGNS:
            path = output / f"{name}.webp"
            subprocess.run([
                "pixlet", "render", str(study),
                f"design={name}", "-o", str(path),
            ], check=True, cwd=ROOT)
            items.append((path, caption))
    contact_sheet(items, output / "comparison.png")
    validate_states()


if __name__ == "__main__":
    main()