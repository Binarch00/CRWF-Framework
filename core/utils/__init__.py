import random
import string
import hashlib


def random_string(length):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for i in range(length))


def hash_maker(secret, salt=""):
    result = (secret + salt).encode('utf-8')
    return hashlib.sha1(result).hexdigest()
