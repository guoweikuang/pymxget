import asyncio
import unittest

from mxget.provider import qq


class TestQQ(unittest.TestCase):
    def setUp(self) -> None:
        self.loop = asyncio.get_event_loop()

    def test_search_song(self):
        resp = self.loop.run_until_complete(qq.search_song('五月天'))
        self.assertIsNotNone(resp)

    def test_get_song(self):
        resp = self.loop.run_until_complete(qq.get_song('002Zkt5S2z8JZx'))
        self.assertIsNotNone(resp)

    def test_get_artist(self):
        resp = self.loop.run_until_complete(qq.get_artist('000Sp0Bz4JXH0o'))
        self.assertIsNotNone(resp)

    def test_get_album(self):
        resp = self.loop.run_until_complete(qq.get_album('002fRO0N4FftzY'))
        self.assertIsNotNone(resp)

    def test_get_playlist(self):
        resp = self.loop.run_until_complete(qq.get_playlist('5474239760'))
        self.assertIsNotNone(resp)

    def test_get_song_url(self):
        resp = self.loop.run_until_complete(qq.get_song_url('002Zkt5S2z8JZx', '002Zkt5S2z8JZx'))
        self.assertIsNotNone(resp)

    def test_get_song_lyric(self):
        resp = self.loop.run_until_complete(qq.get_song_lyric('002Zkt5S2z8JZx'))
        self.assertIsNotNone(resp)


if __name__ == '__main__':
    unittest.main()
