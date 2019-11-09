import asyncio
import hashlib
import json
import random
import typing

import aiohttp

from mxget import (
    api,
    exceptions,
)

__all__ = [
    'search_songs',
    'get_song',
    'get_artist',
    'get_album',
    'get_playlist',
    'get_song_url',
    'get_song_lyric',
]

_API_SEARCH = 'http://mobilecdn.kugou.com/api/v3/search/song'
_API_GET_SONG = 'http://m.kugou.com/app/i/getSongInfo.php?cmd=playInfo'
_API_GET_SONG_URL = 'http://trackercdn.kugou.com/i/v2/?pid=2&behavior=play&cmd=25'
_API_GET_SONG_LYRIC = 'http://m.kugou.com/app/i/krc.php?cmd=100&timelength=1'
_API_GET_ARTIST_INFO = 'http://mobilecdn.kugou.com/api/v3/singer/info'
_API_GET_ARTIST_SONGS = 'http://mobilecdn.kugou.com/api/v3/singer/song'
_API_GET_ALBUM_INFO = 'http://mobilecdn.kugou.com/api/v3/album/info'
_API_GET_ALBUM_SONGS = 'http://mobilecdn.kugou.com/api/v3/album/song'
_API_GET_PLAYLIST_INFO = 'http://mobilecdn.kugou.com/api/v3/special/info'
_API_GET_PLAYLIST_SONGS = 'http://mobilecdn.kugou.com/api/v3/special/song'


def _resolve(*songs: dict) -> typing.List[api.Song]:
    return [
        api.Song(
            name=song['songName'].strip(),
            artist=song['choricSinger'].replace('、', '/').strip(),
            album=song.get('album_name', '').strip(),
            pic_url=song['album_img'].replace('{size}', '480'),
            lyric=song.get('lyric'),
            url=song.get('url'),
        ) for song in songs if song.get('songName') is not None
    ]


class KuGou(api.API):
    def __init__(self, session: aiohttp.ClientSession = None):
        if session is None:
            session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=120),
            )
        self._session = session

    async def close(self):
        await self._session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def platform(self) -> api.Platform:
        return api.Platform.KuGou

    async def search_songs(self, keyword: str) -> api.SearchSongsResult:
        resp = await self.search_songs_raw(keyword)
        try:
            _songs = resp['data']['info']
        except KeyError:
            raise exceptions.DataError('search songs: no data')

        if not _songs:
            raise exceptions.DataError('search songs: no data')

        songs = [
            api.SearchSongsData(
                song_id=_song['hash'],
                name=_song['songname'].strip(),
                artist=_song['singername'].replace('、', '/').strip(),
                album=_song['album_name'].strip(),
            ) for _song in _songs
        ]
        return api.SearchSongsResult(keyword=keyword, count=len(songs), songs=songs)

    async def search_songs_raw(self, keyword: str, page: int = 1, page_size: int = 50) -> dict:
        params = {
            'keyword': keyword,
            'page': page,
            'pagesize': page_size,
        }

        try:
            _resp = await self.request('GET', _API_SEARCH, params=params)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('search songs: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            if resp['errcode'] != 0:
                raise exceptions.ResponseError('search songs: {}'.format(resp.get('error', resp['errcode'])))
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('search songs: {}'.format(e))

        return resp

    async def get_song(self, file_hash: str) -> api.Song:
        resp = await self.get_song_raw(file_hash)
        await self._patch_album_info(resp)
        await self._patch_song_lyric(resp)
        songs = _resolve(resp)
        return songs[0]

    async def get_song_raw(self, file_hash: str) -> dict:
        params = {
            'hash': file_hash,
        }

        try:
            _resp = await self.request('GET', _API_GET_SONG, params=params)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('get song: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            if resp['errcode'] != 0:
                raise exceptions.ResponseError('get song: {}'.format(resp.get('error', resp['errcode'])))
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('get song: {}'.format(e))

        return resp

    async def get_song_url(self, file_hash: str) -> typing.Optional[str]:
        try:
            resp = await self.get_song_url_raw(file_hash)
        except (exceptions.RequestError, exceptions.ResponseError):
            return None

        try:
            url = resp['url']
        except KeyError:
            return None

        return random.choice(url)

    async def get_song_url_raw(self, file_hash: str) -> dict:
        data = file_hash + 'kgcloudv2'
        key = hashlib.md5(data.encode('utf-8')).hexdigest()
        params = {
            'hash': file_hash,
            'key': key,
        }

        try:
            _resp = await self.request('GET', _API_GET_SONG_URL, params=params)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('get song url: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            if resp['status'] != 1:
                raise exceptions.ResponseError('get song url: {}'.format(resp.get('error', 'copyright protection')))
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('get song url: {}'.format(e))

        return resp

    async def get_song_lyric(self, file_hash: str) -> typing.Optional[str]:
        params = {
            'hash': file_hash,
        }

        try:
            resp = await self.request('GET', _API_GET_SONG_LYRIC, params=params)
            lyric = await resp.text()
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            return None

        return lyric if lyric else None

    async def _patch_song_info(self, *songs: dict) -> None:
        sem = asyncio.Semaphore(32)

        async def worker(song: dict):
            async with sem:
                try:
                    resp = await self.get_song_raw(song['hash'])
                except (exceptions.RequestError, exceptions.ResponseError):
                    return
                song['songName'] = resp['songName']
                song['singerId'] = resp['singerId']
                song['singerName'] = resp['singerName']
                song['choricSinger'] = resp['choricSinger']
                song['albumid'] = resp['albumid']
                song['album_img'] = resp['album_img']
                song['extra'] = resp['extra']
                song['url'] = resp['url']

        tasks = [asyncio.ensure_future(worker(song)) for song in songs]
        await asyncio.gather(*tasks)

    async def _patch_song_url(self, *songs: dict) -> None:
        sem = asyncio.Semaphore(32)

        async def worker(song: dict):
            async with sem:
                song['url'] = await self.get_song_url(song['hash'])

        tasks = [asyncio.ensure_future(worker(song)) for song in songs]
        await asyncio.gather(*tasks)

    async def _patch_song_lyric(self, *songs: dict) -> None:
        sem = asyncio.Semaphore(32)

        async def worker(song: dict):
            async with sem:
                song['lyric'] = await self.get_song_lyric(song['hash'])

        tasks = [asyncio.ensure_future(worker(song)) for song in songs]
        await asyncio.gather(*tasks)

    async def _patch_album_info(self, *songs: dict) -> None:
        sem = asyncio.Semaphore(32)

        async def worker(song: dict):
            async with sem:
                try:
                    resp = await self.get_album_info_raw(song['albumid'])
                    song['album_name'] = resp['data']['albumname']
                except (exceptions.RequestError, exceptions.ResponseError, KeyError):
                    pass

        tasks = [asyncio.ensure_future(worker(song)) for song in songs if song.get('albumid', 0) != 0]
        await asyncio.gather(*tasks)

    async def get_artist(self, singer_id: typing.Union[int, str]) -> api.Artist:
        artist_info = await self.get_artist__info_raw(singer_id)
        artist_song = await self.get_artist_songs_raw(singer_id)

        try:
            _songs = artist_song['data']['info']
        except KeyError:
            raise exceptions.DataError('get artist: no data')

        if not _songs:
            raise exceptions.DataError('get artist: no data')

        await self._patch_song_info(*_songs)
        await self._patch_album_info(*_songs)
        await self._patch_song_lyric(*_songs)
        songs = _resolve(*_songs)
        return api.Artist(
            name=artist_info['data']['singername'].strip(),
            pic_url=artist_info['data']['imgurl'].replace('{size}', '480'),
            count=len(songs),
            songs=songs
        )

    async def get_artist__info_raw(self, singer_id: typing.Union[int, str]) -> dict:
        params = {
            'singerid': singer_id,
        }

        try:
            _resp = await self.request('GET', _API_GET_ARTIST_INFO, params=params)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('get artist info: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            if resp['errcode'] != 0:
                raise exceptions.ResponseError('get artist info: {}'.format(resp.get('error', resp['errcode'])))
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('get artist info: {}'.format(e))

        return resp

    async def get_artist_songs_raw(self, singer_id: typing.Union[int, str],
                                   page: int = 1, page_size: int = 50) -> dict:
        params = {
            'singerid': singer_id,
            'page': page,
            'pagesize': page_size,
        }

        try:
            _resp = await self.request('GET', _API_GET_ARTIST_SONGS, params=params)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('get artist songs: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            if resp['errcode'] != 0:
                raise exceptions.ResponseError('get artist songs: {}'.format(resp.get('error', resp['errcode'])))
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('get artist songs: {}'.format(e))

        return resp

    async def get_album(self, album_id: typing.Union[int, str]) -> api.Album:
        album_info = await self.get_album_info_raw(album_id)
        album_song = await self.get_album_songs_raw(album_id)

        try:
            _songs = album_song['data']['info']
        except KeyError:
            raise exceptions.DataError('get album: no data')

        if not _songs:
            raise exceptions.DataError('get album: no data')

        await self._patch_song_info(*_songs)
        await self._patch_album_info(*_songs)
        await self._patch_song_lyric(*_songs)
        songs = _resolve(*_songs)
        return api.Album(
            name=album_info['data']['albumname'].strip(),
            pic_url=album_info['data']['imgurl'].replace('{size}', '480'),
            count=len(songs),
            songs=songs
        )

    async def get_album_info_raw(self, album_id: typing.Union[int, str]) -> dict:
        params = {
            'albumid': album_id,
        }

        try:
            _resp = await self.request('GET', _API_GET_ALBUM_INFO, params=params)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('get album info: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            if resp['errcode'] != 0:
                raise exceptions.ResponseError('get album info: {}'.format(resp.get('error', resp['errcode'])))
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('get album info: {}'.format(e))

        return resp

    async def get_album_songs_raw(self, album_id: typing.Union[int, str],
                                  page: int = 1, page_size: int = -1) -> dict:
        params = {
            'albumid': album_id,
            'page': page,
            'pagesize': page_size,
        }

        try:
            _resp = await self.request('GET', _API_GET_ALBUM_SONGS, params=params)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('get album songs: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            if resp['errcode'] != 0:
                raise exceptions.ResponseError('get album songs: {}'.format(resp.get('error', resp['errcode'])))
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('get album songs: {}'.format(e))

        return resp

    async def get_playlist(self, special_id: typing.Union[int, str]) -> api.Playlist:
        playlist_info = await self.get_playlist_info_raw(special_id)
        playlist_song = await self.get_playlist_songs_raw(special_id)

        try:
            _songs = playlist_song['data']['info']
        except KeyError:
            raise exceptions.DataError('get playlist: no data')

        if not _songs:
            raise exceptions.DataError('get playlist: no data')

        await self._patch_song_info(*_songs)
        await self._patch_album_info(*_songs)
        await self._patch_song_lyric(*_songs)
        songs = _resolve(*_songs)
        return api.Playlist(
            name=playlist_info['data']['specialname'].strip(),
            pic_url=playlist_info['data']['imgurl'].replace('{size}', '480'),
            count=len(songs),
            songs=songs
        )

    async def get_playlist_info_raw(self, special_id: typing.Union[int, str]) -> dict:
        params = {
            'specialid': special_id,
        }

        try:
            _resp = await self.request('GET', _API_GET_PLAYLIST_INFO, params=params)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('get playlist info: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            if resp['errcode'] != 0:
                raise exceptions.ResponseError('get playlist info: {}'.format(resp.get('error', resp['errcode'])))
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('get playlist info: {}'.format(e))

        return resp

    async def get_playlist_songs_raw(self, special_id: typing.Union[int, str],
                                     page: int = 1, page_size: int = -1) -> dict:
        params = {
            'specialid': special_id,
            'page': page,
            'pagesize': page_size,
        }

        try:
            _resp = await self.request('GET', _API_GET_PLAYLIST_SONGS, params=params)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('get playlist songs: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            if resp['errcode'] != 0:
                raise exceptions.ResponseError('get playlist songs: {}'.format(resp.get('error', resp['errcode'])))
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('get playlist songs: {}'.format(e))

        return resp

    async def request(self, method: str, url: str, **kwargs) -> aiohttp.ClientResponse:
        headers = {
            'Origin': 'https://www.kugou.com',
            'Referer': 'https://www.kugou.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/74.0.3729.169 Safari/537.36',
        }
        kwargs.update({
            'headers': headers,
        })
        return await self._session.request(method, url, **kwargs)


async def search_songs(keyword: str) -> api.SearchSongsResult:
    async with KuGou() as client:
        return await client.search_songs(keyword)


async def get_song(file_hash: str) -> api.Song:
    async with KuGou() as client:
        return await client.get_song(file_hash)


async def get_artist(singer_id: typing.Union[int, str]) -> api.Artist:
    async with KuGou() as client:
        return await client.get_artist(singer_id)


async def get_album(album_id: typing.Union[int, str]) -> api.Album:
    async with KuGou() as client:
        return await client.get_album(album_id)


async def get_playlist(special_id: typing.Union[int, str]) -> api.Playlist:
    async with KuGou() as client:
        return await client.get_playlist(special_id)


async def get_song_url(file_hash: str) -> typing.Optional[str]:
    async with KuGou() as client:
        return await client.get_song_url(file_hash)


async def get_song_lyric(file_hash: str) -> typing.Optional[str]:
    async with KuGou() as client:
        return await client.get_song_lyric(file_hash)
