from desfire_read import RCDESFire
import os

APP_READ_KEY = bytes.fromhex(os.getenv('APP_READ_KEY'))

card = RCDESFire()
if card.connect_reader() and card.connect_card():
    card.select_application(bytes.fromhex(os.getenv('APP_ID')))
    card.authenticate(1, APP_READ_KEY)
    data = card.read_data(file_no=int(os.getenv('FILE_NO')))
    if data:
        print(f"Data: '{data}'")
        userid, username, credit = data.decode('utf-8').split('|')
        result = {
            'userid': int(userid),
            'username': username,
            'credit': float(credit)
        }
        print(result)
    else:
        print("No data read from the card.")
    card.disconnect()
