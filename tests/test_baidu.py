import asyncio
import unittest

from mxget.provider import baidu


def async_test(f):
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(f(*args, **kwargs))

    return wrapper


class TestBaiDu(unittest.TestCase):
    @async_test
    async def test_search_songs(self):
        async with baidu.BaiDu() as client:
            resp = await client.search_songs('五月天')
            self.assertIsNotNone(resp)

    @async_test
    async def test_get_song(self):
        async with baidu.BaiDu() as client:
            resp = await client.get_song('1686649')
            self.assertIsNotNone(resp)

    @async_test
    async def test_get_artist(self):
        async with baidu.BaiDu() as client:
            resp = await client.get_artist('1557')
            self.assertIsNotNone(resp)

    @async_test
    async def test_get_album(self):
        async with baidu.BaiDu() as client:
            resp = await client.get_album('946499')
            self.assertIsNotNone(resp)

    @async_test
    async def test_get_playlist(self):
        async with baidu.BaiDu() as client:
            resp = await client.get_playlist('566347665')
            self.assertIsNotNone(resp)


if __name__ == '__main__':
    unittest.main()
