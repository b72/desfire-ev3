


def read_card_data(cardReader, APP_READ_KEY, APP_ID, FILE_NO):
    result = None
    if cardReader.connect_reader() and cardReader.connect_card():
        cardReader.select_application(bytes.fromhex(APP_ID))
        cardReader.authenticate(1, APP_READ_KEY)
        data = cardReader.read_data(file_no=int(FILE_NO))
        if data:
            userid, username, credit = data.decode('utf-8').split('|')
            result = {
                        'userid': int(userid),
                        'username': username,
                        'credit': float(credit)
                    }
        else:
            result = None
    cardReader.disconnect()
    return result



