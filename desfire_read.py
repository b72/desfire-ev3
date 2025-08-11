from Crypto.Cipher import DES, DES3
from Crypto.Random import get_random_bytes
import Crypto.Cipher.DES3 as des3_module
from smartcard.System import readers
from smartcard.util import toBytes
from smartcard.util import toHexString
from smartcard.Exceptions import NoCardException, CardConnectionException
import logging

logging.basicConfig(
    level=logging.INFO,  # default level
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

class RCDESFire:
    CLA = 0x90
    # Command Codes
    DF_AUTHENTICATE = 0x0A
    DF_CHANGE_KEY = 0xC4
    DF_GET_KEY_SETTINGS = 0x45
    DF_CHANGE_KEY_SETTINGS = 0x54
    DF_SELECT_APPLICATION = 0x5A
    DF_GET_VERSION = 0x60
    DF_CREATE_APPLICATION = 0xCA
    DF_DELETE_APPLICATION = 0xDA
    DF_FORMAT_PICC = 0xFC
    DF_CREATE_STD_DATA_FILE = 0xCD
    DF_READ_DATA = 0xBD
    DF_WRITE_DATA = 0x3D
    DF_ADDITIONAL_FRAME = 0xAF
    DF_GET_APPLICATION_IDS = 0x6A
    DF_GET_FILE_IDS = 0x6F
    DF_GET_CARD_UUID = 0x51

    # Status Codes
    DF_OPERATION_OK = 0x00
    DF_NO_CHANGES = 0x0C
    DF_OUT_OF_EEPROM_ERROR = 0x0E
    DF_ILLEGAL_COMMAND_CODE = 0x1C
    DF_INTEGRITY_ERROR = 0x1E
    DF_NO_SUCH_KEY = 0x40
    DF_LENGTH_ERROR = 0x7E
    DF_PERMISSION_DENIED = 0x9D
    DF_PARAMETER_ERROR = 0x9E
    DF_APPLICATION_NOT_FOUND = 0xA0
    DF_AUTHENTICATION_ERROR = 0xAE
    DF_BOUNDARY_ERROR = 0xBE
    DF_COMMAND_ABORTED = 0xCA
    DF_DUPLICATE_ERROR = 0xDE
    DF_FILE_NOT_FOUND = 0xF0
    
    # Error map 
    _ERROR_MAP = {
        0x00: "Operation OK: Function was executed without failure.",
        0x0C: "No Changes: No changes done to backup file, no need to commit/abort.",
        0x0E: "Out of EEPROM Error: Insufficient NV-memory to complete command.",
        0x1C: "Illegal Command Code: Command code not supported.",
        0x1E: "Integrity Error: CRC or MAC does not match, or invalid padding bytes.",
        0x40: "No Such Key: Invalid key number specified.",
        0x7E: "Length Error: Length of command string invalid.",
        0x9D: "Permission Denied: Current configuration or status does not allow the requested command.",
        0x9E: "Parameter Error: Value of the parameter(s) invalid.",
        0xA0: "Application Not Found: Requested application not present on the card.",
        0xAE: "Authentication Error: Current authentication status does not allow the requested command.",
        0xAF: "Additional Frame: Additional data frame is expected to be sent.",
        0xBE: "Boundary Error: Attempt to read or write data out of the file's or record's limits.",
        0xCA: "Command Aborted: The current command has been aborted.",
        0xDE: "Duplicate Error: The specified file or application already exists.",
        0xF0: "File Not Found: The specified file does not exist.",
    }

    @staticmethod
    def get_error_message(status_byte):
        return RCDESFire._ERROR_MAP.get(status_byte, f"Unknown status: {status_byte:02X}")

    def __init__(self, reader_index=0):
        self.reader = None
        self.connection = None
        self.session_key = None
        self.use_single_des_mode = False
        self.auth_key = None
           
    def get_readers(self):
        return readers()

    def connect_reader(self):
        r = self.get_readers()
        if not r:
            self.reader = None
            return False
        self.reader = r[0]
        return True

    def connect_card(self):
        if not self.reader:
            return False
        try:
            self.connection = self.reader.createConnection()
            self.connection.connect()
            return True
        except (NoCardException, CardConnectionException):
            self.connection = None
            return False

    def disconnect(self):
        if self.connection:
            self.connection.disconnect()
            logger.info("🔌 Card connection closed.")

    def _transmit(self, apdu: list):
        """Sends an APDU and returns the response data and status words."""
        response, sw1, sw2 = self.connection.transmit(apdu)
        logger.info(f"SW: {hex(sw1)} {hex(sw2)}")
        if sw1 != 0x91: # Main status for DESFire
            logger.error(f"Card communication error. SW={sw1:02X}{sw2:02X}")
            raise IOError(f"Card communication error. SW={sw1:02X}{sw2:02X}")
        return bytes(response), sw2

    def _expand_des_key(self, key_bytes):
        if len(key_bytes) == 16: return key_bytes + key_bytes[:8]
        if len(key_bytes) == 24: return key_bytes
        logger.error("Key must be 16 or 24 bytes for 3DES.")
        raise ValueError("Key must be 16 or 24 bytes for 3DES.")


    def _custom_crypto_transform(self, data: bytes, key: bytes, num_blocks: int) -> bytes:
        if len(data) < num_blocks * 8:
            logger.error("Not enough data for the specified number of blocks.")
            raise ValueError("Not enough data for the specified number of blocks.")

        if self.use_single_des_mode:
            cipher = DES.new(key[:8], DES.MODE_ECB)
        else:
            cipher = DES3.new(self._expand_des_key(key), DES3.MODE_ECB)

        buffer = bytearray(data)
        
        block_plain = buffer[0:8]
        block_transformed = cipher.decrypt(block_plain)
        buffer[0:8] = block_transformed

        for i in range(1, num_blocks):
            prev_block_transformed = buffer[(i-1)*8 : i*8] 
            curr_block_plain = data[i*8 : (i+1)*8]
            xored = bytes(a ^ b for a, b in zip(curr_block_plain, prev_block_transformed))
            curr_block_transformed = cipher.decrypt(xored)
            buffer[i*8 : (i+1)*8] = curr_block_transformed

        return bytes(buffer)
    

    def select_application(self, app_id: bytes):
        if len(app_id) != 3:
            logger.error("Application ID must be 3 bytes long.")
            raise ValueError("Application ID must be 3 bytes long.")
        logger.info(f"--- Selecting App: {app_id.hex()} ---")
        apdu = [self.CLA, self.DF_SELECT_APPLICATION, 0x00, 0x00, 0x03] + list(app_id) + [0x00]
        _, status = self._transmit(apdu)
        if status != self.DF_OPERATION_OK:
            logger.error(f"Failed to select application: {self.get_error_message(status)}")
            raise Exception(f"Failed to select app: {self.get_error_message(status)}")
        logger.info("✅ Application selected successfully.")
        return True

    def authenticate(self, key_no: int, key: bytes):
        logger.info(f"--- Authenticating with Key No. {key_no} ---")
        self.auth_key = key
        self.use_single_des_mode = (key[0:8] == key[8:16])

        apdu1 = [self.CLA, self.DF_AUTHENTICATE, 0x00, 0x00, 0x01, key_no] + [0x00]
        enc_rndB, status = self._transmit(apdu1)
        if status != self.DF_ADDITIONAL_FRAME:
            logger.error(f"Auth step 1 failed: {self.get_error_message(status)}")
            raise Exception(f"Auth step 1 failed: {self.get_error_message(status)}")

        rndB = self._custom_crypto_transform(enc_rndB, self.auth_key, 1)
        
        rndA = get_random_bytes(8)
        payload_plain = rndA + (rndB[1:] + rndB[:1])
        payload_enc = self._custom_crypto_transform(payload_plain, self.auth_key, 2)
        
        apdu2 = [self.CLA, self.DF_ADDITIONAL_FRAME, 0x00, 0x00, 0x10] + list(payload_enc) + [0x00]
        enc_rndA_rot_card, status = self._transmit(apdu2)
        if status != self.DF_OPERATION_OK:
            logger.error(f"Auth step 2 failed: {self.get_error_message(status)}")
            raise Exception(f"Auth step 2 failed: {self.get_error_message(status)}")
        
        rndA_rot_card = self._custom_crypto_transform(enc_rndA_rot_card, self.auth_key, 1)
        if rndA_rot_card[:8] != (rndA[1:] + rndA[:1]):
            logger.error("Authentication failed: RndA mismatch")
            raise Exception("Authentication failed: RndA mismatch")
        
        logger.info("✅ Authentication successful")
        session_key_seed = rndA[:4] + rndB[:4] + rndA[4:8] + rndB[4:8]
        self.session_key = session_key_seed # The C# code uses the 16-byte key directly
        logger.info(f"Session Key: {self.session_key.hex()}")
        return True


    def read_data(self, file_no: int, offset: int = 0) -> bytes:
        # Step 1: Read the 2-byte length prefix
        length_prefix_len = 2
        offset_bytes = offset.to_bytes(3, 'little')
        length_bytes = length_prefix_len.to_bytes(3, 'little')

        data_field = bytes([file_no]) + offset_bytes + length_bytes
        lc = len(data_field)
        le = 0x00  # up to 256 bytes in response

        apdu = [self.CLA, self.DF_READ_DATA, 0x00, 0x00, lc] + list(data_field) + [le]
        response_data, status = self._transmit(apdu)

        full_response = bytearray(response_data)

        while status == self.DF_ADDITIONAL_FRAME:
            apdu_af = [self.CLA, self.DF_ADDITIONAL_FRAME, 0x00, 0x00, le]
            response_data, status = self._transmit(apdu_af)
            full_response.extend(response_data)

        if status != self.DF_OPERATION_OK:
            logger.error(f"Failed to read length prefix: {self.get_error_message(status)}")
            raise Exception(f"Failed to read length prefix: {self.get_error_message(status)}")

        if len(full_response) < length_prefix_len:
            logger.error("Failed to read length prefix: insufficient data received")
            raise Exception("Failed to read length prefix: insufficient data received")

        data_length = int.from_bytes(full_response[:length_prefix_len], 'big')

        # Step 2: Read the actual data length bytes starting from offset + 2
        offset_bytes = (offset + length_prefix_len).to_bytes(3, 'little')
        length_bytes = data_length.to_bytes(3, 'little')

        data_field = bytes([file_no]) + offset_bytes + length_bytes
        lc = len(data_field)

        apdu = [self.CLA, self.DF_READ_DATA, 0x00, 0x00, lc] + list(data_field) + [le]
        response_data, status = self._transmit(apdu)

        full_response = bytearray(response_data)

        while status == self.DF_ADDITIONAL_FRAME:
            apdu_af = [self.CLA, self.DF_ADDITIONAL_FRAME, 0x00, 0x00, le]
            response_data, status = self._transmit(apdu_af)
            full_response.extend(response_data)

        if status != self.DF_OPERATION_OK:
            logger.error(f"Failed to read data: {self.get_error_message(status)}")
            raise Exception(f"Failed to read data: {self.get_error_message(status)}")

        logger.info(f"✅ Read {len(full_response)} bytes successfully.")
    
        return bytes(full_response[:data_length])
