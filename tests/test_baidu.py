import asyncio
import unittest

from mxget.provider import baidu


class TestKuWo(unittest.TestCase):
    def setUp(self) -> None:
        self.loop = asyncio.get_event_loop()

    def test_search_song(self):
        resp = self.loop.run_until_complete(baidu.search_songs('五月天'))
        self.assertIsNotNone(resp)

    def test_get_song(self):
        resp = self.loop.run_until_complete(baidu.get_song('1686649'))
        self.assertIsNotNone(resp)

    def test_get_artist(self):
        resp = self.loop.run_until_complete(baidu.get_artist('1557'))
        self.assertIsNotNone(resp)

    def test_get_album(self):
        resp = self.loop.run_until_complete(baidu.get_album('946499'))
        self.assertIsNotNone(resp)

    def test_get_playlist(self):
        resp = self.loop.run_until_complete(baidu.get_playlist('566347665'))
        self.assertIsNotNone(resp)


if __name__ == '__main__':
    unittest.main()
