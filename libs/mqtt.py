import os
import paho.mqtt.client as mqtt
import logging

logging.basicConfig(
    level=logging.INFO,  # default level
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)
class MqttClient:
    def __init__(self, broker=None, port=None, channel=None):
        self.broker = broker or os.getenv('MQTT_BROKER', 'localhost')
        self.port = port or int(os.getenv('MQTT_PORT', 1883))
        self.channel = channel or os.getenv('MQTT_CHANNEL', 'card/data')
        self.mqtt_client = mqtt.Client()
        self.connected = False
        self.mqtt_client.on_connect = self._on_connect
        self.mqtt_client.on_message = self._on_message
        self._message_callback = None

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            client.subscribe(self.channel)
        else:
            logger.error(f"Failed to connect, return code {rc}")

    def _on_message(self, client, userdata, msg):
        if self._message_callback:
            self._message_callback(msg.topic, msg.payload.decode())

    def connect(self):
        if not self.connected:
            logger.info(f"Connecting to MQTT broker at {self.broker}:{self.port} on channel {self.channel}")
            self.mqtt_client.connect(self.broker, self.port)
            logger.info("Connected to MQTT broker")
            self.mqtt_client.loop_start()

    def send(self, data):
        self.connect()
        if not isinstance(data, (str, bytearray, int, float)) and data is not None:
            data = str(data)
        self.mqtt_client.publish(self.channel, data)
        logger.info(f"Sent data: {data} to channel: {self.channel}")

    def receive(self, callback):
        self._message_callback = callback
        self.connect()
