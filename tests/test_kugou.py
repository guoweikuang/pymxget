import asyncio
import unittest

from mxget.provider import kugou


class TestKuGou(unittest.TestCase):
    def setUp(self) -> None:
        self.loop = asyncio.get_event_loop()

    def test_search_song(self):
        resp = self.loop.run_until_complete(kugou.search_songs('五月天'))
        self.assertIsNotNone(resp)

    def test_get_song(self):
        resp = self.loop.run_until_complete(kugou.get_song('1571941D82D63AD614E35EAD9DB6A6A2'))
        self.assertIsNotNone(resp)

    def test_get_artist(self):
        resp = self.loop.run_until_complete(kugou.get_artist('8965'))
        self.assertIsNotNone(resp)

    def test_get_album(self):
        resp = self.loop.run_until_complete(kugou.get_album('976965'))
        self.assertIsNotNone(resp)

    def test_get_playlist(self):
        resp = self.loop.run_until_complete(kugou.get_playlist('610433'))
        self.assertIsNotNone(resp)

    def test_get_song_url(self):
        resp = self.loop.run_until_complete(kugou.get_song_url('1571941D82D63AD614E35EAD9DB6A6A2'))
        self.assertIsNotNone(resp)

    def test_get_song_lyric(self):
        resp = self.loop.run_until_complete(kugou.get_song_lyric('1571941D82D63AD614E35EAD9DB6A6A2'))
        self.assertIsNotNone(resp)


if __name__ == '__main__':
    unittest.main()
