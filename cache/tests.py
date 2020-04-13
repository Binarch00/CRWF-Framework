import unittest
import cache


class TestCacheMethods(unittest.TestCase):

    def test_set_get_object(self):
        data = {
            "A": 1,
            "B": 2
        }
        cache.set_object("test1", data)
        self.assertEqual(cache.get_object("test1"), data)
