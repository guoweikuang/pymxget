import asyncio
import unittest

from mxget.provider import xiami


class TestKuWo(unittest.TestCase):
    def setUp(self) -> None:
        self.loop = asyncio.get_event_loop()

    def test_search_song(self):
        resp = self.loop.run_until_complete(xiami.search_songs('五月天'))
        self.assertIsNotNone(resp)

    def test_get_song(self):
        resp = self.loop.run_until_complete(xiami.get_song('xMPr7Lbbb28'))
        self.assertIsNotNone(resp)

    def test_get_artist(self):
        resp = self.loop.run_until_complete(xiami.get_artist('3110'))
        self.assertIsNotNone(resp)

    def test_get_album(self):
        resp = self.loop.run_until_complete(xiami.get_album('nmTM4c70144'))
        self.assertIsNotNone(resp)

    def test_get_playlist(self):
        resp = self.loop.run_until_complete(xiami.get_playlist('8007523'))
        self.assertIsNotNone(resp)

    def test_get_song_lyric(self):
        resp = self.loop.run_until_complete(xiami.get_song_lyric('xMPr7Lbbb28'))
        self.assertIsNotNone(resp)


if __name__ == '__main__':
    unittest.main()
