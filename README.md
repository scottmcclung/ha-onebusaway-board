# OneBusAway Board

A Home Assistant integration that exposes a **departure board** for a
[OneBusAway](https://onebusaway.org/) transit stop — not just the single next
arrival, but the next several departures, each with its route, destination, live
departure time, real-time delay, and (optionally) its predicted arrival time at
one or more **downstream stops you care about**.

Built for a fixed, non-interactive wall dashboard: pick your origin platform and
your destination stations once, and every train on the board shows when it will
get you to each destination.

## What makes this different

Most OneBusAway integrations answer "when is the next train?" with a single
value. This one keeps the whole board and adds destination ETAs:

- **A list of upcoming departures**, not one timestamp.
- **Route + destination** for each (e.g. `1 Line → Federal Way Downtown`).
- **Real-time vs. scheduled** flag and `scheduleDeviation` (seconds early/late).
- **Cancellations** via each departure's `status`.
- **Per-destination arrival times.** Configure target stops and each departure
  reports its predicted arrival there. A train that doesn't serve a target
  simply reports `null` for it — no configuration gymnastics.
- **Service alerts** for the stop(s), from OneBusAway `situations`.

Everything lives on one sensor's attributes so any dashboard or automation can
consume it.

## How the destination ETAs work

Each poll fetches the origin board plus one board per target stop (using a wide
look-ahead window), then joins them on `tripId`. The arrival time therefore
comes straight from OneBusAway's own prediction at the destination — including
delay recovery — rather than an estimate. Cost is `1 + N` API calls per poll
(origin + N targets), which is negligible at the default 5-minute interval.

## Installation (HACS)

1. HACS → ⋮ → **Custom repositories** → add this repo's URL, category
   **Integration**.
2. Install **OneBusAway Board**, then restart Home Assistant.
3. **Settings → Devices & Services → Add Integration → OneBusAway Board.**

## Configuration

| Field | Notes |
| --- | --- |
| Name | Friendly name for this board. |
| API base URL | Defaults to Puget Sound (`https://api.pugetsound.onebusaway.org/api`). |
| API key | Your OneBusAway key. Puget Sound: request one at `oba_api_key@soundtransit.org`. |
| Origin stop ID | The platform you board at (e.g. `40_N15-T2`). |
| Target stops | Optional. One per line: `Label = stop_id`. |
| Poll interval | Minutes between refreshes (default 5). |

Targets and poll interval can be edited later via the integration's
**Configure** (options) dialog.

### Finding stop IDs

Stop IDs are agency-prefixed (`40_N15-T2`). Query the API with your key, e.g.
`.../where/stops-for-route/<routeId>.json` or `stops-for-location`. The included
`scripts/validate_live.py` shows the pattern.

## Sensor output

One `sensor` per configured board. State is the next departure time
(`device_class: timestamp`); the board is in the attributes:

```yaml
departures:
  - route: "2 Line"
    headsign: "Redmond Technology"
    trip_id: "40_..."
    depart: "2026-07-04T12:41:00+00:00"
    predicted: true
    status: "default"
    schedule_deviation: -75      # seconds; negative = ahead of schedule
    arrivals:
      Westlake: "2026-07-04T13:01:00+00:00"
      Bellevue Downtown: "2026-07-04T13:28:00+00:00"
  - route: "1 Line"
    headsign: "Federal Way Downtown"
    arrivals:
      Westlake: "2026-07-04T13:10:00+00:00"
      Bellevue Downtown: null    # 1 Line does not serve Bellevue
alerts:
  - severity: "noImpact"
    summary: "..."
```

## Development

`OBA_KEY=<your-key> python scripts/validate_live.py` exercises the parsing/join
logic against the live API without Home Assistant (defaults to Shoreline South →
Westlake/Bellevue; override with `OBA_URL`, `OBA_ORIGIN`, `OBA_TARGETS`).
`OBA_KEY` is required — supply your own OneBusAway API key.

## Credits

Structure and approach informed by
[jvert/home-assistant-onebusaway](https://github.com/jvert/home-assistant-onebusaway),
extended from a single-arrival sensor to a full multi-target departure board.

## License

MIT
