#!/usr/bin/env python3
"""Verify the two Oslo Colletts gate platforms against live Entur data."""

import argparse
import os
import sys

import requests

ENDPOINT = "https://api.entur.io/journey-planner/v3/graphql"
QUERY = """
query Probe($stop: String!) {
  stopPlace(id: $stop) {
    id name
    quays {
    id name publicCode
      lines { id publicCode name }
      estimatedCalls(numberOfDepartures: 10, timeRange: 7200,
                     arrivalDeparture: departures, includeCancelledTrips: true) {
        expectedDepartureTime
        destinationDisplay { frontText }
        serviceJourney { line { publicCode } }
      }
    }
  }
}
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--client-name", default=os.environ.get(
        "ET_CLIENT_NAME", "jakobbbbbbb-tidbyt-colletts"))
    args = parser.parse_args()
    try:
        response = requests.post(
            ENDPOINT,
            json={"query": QUERY, "variables": {"stop": "NSR:StopPlace:6286"}},
            headers={"ET-Client-Name": args.client_name,
                     "Content-Type": "application/json"},
            timeout=20,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("errors"):
            raise ValueError(str(payload["errors"]))
        stop = payload["data"]["stopPlace"]
        if not stop:
            raise ValueError("Oslo stop not found")
        print(f"{stop['name']} ({stop['id']})")
        for quay in stop["quays"]:
            print(f"\n{quay['id']} | platform {quay['publicCode']}")
            for line in quay["lines"]:
                print(f"  Line {line['publicCode']}: {line['name']} [{line['id']}]")
            print(f"  {'DEPARTURE':25} {'LINE':5} DESTINATION")
            for call in quay["estimatedCalls"]:
                print(f"  {call['expectedDepartureTime']:25} "
                      f"{call['serviceJourney']['line']['publicCode']:5} "
                      f"{call['destinationDisplay']['frontText']}")
    except (requests.RequestException, ValueError, KeyError, TypeError) as error:
        print(f"Entur probe failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())