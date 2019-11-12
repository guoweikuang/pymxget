import asyncio
import unittest

from mxget.provider import migu


def async_test(f):
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(f(*args, **kwargs))

    return wrapper


class TestMiGu(unittest.TestCase):
    @async_test
    async def test_search_songs(self):
        async with migu.MiGu() as client:
            resp = await client.search_songs('周杰伦')
            self.assertIsNotNone(resp)

    @async_test
    async def test_get_song(self):
        async with migu.MiGu() as client:
            resp = await client.get_song('63273402938')
            self.assertIsNotNone(resp)

    @async_test
    async def test_get_artist(self):
        async with migu.MiGu() as client:
            resp = await client.get_artist('112')
            self.assertIsNotNone(resp)

    @async_test
    async def test_get_album(self):
        async with migu.MiGu() as client:
            resp = await client.get_album('1121438701')
            self.assertIsNotNone(resp)

    @async_test
    async def test_get_playlist(self):
        async with migu.MiGu() as client:
            resp = await client.get_playlist('159248239')
            self.assertIsNotNone(resp)


if __name__ == '__main__':
    unittest.main()
