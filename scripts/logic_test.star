def equal(actual, expected, label):
    if actual != expected:
        fail("%s: expected %s, got %s" % (label, expected, actual))

def run_logic_tests():
    options = settings({})
    equal(options["quay"], "NSR:Quay:11544", "default downtown platform")
    equal(settings({"stop": "NSR:StopPlace:337"})["quay"], "all", "other stations")
    equal(settings({"stop": "{bad", "walk_minutes": "nan"})["walk"], 2, "invalid values")
    equal(settings({"rows": "99", "walk_minutes": "-3"})["rows"], 4, "row clamp")
    equal(settings({"walk_minutes": "-3"})["walk"], 0, "walking clamp")
    equal(settings({"stop": '{"value":"NSR:StopPlace:337"}'})["stop"], "NSR:StopPlace:337", "typeahead JSON")
    for invalid in [None, "bad", "2026-02-30T12:00:00+01:00", "2026-09-24T24:00:00+02:00", "2026-09-24T12:00:00+99:00"]:
        equal(parse_timestamp(invalid), None, "malformed timestamp")
    for before, after in [
        ("2026-03-29T01:55:00+01:00", "2026-03-29T03:05:00+02:00"),
        ("2026-10-25T02:55:00+02:00", "2026-10-25T02:05:00+01:00"),
        ("2026-09-24T23:55:00+02:00", "2026-09-25T00:05:00+02:00"),
    ]:
        equal(parse_timestamp(after).unix - parse_timestamp(before).unix, 600, "DST or midnight elapsed time")
    departure = parse_timestamp("2026-09-25T00:05:00+02:00")
    for seconds, label in [(0, "n\u00e5"), (59, "n\u00e5"), (60, "1m"), (899, "14m"), (900, "00:05")]:
        equal(format_countdown({"seconds": seconds, "expected": departure}, options), label, "countdown boundary")
    equal(format_countdown({"seconds": 30, "expected": departure}, settings({"lang": "en"})), "now", "English countdown")
    now = parse_timestamp("2026-09-24T12:00:30+02:00")
    equal(len(parse_calls(fixture("normal"), options, now)), 4, "walk exact boundary")
    equal(len(parse_calls(fixture("normal"), options, parse_timestamp("2026-09-24T12:00:31+02:00"))), 3, "unreachable hidden")
    equal(len(parse_calls(fixture("multimodal"), options, now)), 4, "all transport modes")
    equal(len(parse_calls(fixture("multimodal"), settings({"lines": "re10,b1"}), now)), 2, "line whitelist")
    equal(len(parse_calls(fixture("normal"), settings({"destination_filter": "HELS"}), now)), 4, "case-insensitive destination")
    calls = parse_calls(fixture("normal"), options, now)
    calls[0]["cancelled"] = True
    calls[1]["cancelled"] = True
    equal(select_calls(calls, 2)[-1]["cancelled"], False, "cancelled rows do not hide next service")
    equal(valid_data(fixture("normal"), settings({"stop": "NSR:StopPlace:337"})), False, "snapshot station isolation")
    return render.Root(child = render.Text("PASS", font = "tb-8"))
