import asyncio
import unittest

from mxget.provider import kuwo


class TestKuWo(unittest.TestCase):
    def setUp(self) -> None:
        self.loop = asyncio.get_event_loop()

    def test_search_song(self):
        resp = self.loop.run_until_complete(kuwo.search_songs('周杰伦'))
        self.assertIsNotNone(resp)

    def test_get_song(self):
        resp = self.loop.run_until_complete(kuwo.get_song('76323299'))
        self.assertIsNotNone(resp)

    def test_get_artist(self):
        resp = self.loop.run_until_complete(kuwo.get_artist('336'))
        self.assertIsNotNone(resp)

    def test_get_album(self):
        resp = self.loop.run_until_complete(kuwo.get_album('10685968'))
        self.assertIsNotNone(resp)

    def test_get_playlist(self):
        resp = self.loop.run_until_complete(kuwo.get_playlist('1085247459'))
        self.assertIsNotNone(resp)

    def test_get_song_url(self):
        resp = self.loop.run_until_complete(kuwo.get_song_url('76323299'))
        self.assertIsNotNone(resp)

    def test_get_song_lyric(self):
        resp = self.loop.run_until_complete(kuwo.get_song_lyric('76323299'))
        self.assertIsNotNone(resp)


if __name__ == '__main__':
    unittest.main()
