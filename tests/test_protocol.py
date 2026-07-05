from __future__ import annotations

import socket
import unittest

from generated.protocol import (
    ForecastRequest,
    ForecastResponse,
    ProtocolError,
    SensorReading,
    deserialize_message,
    pack_frame,
    receive_message,
    send_message,
    serialize_message,
)


class ProtocolTests(unittest.TestCase):
    def test_round_trip_sensor_reading(self) -> None:
        message = SensorReading(
            station_id=42,
            temperature_c=18.75,
            humidity_percent=58,
            wind_speed_mps=4.5,
            status="OK",
        )

        decoded = deserialize_message(serialize_message(message))

        self.assertIsInstance(decoded, SensorReading)
        self.assertEqual(decoded.station_id, message.station_id)
        self.assertAlmostEqual(decoded.temperature_c, message.temperature_c, places=5)
        self.assertEqual(decoded.humidity_percent, message.humidity_percent)
        self.assertAlmostEqual(decoded.wind_speed_mps, message.wind_speed_mps, places=5)
        self.assertEqual(decoded.status, message.status)

    def test_socket_helpers_transfer_one_message(self) -> None:
        left, right = socket.socketpair()
        try:
            expected = ForecastResponse(
                station_id=7,
                forecast="Stable weather",
                risk_level=1,
            )

            send_message(left, expected)
            received = receive_message(right)

            self.assertEqual(received, expected)
        finally:
            left.close()
            right.close()

    def test_unknown_message_id_is_rejected(self) -> None:
        with self.assertRaises(ProtocolError):
            deserialize_message(b"\x12\x34")

    def test_frame_contains_length_prefix(self) -> None:
        frame = pack_frame(ForecastRequest(station_id=7, hours=24))

        self.assertEqual(int.from_bytes(frame[:4], "big"), len(frame) - 4)


if __name__ == "__main__":
    unittest.main()
