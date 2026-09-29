"""
Connectivity service — MQTT subscriber, bridges telemetry into TimescaleDB.

Subscribes to devices/+/telemetry (wildcard across all devices), looks up
the publishing device's UUID by its device_uid, and writes each reading
into the telemetry hypertable. This is the piece that makes the whole
chain real: firmware decode -> MQTT publish -> database -> queryable via
telemetry-api / sovd-api.

In a real deployment, an AWS IoT Rules Engine rule would do this job
instead of a standalone Python process (see project spec Section 4) —
this script is the local-dev equivalent, and its logic (topic parsing,
device lookup, insert) is what a Rules Engine SQL statement or Lambda
would eventually replicate.
"""

import json
import os

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

from db import get_connection

load_dotenv()

BROKER_HOST = os.environ["MQTT_BROKER_HOST"]
BROKER_PORT = int(os.environ["MQTT_BROKER_PORT"])

TOPIC_FILTER = "devices/+/telemetry"


def get_device_id(device_uid: str):
    """Looks up a device's UUID by its device_uid. Returns None if unregistered."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM devices WHERE device_uid = %s", [device_uid])
            row = cur.fetchone()
            return row[0] if row else None


def insert_telemetry(device_id, pid: str, value: float, time: str):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO telemetry (time, device_id, pid, value) VALUES (%s, %s, %s, %s)",
                [time, device_id, pid, value],
            )
            conn.commit()


def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print(f"Connected to broker at {BROKER_HOST}:{BROKER_PORT}, subscribing to {TOPIC_FILTER}")
        client.subscribe(TOPIC_FILTER, qos=1)
    else:
        print(f"Connection failed: {reason_code}")


def on_message(client, userdata, msg):
    # Topic shape: devices/{device_uid}/telemetry
    parts = msg.topic.split("/")
    if len(parts) != 3 or parts[0] != "devices" or parts[2] != "telemetry":
        print(f"Ignoring unexpected topic: {msg.topic}")
        return

    device_uid = parts[1]

    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except json.JSONDecodeError:
        print(f"Ignoring malformed (non-JSON) payload on {msg.topic}: {msg.payload!r}")
        return

    device_id = get_device_id(device_uid)
    if device_id is None:
        print(f"Ignoring message from unregistered device_uid: {device_uid}")
        return

    try:
        insert_telemetry(device_id, payload["pid"], payload["value"], payload["time"])
        print(f"Stored: device={device_uid} pid={payload['pid']} value={payload['value']}")
    except KeyError as e:
        print(f"Ignoring payload missing required field {e}: {payload}")


def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER_HOST, BROKER_PORT)
    client.loop_forever()


if __name__ == "__main__":
    main()