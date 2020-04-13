"""
crypto gateway IPN client
https://github.com/Binarch00/crypto_gateway
"""

import requests
from settings import CRYPTO_GATEWAY_SERVER, logger, SERVER_NAME


# TODO: move to https
def subscribe(address, coin="btc"):
    try:
        url = "http://{}/btc_ipn".format(CRYPTO_GATEWAY_SERVER)
        data = {
            "address": address,
            "max_confirms": 1,
            "url": "http://{}/ipn".format(SERVER_NAME)
        }
        res = requests.post(url=url, data=data)
        if res.content.strip().count(b"success") >= 1:
            return True
        else:
            logger.error("Address {} subscription fail: {}".format(address, res.content[:30]))
    except Exception as ex:
        logger.exception(ex)
    return False
