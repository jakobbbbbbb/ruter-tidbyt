# Copilot prompt: "Colletts gate → Sentrum" Tidbyt app

> Paste everything below the line into GitHub Copilot Chat in **Agent mode** from an empty repo folder. You can also save it as `.github/prompts/tidbyt-bus.prompt.md` and run it with `/tidbyt-bus`.

---

## Role and goal

You are a senior embedded-UI engineer who has shipped many apps for the **Tidbyt** 64×32 RGB LED matrix using **Pixlet** (Starlark). Build a production-quality Tidbyt app that shows live bus departures from **Colletts gate (Oslo)** toward **downtown (Sentrum)**, using Entur's open real-time API.

The app must look like it was designed for the pixel grid: crisp, glanceable from across the room, readable in under two seconds, and robust when the network or API misbehaves. Work in small, verifiable steps and run the Pixlet tooling after each step.

## Platform context (read before writing code)

- **Language:** Starlark, which looks like Python but is not Python. It has **no** `try/except`, `while` loops, recursion, classes, f-strings, `import`, sets, or `**kwargs` unpacking into widgets. Use `load()`, `for` loops over finite ranges, `"%s" % x` or `.format()`, and explicit status-code checks. If you catch yourself writing Python-only syntax, stop and rewrite it.
- **Runtime modules to use:** `render.star`, `schema.star`, `http.star`, `time.star`, `encoding/json.star`, `cache.star` (only if `http` `ttl_seconds` is not enough), `humanize.star` (optional).
- **Entry points:** `def main(config):` returns `render.Root(...)`; `def get_schema():` returns `schema.Schema(version = "1", fields = [...])`.
- **Display:** 64×32 px. Design for that size. If the runtime exposes the canvas size (some newer Pixlet builds do), read it and scale the layout, but 64×32 must remain the reference layout.
- **Tooling (macOS, Homebrew):** Install with `brew install pixlet`. If that formula is not available, use the Tronbyt fork (`github.com/tronbyt/pixlet`) or the upstream `tidbyt/pixlet` release binary. Tidbyt's team joined Modal in 2024, and the community-maintained **Tronbyt** fork of Pixlet and the apps repo is where active development now happens. Write code that runs on both.
- **Commands you will use:** `pixlet serve <app>.star` (live preview at http://localhost:8080), `pixlet render <app>.star [key=value ...]`, `pixlet lint`, `pixlet format`, `pixlet check` (if available in the installed version), `pixlet push <DEVICE_ID> <file>.webp [--installation-id <id>]`. Run `pixlet --help` first and adapt to the commands that actually exist.
## Data source: Entur Journey Planner v3 (GraphQL)

- **Endpoint:** `POST https://api.entur.io/journey-planner/v3/graphql`
- **Required header:** `ET-Client-Name: <github-username>-tidbyt-colletts` (Entur throttles or blocks clients that don't identify themselves). Also send `Content-Type: application/json`.
- **No API key** is needed.
- **Stop:** `Colletts gate, Oslo` = `NSR:StopPlace:6286`. There is also a *Colletts gate* in Drammen (`NSR:StopPlace:17176`). Never use that one.
- **Platforms (quays) at the Oslo stop:**
  - `NSR:Quay:11544`: platform **1**, compass bearing **193°** (southbound). **This is probably the downtown direction**, since Oslo sentrum lies due south.
  - `NSR:Quay:11545`: platform **2**, bearing **14°** (northbound).
- **Verify before hard-coding:** Write `scripts/probe_entur.py` (Python 3, `requests` only), which queries both quays for `lines { publicCode name }` and the next ~10 `estimatedCalls` with `destinationDisplay.frontText`. Print a table so the correct downtown quay and its destinations can be confirmed. Record the verified result in the README.
**Departures query:** use variables, not string concatenation.

```graphql
query Departures($quayId: String!, $n: Int!, $lines: [ID!]) {
  quay(id: $quayId) {
    id
    name
    publicCode
    situations { summary { value language } }
    estimatedCalls(
      numberOfDepartures: $n
      timeRange: 7200
      arrivalDeparture: departures
      includeCancelledTrips: true
      whiteListed: { lines: $lines }
    ) {
      aimedDepartureTime
      expectedDepartureTime
      realtime
      cancellation
      predictionInaccurate
      destinationDisplay { frontText }
      serviceJourney {
        line {
          id
          publicCode
          transportMode
          presentation { colour textColour }
        }
      }
      situations { summary { value language } }
    }
  }
}
```

If `whiteListed` with a null list causes an error, omit the argument when no line filter is set. Request a few more departures than you display (for example, 2× the rows) so filtering still leaves enough to show.

## Functional requirements

1. **Next departures.** Show the next *N* departures (default 3) from the downtown quay, sorted by `expectedDepartureTime`.
2. **Countdown formatting**, computed at render time against `time.now().in_location("Europe/Oslo")`:
   - `< 1 min` → `nå` (or `now` in English mode)
   - `1–14 min` → `N min` (compact form `Nm` if space is tight)
   - `≥ 15 min` → clock time `HH:MM` (24-hour)
   - Not real time (`realtime == false`): prefix with `ca.`, or dim the time color. Choose whichever reads better at 64×32 and document the choice.
3. **Walking-time awareness.** A `walk_minutes` config (default 2). Hide departures you can no longer reach. Colour-code the rest by urgency: time to leave now → amber, comfortable → white/green, delayed more than 2 min vs. aimed → a subtle red delay dot or `+N`.
4. **Line badges.** Draw the line number in a solid rectangle using Entur's `presentation.colour`/`textColour`. If those are missing, fall back to Ruter bus red `#E60000` with white text. Right-align the text inside a fixed-width badge so rows line up.
5. **Destinations.** Show `frontText`, abbreviated smartly (for example, `Jernbanetorget` → `Jernbanetorg.`). If the text still doesn't fit, use `render.Marquee` on that row only. Never marquee more than one row at a time.
6. **Cancellations.** Keep cancelled departures visible but marked (red "INNSTILT"/"CANCELLED", or a struck-through, dimmed row), and don't count them toward "next bus".
7. **Service disruptions (avvik).** If there are quay- or call-level `situations`, show a thin warning glyph in the header. Optionally scroll the Norwegian or English summary on a final animation frame, controlled by a `show_disruptions` toggle.
8. **Header.** A 1-line header such as `COLLETTS GT → SENTRUM`, or a compact pictogram plus a short label, with an optional small clock on the right (`show_clock` toggle).
9. **Empty, error, and stale states.** Each needs its own clear screen:
   - HTTP error or timeout: show the last good data (from the `http` cache/`cache` module) with a small "stale" indicator. If there's nothing cached, show a friendly `Ingen data` / `No data` screen with an icon. Never crash and never show a blank screen.
   - No departures in the next 2 hours (night): show `Ingen avganger` plus the first departure time if one is known.
10. **Language.** `lang` option: `no` (default) or `en`, for all UI strings.
## Configuration schema (`get_schema`)

Provide sensible defaults so the app works with zero configuration:

- `stop`: a `schema.Typeahead` backed by a handler that calls Entur's geocoder (`https://api.entur.io/geocoder/v1/autocomplete?text=...&layers=venue&size=10`) and returns `NSR:StopPlace:*` options with labels like `Colletts gate, Oslo`. Default: `NSR:StopPlace:6286`.
- `quay`: a dropdown or generated field listing quays for the selected stop, labelled by platform code plus a direction hint (bearing → N/S/E/W, or the most common destination). Default: the verified downtown quay.
- `lines`: an optional comma-separated whitelist (e.g. `37`); empty means all lines.
- `destination_filter`: an optional case-insensitive substring filter on `frontText`. This is an extra safety net for the "toward downtown" requirement.
- `rows`: 2, 3, or 4 (4 only if it stays legible).
- `walk_minutes`: 0–15.
- `lang`: `no` / `en`.
- `show_clock`, `show_disruptions`: toggles.
Validate and coerce every config value (ints from strings, clamped ranges). Bad config must fall back to defaults, never error.

## Visual design spec (64×32)

- **Grid:** 8 px header plus 3 × 8 px rows, as the default. Use 1 px of spacing wisely; mockups are drawn on the pixel grid, not in points.
- **Fonts:** use built-in Pixlet fonts only. Start with `tom-thumb` (compact) for rows and `tb-8` or `CG-pixel-3x5-mono` for the header or numbers. Compare two or three combos by rendering them, then pick one and justify it in the README.
- **Suggested columns per row:** `[badge ~11px][gap 2px][destination, flexible][gap][time, right-aligned ~16px]`. Use `render.Row(expanded = True, main_align = "space_between")` or fixed-width `render.Box`es so columns don't jitter.
- **Palette:** black background. Use a restrained palette of white, one amber, one red, a dim grey for secondary info, and line colours. No gradients or glow effects that turn to mush on LEDs. Check contrast: very dark blues and purples are nearly invisible on a real panel.
- **Motion:** at most one subtle motion element (a marquee *or* a blinking "nå"). Set `render.Root(delay = ..., max_age = ...)` appropriately. Keep total animation ≤ 15 s so it fits a normal rotation slot. Use `show_full_animation` only if it is justified.
- **Polish:** a tiny 5×5 or 7×7 bus pictogram drawn with `render.Box`es or a small embedded base64 PNG, consistent alignment on the baseline, no text touching the panel edge (≥ 1 px margin).
## Engineering requirements

- **Structure:**
```
  apps/collettsbus/
    collettsbus.star     # the app
    manifest.yaml        # id, name, summary, desc, author (community-apps format)
    README.md            # screenshots, config, design decisions, verified quay
    screenshots/         # rendered .webp/.gif of every state
  scripts/
    probe_entur.py       # quay/line verification
    render_states.sh     # renders all states via pixlet render with config overrides
  .github/workflows/ci.yml  # installs pixlet, runs format --dry-run/lint/check/render
```
- **Code quality:** small pure helper functions (`fetch_departures`, `parse_calls`, `format_countdown`, `badge`, `row`, `header`, `error_screen`). Constants at the top (IDs, colours, fonts, TTLs). No magic numbers buried in the layout. Clear comments on anything that is Starlark-specific.
- **Network hygiene:** one HTTP call per render, `ttl_seconds = 30` on the request (real-time data), a timeout, the `ET-Client-Name` header, and a check of `resp.status_code` and GraphQL `errors` before reading `data`.
- **Time handling:** parse ISO-8601 with `time.parse_time`. Do all maths in `Europe/Oslo`, and make sure DST transitions and midnight rollover (departure after 00:00) work correctly.
- **Deterministic testing:** add a hidden `debug_fixture` config key that makes `main` use an embedded JSON fixture instead of the network, with fixtures for: normal, crowded (long names), realtime missing, cancellation, delay, disruption, empty/night, and HTTP error. `render_states.sh` renders each fixture to `screenshots/`.
- **Checks that must pass:** `pixlet format` (no diff), `pixlet lint`, `pixlet check` if available, and a render of every fixture without errors.
## Process

1. Run `pixlet version` and `pixlet --help`, and tell me which Pixlet build and commands are available.
2. Write and run `scripts/probe_entur.py`. Show me the lines and destinations per quay and confirm the downtown quay before continuing.
3. Scaffold the app, then build the happy path with the fixture and render it.
4. Add live data, then error, empty, and stale handling, then the schema.
5. Render all states, inspect each image, and iterate on the pixel layout at least twice (alignment, truncation, contrast).
6. Write the README with screenshots, and finish with the exact commands to preview (`pixlet serve`), render, and push to my device (`pixlet devices` → `pixlet push ...`).
Ask me only when something is genuinely ambiguous (for example, the probe shows both quays serve downtown destinations). Otherwise make a sensible decision, note it in the README, and keep going.