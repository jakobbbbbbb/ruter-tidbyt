#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
app=apps/collettsbus/collettsbus.star
output=apps/collettsbus/screenshots
mkdir -p "$output"
for state in normal crowded realtime_missing cancellation all_cancelled delay disruption empty http_error stale malformed multimodal typography; do
  pixlet render "$app" "debug_fixture=$state" -o "$output/$state.webp"
done
pixlet render "$app" debug_fixture=now walk_minutes=0 -o "$output/now.webp"
pixlet render "$app" debug_fixture=normal rows=2 show_clock=true -o "$output/two_pages_clock.webp"
pixlet render "$app" debug_fixture=multimodal rows=4 quay=all -o "$output/four_pages.webp"
pixlet render "$app" debug_fixture=normal layout=board -o "$output/board.webp"
pixlet render "$app" debug_fixture=normal rows=2 show_clock=true layout=board -o "$output/two_rows_clock.webp"
pixlet render "$app" debug_fixture=multimodal rows=4 quay=all layout=board -o "$output/four_rows.webp"
pixlet render "$app" debug_fixture=http_error lang=en -o "$output/error_en.webp"
pixlet render "$app" debug_fixture=empty lang=en -o "$output/empty_en.webp"
pixlet render "$app" debug_fixture=disruption lang=en -o "$output/disruption_en.webp"
pixlet render "$app" debug_fixture=normal rows=oops walk_minutes=invalid show_clock=invalid stop='{bad' -o "$output/bad_config.webp"