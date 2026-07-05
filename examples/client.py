"""TCP client using the generated weather station protocol."""

from __future__ import annotations

import argparse
import socket
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from generated.protocol import (  # noqa: E402
    ErrorMessage,
    ForecastRequest,
    ForecastResponse,
    SensorReading,
    receive_message,
    send_message,
)


def run_client(host: str, port: int) -> None:
    with socket.create_connection((host, port), timeout=5) as sock:
        reading = SensorReading(
            station_id=7,
            temperature_c=21.6,
            humidity_percent=64,
            wind_speed_mps=3.4,
            status="OK",
            history={
                "last_hour": [21.1, 21.3, 21.6],
                "battery": {"percent": 88, "charging": False},
            },
        )
        send_message(sock, reading)
        print(f"sent reading: {reading}")

        request = ForecastRequest(station_id=7, hours=12)
        send_message(sock, request)
        print(f"sent request: {request}")

        response = receive_message(sock)
        if isinstance(response, ForecastResponse):
            print(
                "forecast "
                f"station={response.station_id} "
                f"risk={response.risk_level} "
                f"text={response.forecast}"
            )
        elif isinstance(response, ErrorMessage):
            print(f"server error {response.code}: {response.message}")
        else:
            print(f"unexpected response: {response!r}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the generated protocol TCP client.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9009)
    args = parser.parse_args()

    run_client(args.host, args.port)


if __name__ == "__main__":
    main()
