"""
Connectivity service — MQTT publisher.

Publishes telemetry to devices/{device_id}/telemetry, matching the topic
structure from the project spec (Section 4). Currently publishes
synthetic/test data; the real version will read from the zone
controller's UART/SPI link instead of generating values here — this is
a stepping stone proving the MQTT publish path end-to-end first, same
"prove each layer independently" approach as the rest of this project.

Structured so migrating from local Mosquitto to AWS IoT Core later is a
config change (host, port, TLS/cert auth), not a rewrite — see ADR 0005.
"""

import json
import os
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()

BROKER_HOST = os.environ["MQTT_BROKER_HOST"]
BROKER_PORT = int(os.environ["MQTT_BROKER_PORT"])
DEVICE_ID = os.environ["MQTT_DEVICE_ID"]

TOPIC = f"devices/{DEVICE_ID}/telemetry"


def build_payload(pid: str, value: float) -> str:
    """Builds the JSON payload for a single telemetry point."""
    return json.dumps({
        "pid": pid,
        "value": value,
        "time": datetime.now(timezone.utc).isoformat(),
    })


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"Connected to broker at {BROKER_HOST}:{BROKER_PORT}")
    else:
        print(f"Connection failed: {reason_code}")


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=DEVICE_ID)
    client.on_connect = on_connect
    client.connect(BROKER_HOST, BROKER_PORT)
    client.loop_start()

    # Stand-in test values until the real zone-controller link exists.
    test_readings = [("rpm", 1726.0), ("speed", 62.0), ("coolant_temp", 91.0)]

    try:
        for pid, value in test_readings:
            payload = build_payload(pid, value)
            result = client.publish(TOPIC, payload, qos=1)
            result.wait_for_publish()
            print(f"Published to {TOPIC}: {payload}")
            time.sleep(1)
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()