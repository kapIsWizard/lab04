"""TCP server using the generated weather station protocol."""

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
    ProtocolError,
    SensorReading,
    receive_message,
    send_message,
)


def build_forecast(request: ForecastRequest) -> ForecastResponse:
    """Create a deterministic answer so the demo is easy to test."""

    risk_level = 1 if request.hours <= 12 else 2
    forecast = f"Station {request.station_id}: stable weather for {request.hours}h"
    return ForecastResponse(
        station_id=request.station_id,
        forecast=forecast,
        risk_level=risk_level,
    )


def handle_message(connection: socket.socket, message: object) -> bool:
    """Handle one decoded message. Return False when the client should close."""

    if isinstance(message, SensorReading):
        print(
            "reading "
            f"station={message.station_id} "
            f"temp={message.temperature_c:.1f}C "
            f"humidity={message.humidity_percent}% "
            f"wind={message.wind_speed_mps:.1f}m/s "
            f"status={message.status} "
            f"history={message.history}"
        )
        return True

    if isinstance(message, ForecastRequest):
        send_message(connection, build_forecast(message))
        return True

    send_message(connection, ErrorMessage(code=400, message="Unsupported message"))
    return True


def serve(host: str, port: int, once: bool = False) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen()
        print(f"server listening on {host}:{port}")

        while True:
            connection, address = server.accept()
            with connection:
                print(f"client connected from {address[0]}:{address[1]}")
                while True:
                    try:
                        message = receive_message(connection)
                    except ProtocolError as exc:
                        send_message(connection, ErrorMessage(code=422, message=str(exc)))
                        break

                    if message is None or not handle_message(connection, message):
                        break

            if once:
                break


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the generated protocol TCP server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9009)
    parser.add_argument("--once", action="store_true", help="Stop after one client disconnects.")
    args = parser.parse_args()

    serve(args.host, args.port, once=args.once)


if __name__ == "__main__":
    main()
