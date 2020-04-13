import unittest
from core.utils.cached_objects import UserCH
import cache
import database
from database.models import User



class TestCachedObjectsMethods(unittest.TestCase):

    def setUp(self) -> None:
        self.session = database.Session()
        self.session.query(User).filter_by(email='test@test.com').delete()
        self.session.commit()

    def test_user(self):
        User.add_user("test@test.com", "any")
        our_item = self.session.query(User).filter_by(email='test@test.com').first()
        usr = UserCH(our_item.id)
        self.assertEqual(usr.email, "test@test.com")
        self.assertEqual(cache.get_object("cached/{}/{}".format(usr.db_table, usr.id)), usr._data)
