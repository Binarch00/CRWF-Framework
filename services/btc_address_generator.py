from crypto import RSATools
from crypto.btc import gen_btc_keys
from database.models import CryptoAddress
import database


# TODO: add some auto-grow conditions

session = database.Session()
PASSWORD = "1234567890"
PUB_KEY_FILE = "public.pem"


RSATools.gen_keys(size=4028, passphrase=PASSWORD, pub_file=PUB_KEY_FILE)
rc = RSATools("public.pem", passphrase=PASSWORD)


def generate_address(amount=10):
    global rc
    for i in range(0, amount, 1):
        keys = gen_btc_keys()
        btc_add = CryptoAddress(public_key=keys["public"], private_key=rc.encrypt(keys["private"]))
        session.add(btc_add)
        session.commit()


if __name__ == "__main__":
    generate_address(10)
