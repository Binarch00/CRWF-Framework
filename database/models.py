import hashlib
import datetime
import time
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime
Base = declarative_base()

import database
from core.utils import random_string, hash_maker, emails
from core import crypto_ipn_client
import cache
from settings import logger, SERVER_NAME, SMTP, SERVICE_NAME, SECRET
from flask import render_template, flash, url_for


class TestModel(Base):
    __tablename__ = 'testmodel'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    fullname = Column(String)
    nickname = Column(String)

    def __repr__(self):
        return "<TestData(name='%s', fullname='%s', nickname='%s')>" % (
            self.name, self.fullname, self.nickname)


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True)
    password = Column(String)
    api_key = Column(String, unique=True)
    SALT = "SJh5HDd2AI"
    vcode = Column(String)

    @staticmethod
    def gen_forgot(id, tm=None):
        if not tm:
            tm = int(time.time())
        tm = str(tm)
        data = "{}{}{}{}".format(id, SECRET, "salt-452341", tm)
        data = data.encode()
        return "{}/{}".format(hashlib.md5(data).hexdigest(), tm)

    @staticmethod
    def forgot(email, session=None):
        if not session:
            session = database.Session()
        user1 = session.query(User).filter_by(email=email).first()
        flash("Check your email to start the password reset process.")
        if user1 and user1.id:
            fcode = User.gen_forgot(user1.id)
            reset_link = "http://{}/reset-auth/{}/{}".format(SERVER_NAME, user1.id, fcode)
            body = render_template("email_forgot.html", reset_link=reset_link)
            emails.send_email(
                None, to_=email, subject="Password Reset For [{}]".format(SERVICE_NAME), body_text=None, body_html=body)
            return True
        return False

    def is_verified(self):
        return not self.vcode

    @staticmethod
    def verify_user(vcode, session=None):
        if not session:
            session = database.Session()
        user1 = session.query(User).filter_by(vcode=vcode).first()
        if user1 and user1.id:
            user1.vcode = ""
            session.commit()
            return True
        return False

    @staticmethod
    def reset_user_password(id, password, session=None):
        try:
            if not session:
                session = database.Session()
            user1 = session.query(User).filter_by(id=id).first()
            user1.password = hash_maker(password, User.SALT)
            session.commit()
            return True
        except Exception as ex:
            logger.exception(ex)
        return False

    @staticmethod
    def add_user(email, password, session=None):
        try:
            if not session:
                session = database.Session()
            api_key = random_string(57)
            vcode = random_string(157)
            usr = User(
                email=email, api_key=api_key,
                password=hash_maker(password, User.SALT), vcode=vcode)
            session.add(usr)
            session.commit()

            # Prepare confirm email to send
            activation_link = "http://{}/activate/{}".format(SERVER_NAME, vcode)
            body = render_template("email_confirm.html", activation_link=activation_link)
            emails.send_email(
                None, to_=email, subject="Account Activation [{}]".format(SERVICE_NAME), body_text=None, body_html=body)
            return True
        except Exception as ex:
            logger.exception(ex)
        return False

    @staticmethod
    def link_crypto_address(user_id, session=None, ipn_subscribe=True):
        """Assign a crypto address to the user and subscribe address to IPN notifications"""
        if not session:
            session = database.Session()
        CryptoAddress.assign_address(user_id, session=session)
        address = CryptoAddress.get_address_by_user(user_id, session=session)
        if not address:
            logger.error("Not address assigned to user {}".format(user_id))
            return False
        return crypto_ipn_client.subscribe(address) if ipn_subscribe else True

    @staticmethod
    def login(email, password, session=None):
        password = hash_maker(password, User.SALT)
        key = "auth/{}/{}".format(email, password)
        user1 = cache.redis_con.get(key)
        if user1:
            return int(user1)
        if not session:
            session = database.Session()
        user1 = session.query(User).filter_by(email=email, password=password).first()
        if user1 and user1.id and not user1.is_verified():
            return -1
        if user1 and user1.id:
            cache.redis_con.set(key, user1.id, ex=600)
            return user1.id
        return False

    @staticmethod
    def login_api(api_key, session=None):
        key = "auth_api/{}".format(api_key)
        user1 = cache.redis_con.get(key)
        if user1:
            return int(user1)
        if not session:
            session = database.Session()
        user1 = session.query(User).filter_by(api_key=api_key).first()
        if user1 and user1.id:
            cache.redis_con.set(key, user1.id, ex=600)
            return user1.id
        return False

    def __repr__(self):
        return "<User(id={}, email={})>".format(self.id, self.email)


class CryptoAddress(Base):
    __tablename__ = 'crypto_address'
    id = Column(Integer, primary_key=True, autoincrement=True)
    public_key = Column(String, unique=True)
    private_key = Column(String, unique=True)
    crypto_type = Column(String, default="btc")
    user = Column(Integer, default=0)
    assigned_date = Column(DateTime, default=None)

    @staticmethod
    def get_address_user(address, crypto_type="btc", session=None):
        if not session:
            session = database.Session()
        query = """
         SELECT user FROM crypto_address 
         WHERE public_key='{}' AND crypto_type='{}'
         LIMIT 1
        """.format(address, crypto_type)
        rs = session.execute(query)
        data = rs.fetchone()
        return data[0] if data and data[0] else None

    @staticmethod
    def get_address_by_user(user, crypto_type="btc", session=None):
        if not session:
            session = database.Session()
        query = """
             SELECT public_key FROM crypto_address 
             WHERE user='{}' AND crypto_type='{}'
             ORDER BY assigned_date ASC
             LIMIT 1
            """.format(user, crypto_type)
        rs = session.execute(query)
        data = rs.fetchone()
        return data[0] if data and data[0] else None

    @staticmethod
    def assign_address(user_id, crypto_type="btc", session=None):
        if not session:
            session = database.Session()
        prev = CryptoAddress.get_address_by_user(user_id, crypto_type=crypto_type, session=session)
        if not prev:
            query = """
            UPDATE crypto_address 
              SET user={user_id}, assigned_date=datetime()
            WHERE user=0 AND crypto_type='{crypto_type}'
            LIMIT 1
            """.format(user_id=user_id, crypto_type=crypto_type)
            session.execute(query)
            session.commit()
            return True
        else:
            logger.warning("User {} already have one assigned address.".format(user_id))
            return False


class UserTransactions(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user = Column(Integer, index=True)
    amount = Column(Float)
    trans_type = Column(String, index=True)
    coin = Column(String, index=True, default="btc")
    added_date = Column(DateTime, default=datetime.datetime.utcnow)
    reference = Column(String)

    @staticmethod
    def get_user_netdeposits(user, coin="btc", session=None):
        """
        Get net user deposits excluding consumes.
        :return: net user deposits
        """
        try:
            assert user > 0
            assert coin in ["btc"]

            if not session:
                session = database.Session()

            query = """
                      SELECT SUM(amount) AS total
                      FROM transactions
                      WHERE user={} AND coin='{}' AND trans_type='deposit' 
                    """.format(user, coin)
            rs = session.execute(query)
            data = rs.fetchone()
            return float(data[0]) if data and data[0] else 0.0
        except Exception as ex:
            logger.exception(ex)


    @staticmethod
    def get_user_netbalance(user, coin="btc", session=None):
        """
        Get net user balance, deposits - consumes
        :return: net user balance
        """
        try:
            assert user > 0
            assert coin in ["btc"]

            if not session:
                session = database.Session()

            query = """
                      SELECT SUM(amount) AS total
                      FROM transactions
                      WHERE user={} AND coin='{}'
                    """.format(user, coin)
            rs = session.execute(query)
            data = rs.fetchone()
            return float(data[0]) if data and data[0] else 0.0
        except Exception as ex:
            logger.exception(ex)

    @staticmethod
    def add_transaction(user, amount, trans_type, reference="", coin="btc", session=None):
        try:
            assert coin in ['btc']
            assert trans_type in ['deposit', 'consume']
            assert amount != 0
            assert user >= 0

            if not session:
                session = database.Session()

            usrt = UserTransactions(
                user=user,
                amount=amount,
                trans_type=trans_type,
                reference=reference,
                coin=coin
            )
            session.add(usrt)
            session.commit()
        except Exception as ex:
            logger.exception(ex)


def init_models():
    Base.metadata.create_all(database.engine)


if __name__ == "__main__":
    init_models()
