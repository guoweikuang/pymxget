import asyncio
import unittest

from mxget.provider import migu


class TestMiGu(unittest.TestCase):
    def setUp(self) -> None:
        self.loop = asyncio.get_event_loop()

    def test_search_song(self):
        resp = self.loop.run_until_complete(migu.search_song('周杰伦'))
        self.assertIsNotNone(resp)

    def test_get_song(self):
        resp = self.loop.run_until_complete(migu.get_song('63273402938'))
        self.assertIsNotNone(resp)

    def test_get_artist(self):
        resp = self.loop.run_until_complete(migu.get_artist('112'))
        self.assertIsNotNone(resp)

    def test_get_album(self):
        resp = self.loop.run_until_complete(migu.get_album('1121438701'))
        self.assertIsNotNone(resp)

    def test_get_playlist(self):
        resp = self.loop.run_until_complete(migu.get_playlist('159248239'))
        self.assertIsNotNone(resp)


if __name__ == '__main__':
    unittest.main()
