import asyncio
import unittest

from mxget.provider import xiami


def async_test(f):
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(f(*args, **kwargs))

    return wrapper


class TestXiaMi(unittest.TestCase):
    @async_test
    async def test_search_songs(self):
        async with xiami.XiaMi() as client:
            resp = await client.search_songs('五月天')
            self.assertIsNotNone(resp)

    @async_test
    async def test_get_song(self):
        async with xiami.XiaMi() as client:
            resp = await client.get_song('xMPr7Lbbb28')
            self.assertIsNotNone(resp)

    @async_test
    async def test_get_artist(self):
        async with xiami.XiaMi() as client:
            resp = await client.get_artist('3110')
            self.assertIsNotNone(resp)

    @async_test
    async def test_get_album(self):
        async with xiami.XiaMi() as client:
            resp = await client.get_album('nmTM4c70144')
            self.assertIsNotNone(resp)

    @async_test
    async def test_get_playlist(self):
        async with xiami.XiaMi() as client:
            resp = await client.get_playlist('8007523')
            self.assertIsNotNone(resp)

    @async_test
    async def test_get_song_lyric(self):
        async with xiami.XiaMi() as client:
            resp = await client.get_playlist('xMPr7Lbbb28')
            self.assertIsNotNone(resp)


if __name__ == '__main__':
    unittest.main()
