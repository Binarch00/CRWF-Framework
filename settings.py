import logging


DB = {
    "engine": "sqlite",
    "file": "///main.db",
    "username": "",
    "password": "",
    "host": "",
    "database": ""
}

RABBIT = {
    "host": "127.0.0.1",
    "port": 5672,
    "user": "guest",
    "passw": "guest"
}

CACHE = {
    "host": "127.0.0.1",
    "port": 6379
}

CRYPTO_GATEWAY_SERVER = "127.0.0.1:8081"

LOG_LEVEL = logging.DEBUG


def setup_logger(level=LOG_LEVEL):
    logger = logging.getLogger('main')
    logger.setLevel(level)
    fh = logging.FileHandler("service.log")
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - {%(pathname)s:%(lineno)d} - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


logger = setup_logger()

SERVER_NAME = "crwf-framework.io:8080"
SERVICE_NAME = "Crypto Ready Framework"

IPN_AUTH = "IPN-Auth1"
SECRET = "s98fu3@98rhfjn3+98y0ryhf8ufqh87ytnaihw74h+"

GOOGLE_CAPTCHA = {
    "sitekey": "6Le4_OUUAAAAAJNUIto3woplV5VDLU96YumbU4MO",
    "secret": "6Le4_OUUAAAAABIZXWcIeBRaYfUpNeEFRlIpiMAE"
}

SMTP = {
    "host": 'smtp.gmail.com',
    "port": 465,
    "user": "",
    "password": "",
    "default_sender": "noreply@test.com"
}
