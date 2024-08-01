"""Define the main class object."""

import os
import time
from typing import Union

from ha_mqtt.ha_device import HaDevice
from ha_mqtt.mqtt_device_base import MqttDeviceBase, MqttDeviceSettings
from ha_mqtt.mqtt_sensor import MqttSensor
from ha_mqtt.util import HaSensorDeviceClass
from loguru import logger
from paho.mqtt.client import Client
from paho.mqtt.enums import CallbackAPIVersion


class MqttDeviceTracker(MqttDeviceBase):
    """class that implements a Device Tracker typ.

    :param settings: as in :class:`~ha_mqtt.mqtt_device_base.MqttDeviceBase`

    .. hint::
       Use :meth:`~ha_mqtt.mqtt_device_base.MqttDeviceBase.update_state`
       to send the actual sensor data to homeassistant

    """

    device_type = "device_tracker"

    def __init__(
        self,
        settings: MqttDeviceSettings,
        send_only: bool = False,
    ):
        """MqttDeviceTracker constructor.

        Args:
            settings (MqttDeviceSettings): MQTT device settings
            send_only (bool, optional): Indicates if it is only sending information.
            Defaults to False.
        """
        super().__init__(settings, send_only)

    def pre_discovery(self) -> None:
        """Pre discovery function."""
        self.add_config_option("json_attributes_topic", "hive-sense-pos/attributes")  # type: ignore
        self.add_config_option("name", "Hive Sense Position")  # type: ignore

    def update_attribute(
        self,
        payload: Union[str, bytes, bytearray, int, float, None],
        retain: bool = True,
    ) -> None:
        """Publishes a payload on the device's attributes topic.

        :param payload: payload to publish
        :param retain: set to True to send as a retained message
        """
        self._logger.debug("publishing payload '%s' for %s", payload, self._unique_id)

        self._client.publish("hive-sense-pos/attributes", payload, retain=retain)
        time.sleep(0.01)


class HA_MANAGER:
    """Class that implements a Home Assistant Manager.

    No parameter.
    """

    def __init__(self) -> None:
        """Home Assistant Manager constructor."""
        self.client = Client(CallbackAPIVersion.VERSION2, "hiveSense2mqtt")
        self.client.connect("localhost", 1883)
        self.client.loop_start()

        # create device info dictionary
        unique_id = "hiveSense2mqtt-" + str(os.getenv("HA_UNIQUE_ID"))
        dev = HaDevice("hiveSense2mqtt", unique_id)

        logger.info("hiveSense2mqtt connected to HA")

        # Create the deviceID field
        self.hsdevid = MqttDeviceBase(
            MqttDeviceSettings("Hive Sense device ID", "hive-sense-devid", self.client, dev),
            True,
        )
        self.hsdevid.start()

        # Create the device tracker
        self.hspos = MqttDeviceTracker(
            MqttDeviceSettings("Hive Sense Voltage", "hive-sense-pos", self.client, dev),
            True,
        )
        self.hspos.start()

        # Create the device for battery voltage
        self.hsvolt = MqttSensor(
            MqttDeviceSettings("Hive Sense Battery Voltage", "hive-sense-batt", self.client, dev),
            HaSensorDeviceClass.BATTERY,
            "V",
            True,
        )
        self.hsvolt.start()

        # Create sensor for the weight
        self.hsweight = MqttSensor(
            MqttDeviceSettings("Hive Sense weight measure", "hive-sense-weight", self.client, dev),
            HaSensorDeviceClass.WEIGHT,
            "g",
            True,
        )
        self.hsweight.start()

        # Create the alarm device
        # TODO
