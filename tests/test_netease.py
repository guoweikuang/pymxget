import asyncio
import unittest

from mxget.provider import netease


class TestNetEase(unittest.TestCase):
    def setUp(self) -> None:
        self.loop = asyncio.get_event_loop()

    def test_search_song(self):
        resp = self.loop.run_until_complete(netease.search_song('alone'))
        self.assertIsNotNone(resp)

    def test_get_song(self):
        resp = self.loop.run_until_complete(netease.get_song('444269135'))
        self.assertIsNotNone(resp)

    def test_get_artist(self):
        resp = self.loop.run_until_complete(netease.get_artist('1045123'))
        self.assertIsNotNone(resp)

    def test_get_album(self):
        resp = self.loop.run_until_complete(netease.get_album('35023284'))
        self.assertIsNotNone(resp)

    def test_get_playlist(self):
        resp = self.loop.run_until_complete(netease.get_playlist('156934569'))
        self.assertIsNotNone(resp)

    def test_get_song_url(self):
        resp = self.loop.run_until_complete(netease.get_song_url('444269135'))
        self.assertIsNotNone(resp)

    def test_get_song_lyric(self):
        resp = self.loop.run_until_complete(netease.get_song_lyric('444269135'))
        self.assertIsNotNone(resp)


if __name__ == '__main__':
    unittest.main()
