import asyncio
import unittest

from mxget.provider import qq


def async_test(f):
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(f(*args, **kwargs))

    return wrapper


class TestQQ(unittest.TestCase):
    @async_test
    async def test_search_songs(self):
        async with qq.QQ() as client:
            resp = await client.search_songs('五月天')
            self.assertIsNotNone(resp)

    @async_test
    async def test_get_song(self):
        async with qq.QQ() as client:
            resp = await client.get_song('002Zkt5S2z8JZx')
            self.assertIsNotNone(resp)

    @async_test
    async def test_get_artist(self):
        async with qq.QQ() as client:
            resp = await client.get_artist('000Sp0Bz4JXH0o')
            self.assertIsNotNone(resp)

    @async_test
    async def test_get_album(self):
        async with qq.QQ() as client:
            resp = await client.get_album('002fRO0N4FftzY')
            self.assertIsNotNone(resp)

    @async_test
    async def test_get_playlist(self):
        async with qq.QQ() as client:
            resp = await client.get_playlist('5474239760')
            self.assertIsNotNone(resp)

    @async_test
    async def test_get_song_url(self):
        async with qq.QQ() as client:
            resp = await client.get_song_url('002Zkt5S2z8JZx', '002Zkt5S2z8JZx')
            self.assertIsNotNone(resp)

    @async_test
    async def test_get_song_lyric(self):
        async with qq.QQ() as client:
            resp = await client.get_song_lyric('002Zkt5S2z8JZx')
            self.assertIsNotNone(resp)


if __name__ == '__main__':
    unittest.main()
