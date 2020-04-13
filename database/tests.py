import unittest
from unittest import mock
import hashlib
import database
from database.models import TestModel, User, UserTransactions, CryptoAddress
from services.btc_address_generator import generate_address
import core.utils.emails


class TestDatabaseMethods(unittest.TestCase):

    def setUp(self) -> None:
        self.session = database.Session()

    def test_TestModel(self):
        ed_test = TestModel(
            name='ed', fullname='Ed Jones', nickname='edsnickname')
        self.session.add(ed_test)
        self.session.commit()
        our_item = self.session.query(TestModel).filter_by(name='ed').first()
        assert our_item
        self.assertEqual(our_item.nickname, 'edsnickname')


class TestUser(unittest.TestCase):

    def setUp(self) -> None:
        self.session = database.Session()
        self.session.query(User).filter_by(email='test@test.com').delete()
        self.session.commit()
        # generate_address(2)

    @mock.patch('core.utils.emails.send_email', return_value=True)
    @mock.patch('flask.render_template', return_value=True)
    def test_add_user(self, mk, mk1):
        User.add_user("test@test.com", "any")
        our_item = self.session.query(User).filter_by(email='test@test.com').first()
        self.assertEqual(our_item.password, hashlib.sha1(("any" + User.SALT).encode('utf-8')).hexdigest())

        assert CryptoAddress.get_address_by_user(our_item.id)

    @mock.patch('core.utils.emails.send_email', return_value=True)
    @mock.patch('flask.render_template', return_value=True)
    def test_login(self, mk, mk1):
        User.add_user("test@test.com", "any")
        assert User.login("test@test.com", "any")
        assert not User.login("test@test.com", "anyXX")


class TestUserTransactions(unittest.TestCase):

    def setUp(self) -> None:
        self.session = database.Session()
        self.session.query(User).filter_by(email='test@test.com').delete()
        self.session.query(UserTransactions).delete()
        self.session.commit()

    def test_transactions(self):
        User.add_user("test@test.com", "any")
        our_item = self.session.query(User).filter_by(email='test@test.com').first()
        self.assertEqual(UserTransactions.get_user_netbalance(our_item.id), 0.0)

        UserTransactions.add_transaction(our_item.id, 0.025, "deposit")
        self.assertEqual(UserTransactions.get_user_netbalance(our_item.id), 0.025)

        UserTransactions.add_transaction(our_item.id, 0.025, "deposit")
        self.assertEqual(UserTransactions.get_user_netbalance(our_item.id), 0.05)

        UserTransactions.add_transaction(our_item.id, -0.025, "consume")
        self.assertEqual(UserTransactions.get_user_netbalance(our_item.id), 0.025)

        UserTransactions.add_transaction(our_item.id, -0.025, "consume")
        self.assertEqual(UserTransactions.get_user_netbalance(our_item.id), 0.0)


if __name__ == '__main__':
    unittest.main()
