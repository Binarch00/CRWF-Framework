import redis
import json

from settings import CACHE


def get_redis(db=0):
    return redis.Redis(host=CACHE["host"], port=CACHE["port"], db=db)


redis_con = get_redis()


def get_object(key):
    global redis_con
    data = redis_con.get(key)
    return json.loads(data) if data else {}


def set_object(key, data, ttl=600):
    global redis_con
    if type(data) is not dict:
        raise ValueError("Dict object required as data")
    return redis_con.set(key, json.dumps(data), ex=ttl)
