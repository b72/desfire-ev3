from libs.mqtt import MqttClient
from smartcard.CardMonitoring import CardObserver
from smartcard.util import toHexString
from libs.desfire_read import RCDESFire
from libs.read_card_data import read_card_data
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
class CardEventObserver(CardObserver, MqttClient):
    def __init__(self, card_handler, mqtt_client):
        self.cardReader = card_handler
        self.mqtt_client = mqtt_client

    def update(self, observable, cards):
        added_cards, removed_cards = cards
        for card in added_cards:
            logger.info(f"Card inserted: {toHexString(card.atr)}")
            time.sleep(0.5)  # Wait for the card to be ready
            try:
                result = read_card_data(self.cardReader, APP_READ_KEY, os.getenv('APP_ID'), os.getenv('FILE_NO'))
                if result:
                    self.mqtt_client.send(result)
                else:
                    logger.warning("No data read from the card.")
            except (NoCardException, CardConnectionException) as e:
                logger.error(f"Error reading card: {e}")
        for card in removed_cards:
            self.mqtt_client.send("Card removed")


