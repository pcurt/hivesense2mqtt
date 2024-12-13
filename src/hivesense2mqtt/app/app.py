"""App main file."""

import binascii
import json
import os
from typing import Any

import paho.mqtt.client as mqtt
import requests
from loguru import logger

from hivesense2mqtt.app.ha_manager import HA_MANAGER

BROKER = "liveobjects.orange-business.com"
PORT = 8883


class HiveSense2Mqtt:
    """Main class object."""

    def __init__(self):
        """HiveSense2Mqtt class constructor."""
        logger.info(f"ClientID is {os.getenv('ORANGE_CLIENT_ID')}")
        self.orange_back = mqtt.Client(client_id=os.getenv("ORANGE_CLIENT_ID"))

        self.orange_back.username_pw_set(os.getenv("ORANGE_USERNAME"), os.getenv("ORANGE_PASSWORD"))
        self.orange_back.tls_set(ca_certs=os.getenv("ORANGE_CA_FILE"))  # type: ignore

        self.orange_back.on_connect = self.on_connect
        self.orange_back.on_message = self.on_message

        self.orange_back.connect(BROKER, PORT, 60)
        logger.info("HiveSense2Mqtt init")

        self.ha_back = HA_MANAGER()

    def on_connect(self, client: mqtt.Client, userdata: Any, flags: dict[str, Any], rc: int):
        """Callback on MQTT connection.

        Args:
            client (mqtt.Client): the MQTT client
            userdata (Any): data
            flags (dict[str, Any]): flags
            rc (int): return code
        """
        if rc == 0:
            logger.info("Connected to Orange Lora backend")
            self.orange_back.subscribe(os.getenv("ORANGE_TOPIC", "fifo"))
        else:
            logger.info("Not Connected")

    def on_message(self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage):
        """Callback on MQTT message.

        Args:
            client (mqtt.Client): the MQTT client
            userdata (Any): data
            msg (mqtt.MQTTMessage): the received message
        """
        message_str = msg.payload.decode("utf-8")
        logger.info(f"Message received on {msg.topic}: {message_str}")

        # Read message as dict
        message_dict = json.loads(message_str)

        # Get payload
        payload = message_dict.get("value", {}).get("payload")
        logger.info(f"Extracted payload: {payload}")

        payload_bytes = binascii.unhexlify(payload)
        device_id = payload_bytes[0]
        vbat = payload_bytes[1] * 7 + 3000
        hx711_value = payload_bytes[2] | (payload_bytes[3] << 8) | (payload_bytes[4] << 16)
        bssids = [
            payload_bytes[5:11],
            payload_bytes[11:17],
            payload_bytes[17:23],
        ]
        logger.info(f"device_id: {device_id}")
        logger.info(f"vbat: {vbat}")
        logger.info(f"hx711_value: {hx711_value}")
        # Convert BSSIDs in str
        bssids_readable = [":".join(f"{byte:02x}" for byte in bssid) for bssid in bssids]

        for bssid in bssids_readable:
            logger.info(f"bssid: {bssid}")

        # Update values to HA instance
        self.ha_back.hsdevid.update_state(str(device_id))
        self.ha_back.hsvolt.update_state(str(vbat / 1000))
        self.ha_back.hsweight.update_state(str(hx711_value))

        # Get location from SSIDs
        result = self.request_google_geolocation(bssids_readable)
        if result is not None:
            (lat, lng, accuracy) = result
            data_dict = {"latitude": lat, "longitude": lng, "gps_accuracy": accuracy}
            logger.info(f"location is: {data_dict}")
            self.ha_back.hspos.update_attribute(json.dumps(data_dict))
        else:
            location = message_dict.get("location")
            if location is not None:
                lat = location.get("lat")
                lon = location.get("lon")
                data_dict = {"latitude": lat, "longitude": lon, "gps_accuracy": 2000}
                logger.info(f"Location from lora Network (poor gps_accuracy): {data_dict}")
                self.ha_back.hspos.update_attribute(json.dumps(data_dict))
            else:
                logger.info("Location unavailable")

    def loop_start(self):
        """Start main loop that collect data from Orange backend."""
        logger.info("Start Orange Lora loop")
        self.orange_back.loop_start()

    def request_google_geolocation(self, bssids: list[str]):
        """Get the GPS position from a list of BSSIDs using google geolocation APi.

        Args:
            bssids (list[str]): List of BSSIDs
        """
        wifi_access_points = [
            {"macAddress": bssid}
            for bssid in bssids
            if bssid != "00:00:00:00:00:00" and len(bssid) == 17
        ]

        headers = {"Content-Type": "application/json"}

        data = {"considerIp": "false", "wifiAccessPoints": wifi_access_points}

        logger.info(f"Raw data : {data}")

        url = (
            f"https://www.googleapis.com/geolocation/v1/geolocate?key={os.getenv('GOOGLE_API_KEY')}"
        )
        response = requests.post(url, headers=headers, json=data, timeout=3)

        logger.info(f"Response status : {response.status_code}")
        if response.status_code == 200:
            response_data = response.json()
            location = response_data.get("location", {})
            lat = location.get("lat")
            lng = location.get("lng")
            accuracy = response_data.get("accuracy")

            return (lat, lng, accuracy)

        return None
