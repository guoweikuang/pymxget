import asyncio
import unittest

from mxget.provider import kugou


def async_test(f):
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(f(*args, **kwargs))

    return wrapper


class TestKuGou(unittest.TestCase):
    @async_test
    async def test_search_songs(self):
        async with kugou.KuGou() as client:
            resp = await client.search_songs('五月天')
            self.assertIsNotNone(resp)

    @async_test
    async def test_get_song(self):
        async with kugou.KuGou() as client:
            resp = await client.get_song('1571941D82D63AD614E35EAD9DB6A6A2')
            self.assertIsNotNone(resp)

    @async_test
    async def test_get_artist(self):
        async with kugou.KuGou() as client:
            resp = await client.get_artist('8965')
            self.assertIsNotNone(resp)

    @async_test
    async def test_get_album(self):
        async with kugou.KuGou() as client:
            resp = await client.get_album('976965')
            self.assertIsNotNone(resp)

    @async_test
    async def test_get_playlist(self):
        async with kugou.KuGou() as client:
            resp = await client.get_playlist('610433')
            self.assertIsNotNone(resp)

    @async_test
    async def test_get_song_url(self):
        async with kugou.KuGou() as client:
            resp = await client.get_song_url('1571941D82D63AD614E35EAD9DB6A6A2')
            self.assertIsNotNone(resp)

    @async_test
    async def test_get_song_lyric(self):
        async with kugou.KuGou() as client:
            resp = await client.get_song_lyric('1571941D82D63AD614E35EAD9DB6A6A2')
            self.assertIsNotNone(resp)


if __name__ == '__main__':
    unittest.main()
