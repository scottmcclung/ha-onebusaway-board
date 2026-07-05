# OneBusAway Board

A Home Assistant integration that exposes a **departure board** for a
[OneBusAway](https://onebusaway.org/) transit stop — not just the single next
arrival, but the next several departures, each with route, destination, live
departure/arrival times, and real-time delay.

Each stop is its own config entry and its own sensor. Add the integration once
per stop you care about. Composition across stops (e.g. "which train from my
origin reaches my destination, and when") is left to the consumer: every
departure carries its `trip_id`, so a dashboard or template joins boards across
stops on that key.

## What makes this different

Most OneBusAway integrations answer "when is the next train?" with a single
value. This one keeps the whole board:

- **A list of upcoming departures**, not one timestamp.
- **Route + destination** for each (e.g. `1 Line → Federal Way Downtown`).
- **Departure and arrival time** at the stop (real-time when available, else
  scheduled), plus a `predicted` flag.
- **`schedule_deviation`** — seconds early/late.
- **Cancellations** via each departure's `status`.
- **Service alerts** for the stop, from OneBusAway `situations`.
- **`trip_id`** on every departure, so you can join stops together downstream.

Everything lives on one sensor's attributes, so any dashboard or automation can
consume it.

## Installation (HACS)

1. HACS → ⋮ → **Custom repositories** → add this repo's URL, category
   **Integration**.
2. Install **OneBusAway Board**, then restart Home Assistant.
3. **Settings → Devices & Services → Add Integration → OneBusAway Board.**
   Repeat for each stop.

## Configuration

One entry per stop:

| Field | Notes |
| --- | --- |
| Name | Friendly name for this board (e.g. "Shoreline South SB"). |
| API base URL | Defaults to Puget Sound (`https://api.pugetsound.onebusaway.org/api`). |
| API key | Your OneBusAway key. Puget Sound: request one at `oba_api_key@soundtransit.org`. |
| Stop ID | The stop/platform (e.g. `40_N15-T2`). |
| Poll interval | Minutes between refreshes (default 5), editable later via **Configure**. |

### Finding stop IDs

Stop IDs are agency-prefixed (`40_N15-T2`). Query the API with your key, e.g.
`.../where/stops-for-route/<routeId>.json` or `stops-for-location`. The included
`scripts/validate_live.py` shows the request pattern.

## Sensor output

One `sensor` per stop. State is the next departure time
(`device_class: timestamp`); the board is in the attributes:

```yaml
departures:
  - route: "2 Line"
    headsign: "Redmond Technology"
    trip_id: "40_..."
    depart: "2026-07-04T12:41:00+00:00"
    arrive: "2026-07-04T12:41:00+00:00"
    predicted: true
    status: "default"
    schedule_deviation: -75      # seconds; negative = ahead of schedule
alerts:
  - severity: "noImpact"
    summary: "..."
```

### Joining stops (destination ETAs)

To show "when does the next train from my origin reach my destination," poll two
boards and match on `trip_id`: a departure at the origin whose `trip_id` also
appears at the destination gets that destination entry's `arrive` time. A train
that does not serve the destination simply has no matching `trip_id` there. This
join is intentionally a consumer concern, not baked into the integration.

## Development

`OBA_KEY=<your-key> python scripts/validate_live.py` exercises the parsing logic
against the live API without Home Assistant (defaults to Shoreline South;
override with `OBA_URL`, `OBA_STOP`). `OBA_KEY` is required — supply your own
OneBusAway API key.

## Credits

Structure and approach informed by
[jvert/home-assistant-onebusaway](https://github.com/jvert/home-assistant-onebusaway),
extended from a single-arrival sensor to a full per-stop departure board.

## License

MIT
