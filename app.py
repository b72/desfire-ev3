# Create a Card Reader
from smartcard.CardMonitoring import CardMonitor
from desfire_read import RCDESFire
from detect_card import CardEventObserver

card_reader = RCDESFire()

# Set up the monitor and observer
card_monitor = CardMonitor()
card_observer = CardEventObserver(card_reader)

card_monitor.addObserver(card_observer)

print("Monitoring card events. Press Ctrl+C to exit.")

try:
    while True:
        pass  # Keep the program running
except KeyboardInterrupt:
    print("Exiting...")
    card_monitor.deleteObserver(card_observer)