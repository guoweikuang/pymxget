import asyncio
import unittest

from mxget.provider import kuwo


def async_test(f):
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(f(*args, **kwargs))

    return wrapper


class TestKuWo(unittest.TestCase):
    @async_test
    async def test_search_songs(self):
        async with kuwo.KuWo() as client:
            resp = await client.search_songs('周杰伦')
            self.assertIsNotNone(resp)

    @async_test
    async def test_get_song(self):
        async with kuwo.KuWo() as client:
            resp = await client.get_song('76323299')
            self.assertIsNotNone(resp)

    @async_test
    async def test_get_artist(self):
        async with kuwo.KuWo() as client:
            resp = await client.get_artist('336')
            self.assertIsNotNone(resp)

    @async_test
    async def test_get_album(self):
        async with kuwo.KuWo() as client:
            resp = await client.get_album('10685968')
            self.assertIsNotNone(resp)

    @async_test
    async def test_get_playlist(self):
        async with kuwo.KuWo() as client:
            resp = await client.get_playlist('1085247459')
            self.assertIsNotNone(resp)

    @async_test
    async def test_get_song_url(self):
        async with kuwo.KuWo() as client:
            resp = await client.get_song_url('76323299')
            self.assertIsNotNone(resp)

    @async_test
    async def test_get_song_lyric(self):
        async with kuwo.KuWo() as client:
            resp = await client.get_song_lyric('76323299')
            self.assertIsNotNone(resp)


if __name__ == '__main__':
    unittest.main()
