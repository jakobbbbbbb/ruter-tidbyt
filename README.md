# ruter-tidbyt

Live Norwegian public-transport departures for a 64x32 Tidbyt or Tronbyt.
Search stations throughout Norway, with all transport modes supported by Entur.
The default is Colletts gate toward Sentrum in Oslo.

The living-room display uses large countdowns, full-width destinations, and calm
departure pages. A compact departure board is also available. Service advisory
pages and warning indicators are intentionally omitted.

![Departure display](apps/collettsbus/screenshots/normal.webp)

## Preview

```sh
brew install pixlet
pixlet serve apps/collettsbus/collettsbus.star --port 8080 --no-browser
```

Open <http://localhost:8080>.

See the [app guide](apps/collettsbus/README.md) for configuration, the eleven-design
comparison, tests, rendering, and device upload instructions.

## Publication

The target is the public Tidbyt app catalogue, via a reviewed pull request to
`tidbyt/community`. Tidbyt hosts accepted apps, so no personal server is needed.
This repository is the development source; pushing here alone does not publish
to the catalogue. CI validates with original Tidbyt Pixlet v0.34.0 and never
uploads to a device.

This is a **new listing**, named **Norway Departures**, with app ID
`norway-departures`. It does not replace the existing Norway Transport app.
The local source remains under `apps/collettsbus` to preserve development and
preview commands; the proposed community submission folder is `apps/norwaydepartures`.

Repository: <https://github.com/jakobbbbbbb/ruter-tidbyt>.
