from smartcard.CardMonitoring import CardMonitor, CardObserver
from smartcard.util import toHexString
from desfire_read import RCDESFire
from read_card_data import read_card_data
from smartcard.Exceptions import NoCardException, CardConnectionException
import os
import time
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(
    level=logging.INFO,  # default level
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("SmartCard-Reader")

APP_READ_KEY = bytes.fromhex(os.getenv('APP_READ_KEY'))
# Define a class to observe card events
class CardEventObserver(CardObserver):
    def __init__(self, card_handler):
        self.cardReader = card_handler

    def update(self, observable, cards):
        added_cards, removed_cards = cards
        for card in added_cards:
            logger.info(f"Card inserted: {toHexString(card.atr)}")
            time.sleep(0.5)  # Wait for the card to be ready
            try:
                result = read_card_data(self.cardReader, APP_READ_KEY, os.getenv('APP_ID'), os.getenv('FILE_NO'))
                if result:
                    logger.info(f"Card Data: {result}")
                else:
                    logger.warning("No data read from the card.")
            except (NoCardException, CardConnectionException) as e:
                logger.error(f"Error reading card: {e}")
        for card in removed_cards:
            logger.info("Card removed")

# Create a Card Reader
card_reader = RCDESFire()

# Set up the monitor and observer
card_monitor = CardMonitor()
card_observer = CardEventObserver(card_reader)

card_monitor.addObserver(card_observer)

logger.info("Monitoring card events. Press Ctrl+C to exit.")

try:
    while True:
        pass  # Keep the program running
except KeyboardInterrupt:
    logger.info("Exiting...")
    card_monitor.deleteObserver(card_observer)
