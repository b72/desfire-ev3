# Create a Card Reader
from libs.mqtt import MqttClient
from smartcard.CardMonitoring import CardMonitor
from libs.desfire_read import RCDESFire
from libs.detect_card import CardEventObserver


card_reader = RCDESFire()
mqtt_client = MqttClient()
try:
    mqtt_client.connect()
    card_reader.check_acr122u_connected()
except Exception as e:
    print(f"Unable to run , {e}")
    exit(1)

# Set up the monitor and observer
card_monitor = CardMonitor()
card_observer = CardEventObserver(card_reader, mqtt_client)

card_monitor.addObserver(card_observer)

print("Monitoring card events. Press Ctrl+C to exit.")

try:
    while True:
        pass  # Keep the program running
except KeyboardInterrupt:
    print("Exiting...")
    card_monitor.deleteObserver(card_observer)