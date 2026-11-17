"""Exercise the plugin against a local MQTT CONNACK responder.

Run with: python3 -m unittest discover -s tests -v
Requires the plugin's paho-mqtt dependency, with no external broker.
"""
import socket
import subprocess
import sys
import threading
import unittest
from pathlib import Path


PLUGIN = Path(__file__).resolve().parents[1] / "check-mqtt.py"


class ConnectionResultTests(unittest.TestCase):
    def run_plugin(self, protocol, reason, broker=False):
        errors = []
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen(1)
            listener.settimeout(8)
            port = listener.getsockname()[1]

            def respond():
                try:
                    conn, _ = listener.accept()
                    with conn:
                        conn.settimeout(8)
                        def read_exact(size):
                            data = b""
                            while len(data) < size:
                                part = conn.recv(size - len(data))
                                if not part:
                                    raise EOFError("Incomplete CONNECT packet")
                                data += part
                            return data
                        if read_exact(1) != b"\x10":
                            raise AssertionError("Expected MQTT CONNECT")
                        size = 0
                        multiplier = 1
                        while True:
                            byte = read_exact(1)[0]
                            size += (byte & 127) * multiplier
                            if not byte & 128:
                                break
                            multiplier *= 128
                        read_exact(size)
                        if protocol == 5:
                            conn.sendall(bytes([0x20, 3, 0, reason, 0]))
                        else:
                            conn.sendall(bytes([0x20, 2, 0, reason]))
                        while conn.recv(4096):
                            pass
                except Exception as exc:
                    errors.append(exc)

            worker = threading.Thread(target=respond, daemon=True)
            worker.start()
            command = [sys.executable, str(PLUGIN), "-H", "127.0.0.1",
                       "-P", str(port), "-M", str(protocol), "-m", "2"]
            if broker:
                command.append("--broker")
            try:
                result = subprocess.run(command, capture_output=True, text=True,
                                        timeout=6)
            finally:
                worker.join(timeout=9)
            self.assertFalse(worker.is_alive(), "MQTT responder did not finish")
            self.assertFalse(errors, errors)
            return result

    def test_rejected_connections_are_critical(self):
        for protocol, reason in ((4, 5), (5, 0x87)):
            for broker in (False, True):
                with self.subTest(protocol=protocol, broker=broker):
                    result = self.run_plugin(protocol, reason, broker)
                    self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                    self.assertEqual(result.stdout.strip(),
                                     "CRITICAL - Connection rejected: Not authorized")
                    self.assertNotIn("Traceback", result.stderr)

    def test_accepted_broker_connections_remain_ok(self):
        for protocol in (4, 5):
            with self.subTest(protocol=protocol):
                result = self.run_plugin(protocol, 0, broker=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertTrue(result.stdout.startswith("OK - broker CONNECT properties:"))


if __name__ == "__main__":
    unittest.main()
