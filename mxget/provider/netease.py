import asyncio
import base64
import binascii
import hashlib
import json
import os
import typing

import aiohttp
import yarl

from mxget import (
    crypto,
    api,
    exceptions,
)

_PRESET_KEY = b'0CoJUm6Qyw8W8jud'
_IV = b'0102030405060708'
_API_LINUX_KEY = b'rFgB&h#%2?^eDg:Q'
_EAPI_KEY = b'e82ckenh8dichen8'
_DEFAULT_RSA_PUBLIC_KEY_MODULES = 'e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b72515' \
                                  '2b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ec' \
                                  'bda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d8' \
                                  '13cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7 '
_DEFAULT_RSA_PUBLIC_KEY_EXPONENT = 0x10001

_API_LINUX = 'https://music.163.com/api/linux/forward'
_API_SEARCH = 'https://music.163.com/weapi/search/get'
_API_GET_SONGS = 'https://music.163.com/weapi/v3/song/detail'
_API_GET_SONGS_URL = 'https://music.163.com/weapi/song/enhance/player/url'
_API_GET_ARTIST = 'https://music.163.com/weapi/v1/artist/{artist_id}'
_API_GET_ALBUM = 'https://music.163.com/weapi/v1/album/{album_id}'
_API_GET_PLAYLIST = 'https://music.163.com/weapi/v3/playlist/detail'

_SONG_REQUEST_LIMIT = 1000


def _create_secret_key(size: int) -> bytes:
    return binascii.hexlify(os.urandom(size))[:16]


def _create_cookies() -> dict:
    return {
        '_ntes_nuid': _create_secret_key(16).decode('utf-8')
    }


def _weapi(orig_data: dict = None) -> dict:
    if orig_data is None:
        orig_data = {}
    plain_text = json.dumps(orig_data)
    params = base64.b64encode(crypto.aes_cbc_encrypt(plain_text.encode('utf-8'), _PRESET_KEY, _IV))
    sec_key = _create_secret_key(16)
    params = base64.b64encode(crypto.aes_cbc_encrypt(params, sec_key, _IV))
    return {
        'params': params.decode('utf-8'),
        'encSecKey': crypto.rsa_encrypt(sec_key[::-1], _DEFAULT_RSA_PUBLIC_KEY_MODULES,
                                        _DEFAULT_RSA_PUBLIC_KEY_EXPONENT),
    }


def _linuxapi(orig_data: dict = None) -> dict:
    if orig_data is None:
        orig_data = {}
    plain_text = json.dumps(orig_data)
    return {
        'eparams': crypto.aes_ecb_encrypt(plain_text.encode('utf-8'), _API_LINUX_KEY).hex().upper()
    }


def _eapi(url: str, orig_data: dict = None) -> dict:
    if orig_data is None:
        orig_data = {}
    plain_text = json.dumps(orig_data)
    message = 'nobody{}use{}md5forencrypt'.format(url, plain_text)
    digest = hashlib.md5(message.encode('utf-8')).hexdigest()
    data = '{}-36cd479b6b5-{}-36cd479b6b5-{}'.format(url, plain_text, digest)
    return {
        'params': crypto.aes_ecb_encrypt(data.encode('utf-8'), _EAPI_KEY).hex().upper()
    }


def _bit_rate(br: int) -> int:
    br = {
        128: 128,
        192: 192,
        320: 320,
        999: 999,
    }.get(br, 999)

    return br * 1000


def _resolve(*songs: dict) -> typing.List[api.Song]:
    return [
        api.Song(
            song_id=song['id'],
            name=song['name'].strip(),
            artist='/'.join([a['name'].strip() for a in song['ar']]),
            album=song['al']['name'].strip(),
            pic_url=song['al']['picUrl'],
            lyric=song.get('lyric'),
            url=song.get('url'),
        ) for song in songs
    ]


class NetEase(api.API):
    def __init__(self, session: aiohttp.ClientSession = None):
        if session is None:
            session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=120),
            )
        self._session = session
        self._cookies = _create_cookies()

    async def close(self):
        await self._session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def platform_id(self) -> api.PlatformId:
        return api.PlatformId.NetEase

    async def search_songs(self, keyword: str) -> api.SearchSongsResult:
        resp = await self.search_songs_raw(keyword)
        try:
            songs = resp['result']['songs']
        except KeyError:
            raise exceptions.DataError('search songs: no data')

        if not songs:
            raise exceptions.DataError('search songs: no data')

        songs = [
            api.SearchSongsData(
                song_id=song['id'],
                name=song['name'].strip(),
                artist='/'.join([a['name'].strip() for a in song['artists']]),
                album=song['album']['name'].strip(),
            ) for song in songs
        ]
        return api.SearchSongsResult(keyword=keyword, count=len(songs), songs=songs)

    async def search_songs_raw(self, keyword: str, offset: int = 0, limit: int = 50) -> dict:
        data = {
            's': keyword,
            'type': 1,
            'offset': offset,
            'limit': limit,
        }

        try:
            _resp = await self.request('POST', _API_SEARCH, data=_weapi(data))
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('search songs: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            if resp['code'] != 200:
                raise exceptions.ResponseError('search songs: {}'.format(resp['msg']))
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('search songs: {}'.format(e))

        return resp

    async def get_song(self, song_id: typing.Union[int, str]) -> api.Song:
        resp = await self.get_songs_raw(song_id)
        try:
            _song = resp['songs'][0]
        except (KeyError, IndexError):
            raise exceptions.DataError('get song: no data')

        await self._patch_song_url(_song)
        await self._patch_song_lyric(_song)
        songs = _resolve(_song)
        return songs[0]

    async def get_songs_raw(self, *song_ids: typing.Union[int, str]) -> dict:
        if len(song_ids) > _SONG_REQUEST_LIMIT:
            song_ids = song_ids[:_SONG_REQUEST_LIMIT]

        c = [{'id': song_id} for song_id in song_ids]
        data = {
            'c': json.dumps(c),
        }

        try:
            _resp = await self.request('POST', _API_GET_SONGS, data=_weapi(data))
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('get songs: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            if resp['code'] != 200:
                raise exceptions.ResponseError('get songs: {}'.format(resp['msg']))
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('get songs: {}'.format(e))

        return resp

    async def get_song_url(self, song_id: typing.Union[int, str], br: int = 128) -> typing.Optional[str]:
        resp = await self.get_songs_url_raw(song_id, br=br)
        try:
            url = resp['data'][0]['url']
        except (KeyError, IndexError):
            return None

        return url if url else None

    async def get_songs_url_raw(self, *song_ids: typing.Union[int, str], br: int = 128) -> dict:
        data = {
            'br': _bit_rate(br),
            'ids': json.dumps(song_ids),
        }

        try:
            _resp = await self.request('POST', _API_GET_SONGS_URL, data=_weapi(data))
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('get songs url: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            if resp['code'] != 200:
                raise exceptions.ResponseError('get songs url: {}'.format(resp['msg']))
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('get songs url: {}'.format(e))

        return resp

    async def get_song_lyric(self, song_id: typing.Union[int, str]) -> typing.Optional[str]:
        resp = await self.get_song_lyric_raw(song_id)
        try:
            lyric = resp['lrc']['lyric']
        except KeyError:
            return None
        return lyric if lyric else None

    async def get_song_lyric_raw(self, song_id: typing.Union[int, str]) -> dict:
        data = {
            'method': 'POST',
            'url': 'https://music.163.com/api/song/lyric?lv=-1&kv=-1&tv=-1',
            'params': {
                'id': song_id,
            }
        }

        try:
            _resp = await self.request('POST', _API_LINUX, data=_linuxapi(data))
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('get song lyric: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            if resp['code'] != 200:
                raise exceptions.ResponseError('get song lyric: {}'.format(resp['msg']))
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('get song lyric: {}'.format(e))

        return resp

    async def _patch_song_url(self, *songs: dict) -> None:
        song_ids = [s['id'] for s in songs]
        resp = await self.get_songs_url_raw(*song_ids)
        if resp.get('data') is None:
            return

        url_map = dict()
        for i in resp['data']:
            if i.get('code') == 200:
                url_map[i['id']] = i['url']

        for s in songs:
            s['url'] = url_map.get(s['id'])

    async def _patch_song_lyric(self, *songs: dict) -> None:
        sem = asyncio.Semaphore(32)

        async def worker(song: dict):
            async with sem:
                song['lyric'] = await self.get_song_lyric(song['id'])

        tasks = [asyncio.ensure_future(worker(song)) for song in songs]
        await asyncio.gather(*tasks)

    async def get_artist(self, artist_id: typing.Union[int, str]) -> api.Artist:
        resp = await self.get_artist_raw(artist_id)
        try:
            _songs = resp['hotSongs']
        except KeyError:
            raise exceptions.DataError('get artist: no data')

        if not _songs:
            raise exceptions.DataError('get artist: no data')

        await self._patch_song_url(*_songs)
        await self._patch_song_lyric(*_songs)
        songs = _resolve(*_songs)
        return api.Artist(
            artist_id=resp['artist']['id'],
            name=resp['artist']['name'].strip(),
            pic_url=resp['artist']['picUrl'],
            count=len(songs),
            songs=songs,
        )

    async def get_artist_raw(self, artist_id: typing.Union[int, str]) -> dict:
        try:
            _resp = await self.request('POST', _API_GET_ARTIST.format(artist_id=artist_id), data=_weapi())
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('get artist: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            if resp['code'] != 200:
                raise exceptions.ResponseError('get artist: {}'.format(resp.get('msg', resp['code'])))
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('get artist: {}'.format(e))

        return resp

    async def get_album(self, album_id: typing.Union[int, str]) -> api.Album:
        resp = await self.get_album_raw(album_id)
        try:
            _songs = resp['songs']
        except KeyError:
            raise exceptions.DataError('get album: no data')

        if not _songs:
            raise exceptions.DataError('get album: no data')

        await self._patch_song_url(*_songs)
        await self._patch_song_lyric(*_songs)
        songs = _resolve(*_songs)
        return api.Album(
            album_id=resp['album']['id'],
            name=resp['album']['name'].strip(),
            pic_url=resp['album']['picUrl'],
            count=len(songs),
            songs=songs,
        )

    async def get_album_raw(self, album_id: typing.Union[int, str]) -> dict:
        try:
            _resp = await self.request('POST', _API_GET_ALBUM.format(album_id=album_id), data=_weapi())
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('get album: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            if resp['code'] != 200:
                raise exceptions.ResponseError('get album: {}'.format(resp.get('msg', resp['code'])))
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('get album: {}'.format(e))

        return resp

    async def get_playlist(self, playlist_id: typing.Union[int, str]) -> api.Playlist:
        resp = await self.get_playlist_raw(playlist_id)
        try:
            total = resp['playlist']['trackCount']
            tracks = resp['playlist']['tracks']
            track_ids = resp['playlist']['trackIds']
        except KeyError:
            raise exceptions.DataError('get playlist: no data')

        if total == 0:
            raise exceptions.DataError('get playlist: no data')

        if total > _SONG_REQUEST_LIMIT:
            song_ids = [track_ids[i]['id'] for i in range(_SONG_REQUEST_LIMIT, total)]

            async def patch_tracks(*ids: typing.Union[int, str]):
                return await self.get_songs_raw(*ids)

            extra = total - _SONG_REQUEST_LIMIT
            tasks = []
            for i in range(0, extra, _SONG_REQUEST_LIMIT):
                _ids = song_ids[i:min(i + _SONG_REQUEST_LIMIT, extra)]
                tasks.append(asyncio.ensure_future(patch_tracks(*_ids)))

            await asyncio.gather(*tasks)
            for task in tasks:
                if not task.exception():
                    tracks.extend(task.result().get('songs', []))

        await self._patch_song_url(*tracks)
        await self._patch_song_lyric(*tracks)
        songs = _resolve(*tracks)
        return api.Playlist(
            playlist_id=resp['playlist']['id'],
            name=resp['playlist']['name'].strip(),
            pic_url=resp['playlist']['coverImgUrl'],
            count=len(songs),
            songs=songs,
        )

    async def get_playlist_raw(self, playlist_id: typing.Union[int, str]) -> dict:
        data = {
            'id': playlist_id,
            'n': 100000,
        }

        try:
            _resp = await self.request('POST', _API_GET_PLAYLIST, data=_weapi(data), ssl=False)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('get playlist: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            if resp['code'] != 200:
                raise exceptions.ResponseError('get playlist: {}'.format(resp['msg']))
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('get playlist: {}'.format(e))

        return resp

    async def request(self, method: str, url: str, **kwargs) -> aiohttp.ClientResponse:
        headers = {
            'Origin': 'https://music.163.com',
            'Referer': 'https://music.163.com',
            'User-Agent': api.USER_AGENT,
        }
        kwargs.update({
            "headers": headers,
        })

        cookie = self._session.cookie_jar.filter_cookies(yarl.URL(url)).get('MUSIC_U')
        if cookie is None:
            kwargs.update({
                'cookies': self._cookies
            })

        return await self._session.request(method, url, **kwargs)
