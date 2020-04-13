import cache
import database
from settings import logger
from database.models import UserTransactions, CryptoAddress


class CachedObject:
    db_table = "none"
    db_id = "id"
    TTL = 600

    def __init__(self, id):
        self.id = id
        self._load_cache()
        if not self._data:
            self._load_database(refresh=True)

    def refresh_data(self):
        """Update the cache with fresh database info"""
        self._load_database(refresh=True)

    def _load_database(self, refresh=False):
        try:
            session = database.Session()
            query = 'SELECT * FROM {} WHERE {} = :val LIMIT 1'.format(self.db_table, self.db_id)
            result = session.execute(query, {'val': self.id})
            self._data = dict(result.first().items())
            if refresh:
                if self._data:
                    key = "cached/{}/{}".format(self.db_table, self.id)
                    cache.set_object(key, self._data, ttl=self.TTL)
                else:
                    raise ValueError("Invalid user id: {}".format(self.id))

        except Exception as ex:
            logger.exception(ex)

    def _load_cache(self):
        key = "cached/{}/{}".format(self.db_table, self.id)
        cdata = cache.get_object(key)
        if cdata:
            self._data = cdata
        else:
            self._data = {}

    def __getattr__(self, item):
        return self._data.get(item)


class UserCH(CachedObject):
    db_table = "users"

    def btc_balance(self):
        key = "user-netbalance/{}".format(self.id)
        net_balance = 0.0
        try:
            net_balance = float(cache.redis_con.get(key))
        except TypeError:
            net_balance = UserTransactions.get_user_netbalance(self.id)
            cache.redis_con.set(key, net_balance, 10)
        return net_balance

    def btc_address(self):
        return CryptoAddress.get_address_by_user(self.id)
