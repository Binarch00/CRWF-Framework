import unittest
from crypto import RSATools
import os


class TestRSATools(unittest.TestCase):

    def setUp(self) -> None:
        RSATools.gen_keys(passphrase="123", prv_file="test_private.pem", pub_file="test_public.pem")

    def tearDown(self) -> None:
        os.remove("test_public.pem")
        os.remove("test_private.pem")

    def test_RSA(self):
        rc = RSATools(pub_key="test_public.pem", prv_key="test_private.pem", passphrase="123")
        in_str = """This is a long test string
        line #2 
        line #3
        end
        """
        enc = rc.encrypt(in_str)
        out_str = rc.decrypt(enc)
        self.assertEqual(in_str, out_str)
