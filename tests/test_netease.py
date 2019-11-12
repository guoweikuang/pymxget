import asyncio
import unittest

from mxget.provider import netease


def async_test(f):
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(f(*args, **kwargs))

    return wrapper


class TestNetEase(unittest.TestCase):
    @async_test
    async def test_search_songs(self):
        async with netease.NetEase() as client:
            resp = await client.search_songs('alone')
            self.assertIsNotNone(resp)

    @async_test
    async def test_get_song(self):
        async with netease.NetEase() as client:
            resp = await client.get_song('444269135')
            self.assertIsNotNone(resp)

    @async_test
    async def test_get_artist(self):
        async with netease.NetEase() as client:
            resp = await client.get_artist('1045123')
            self.assertIsNotNone(resp)

    @async_test
    async def test_get_album(self):
        async with netease.NetEase() as client:
            resp = await client.get_album('35023284')
            self.assertIsNotNone(resp)

    @async_test
    async def test_get_playlist(self):
        async with netease.NetEase() as client:
            resp = await client.get_playlist('156934569')
            self.assertIsNotNone(resp)

    @async_test
    async def test_get_song_url(self):
        async with netease.NetEase() as client:
            resp = await client.get_song_url('444269135')
            self.assertIsNotNone(resp)

    @async_test
    async def test_get_song_lyric(self):
        async with netease.NetEase() as client:
            resp = await client.get_song_lyric('444269135')
            self.assertIsNotNone(resp)


if __name__ == '__main__':
    unittest.main()
