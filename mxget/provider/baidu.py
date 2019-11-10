import asyncio
import base64
import hashlib
import json
import time
import typing
import urllib.parse

import aiohttp

from mxget import (
    api,
    crypto,
    exceptions,
)

__all__ = [
    'search_songs',
    'get_song',
    'get_artist',
    'get_album',
    'get_playlist',
]

_API_SEARCH = "http://musicapi.qianqian.com/v1/restserver/ting?method=baidu.ting.search.merge" \
              "&from=android&version=8.1.4.0&format=json&type=-1&isNew=1"
_API_GET_SONG = "http://musicapi.qianqian.com/v1/restserver/ting?method=baidu.ting.song.getInfos" \
                "&format=json&from=android&version=8.1.4.0"
_API_GET_SONGS = "http://music.taihe.com/data/music/fmlink"
_API_GET_SONG_LYRIC = "http://musicapi.qianqian.com/v1/restserver/ting?method=baidu.ting.song.lry&format=json" \
                      "&from=android&version=8.1.4.0"
_API_GET_ARTIST = "http://musicapi.qianqian.com/v1/restserver/ting?method=baidu.ting.artist.getSongList" \
                  "&from=android&version=8.1.4.0&format=json&order=2"
_API_GET_ALBUM = "http://musicapi.qianqian.com/v1/restserver/ting?method=baidu.ting.album.getAlbumInfo&from=android" \
                 "&version=8.1.4.0&format=json"
_API_GET_PLAYLIST = "http://musicapi.qianqian.com/v1/restserver/ting?method=baidu.ting.ugcdiy.getBaseInfo" \
                    "&from=android&version=8.1.4.0"

_INPUT = '2012171402992850'
_IV = '2012061402992850'
_HASH = hashlib.md5(_INPUT.encode('utf-8')).hexdigest().upper()
_KEY = _HASH[len(_HASH) // 2:]


def _aes_cbc_encrypt(song_id: typing.Union[int, str]) -> dict:
    params = {
        'songid': song_id,
        'ts': int(time.time() * 1000),
    }

    q = urllib.parse.urlencode(params)
    sec = crypto.aes_cbc_encrypt(q.encode('utf-8'), _KEY.encode('utf-8'), _IV.encode('utf-8'))
    e = base64.b64encode(sec).decode('utf-8')

    params['e'] = e
    return params


def _sign_payload(params: dict) -> dict:
    ts = int(time.time())
    r = 'baidu_taihe_music_secret_key{}'.format(ts)
    key = hashlib.md5(r.encode('utf-8')).hexdigest()[8:24]

    q = urllib.parse.urlencode(params)
    sec = crypto.aes_cbc_encrypt(q.encode('utf-8'), key.encode('utf-8'), key.encode('utf-8'))
    param = base64.b64encode(sec).decode('utf-8')
    sign = hashlib.md5('baidu_taihe_music{}{}'.format(param, ts).encode('utf-8')).hexdigest()

    return {
        'timestamp': ts,
        'param': param,
        'sign': sign,
    }


def _song_url(urls: typing.List[dict]) -> typing.Optional[str]:
    for u in urls:
        if u.get('file_format') == 'mp3':
            return u.get('show_link')

    return None


def _resolve(*songs: dict) -> typing.List[api.Song]:
    return [
        api.Song(
            name=song['title'].strip(),
            artist=song['author'].replace(',', '/').strip(),
            album=song.get('album_title', '').strip(),
            pic_url=song.get('pic_big', '').split('@')[0],
            lyric=song.get('lyric'),
            url=song.get('url'),
        ) for song in songs
    ]


class BaiDu(api.API):
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
        return api.Platform.BaiDu

    async def search_songs(self, keyword: str) -> api.SearchSongsResult:
        resp = await self.search_songs_raw(keyword)
        try:
            _songs = resp['result']['song_info']['song_list']
        except KeyError:
            raise exceptions.DataError('search songs: no data')

        if not _songs:
            raise exceptions.DataError('search songs: no data')

        songs = [
            api.SearchSongsData(
                song_id=_song['song_id'],
                name=_song['title'].strip(),
                artist=_song['author'].replace(',', '/').strip(),
                album=_song['album_title'].strip(),
            ) for _song in _songs
        ]
        return api.SearchSongsResult(keyword=keyword, count=len(songs), songs=songs)

    async def search_songs_raw(self, keyword: str, page: int = 1, page_size: int = 50) -> dict:
        params = {
            'query': keyword,
            'page_no': page,
            'page_size': page_size,
        }

        try:
            _resp = await self.request('GET', _API_SEARCH, params=params)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('search songs: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            if resp['error_code'] != 22000:
                raise exceptions.ResponseError('search songs: {}'.format(resp.get('error_message', resp['error_code'])))
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('search songs: {}'.format(e))

        return resp

    async def get_song(self, song_id: typing.Union[int, str]) -> api.Song:
        resp = await self.get_song_raw(song_id)
        try:
            _song = resp['songinfo']
        except KeyError:
            raise exceptions.DataError('get song: no data')

        _song['url'] = _song_url(resp['songurl']['url'])
        await self._patch_song_lyric(_song)
        songs = _resolve(_song)
        return songs[0]

    async def get_song_raw(self, song_id: typing.Union[int, str]) -> dict:
        try:
            _resp = await self.request('GET', _API_GET_SONG, params=_aes_cbc_encrypt(song_id))
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('get song: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            if resp['error_code'] != 22000:
                raise exceptions.ResponseError('get song: {}'.format(resp.get('error_message', resp['error_code'])))
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('get song: {}'.format(e))

        return resp

    async def _patch_song_url(self, *songs: dict) -> None:
        sem = asyncio.Semaphore(32)

        async def worker(song: dict):
            async with sem:
                try:
                    resp = await self.get_song_raw(song['song_id'])
                except exceptions.ClientError:
                    return

                try:
                    urls = resp['songurl']['url']
                except KeyError:
                    pass
                else:
                    song['url'] = _song_url(urls)

                try:
                    lrc_link = resp['songinfo']['lrclink']
                except KeyError:
                    return

                if not song.get('lrclink', ''):
                    song['lrclink'] = lrc_link

        tasks = [asyncio.ensure_future(worker(song)) for song in songs]
        await asyncio.gather(*tasks)

    async def _patch_song_lyric(self, *songs: dict) -> None:
        sem = asyncio.Semaphore(32)

        async def worker(song: dict):
            async with sem:
                lrc_link = song.get('lrclink', '')
                if not lrc_link:
                    return
                try:
                    resp = await self.request('GET', lrc_link)
                    song['lyric'] = await resp.text()
                except (aiohttp.ClientError, asyncio.TimeoutError):
                    pass

        tasks = [asyncio.ensure_future(worker(song)) for song in songs]
        await asyncio.gather(*tasks)

    async def get_artist(self, ting_uid: typing.Union[int, str]) -> api.Artist:
        resp = await self.get_artist_raw(ting_uid)

        try:
            artist = resp['artistinfo']
            _songs = resp['songlist']
        except KeyError:
            raise exceptions.DataError('get artist: no data')

        if not _songs:
            raise exceptions.DataError('get artist: no data')

        await self._patch_song_url(*_songs)
        await self._patch_song_lyric(*_songs)
        songs = _resolve(*_songs)
        return api.Artist(
            name=artist['name'].strip(),
            pic_url=artist.get('avatar_big', '').split('@')[0],
            count=len(songs),
            songs=songs
        )

    async def get_artist_raw(self, ting_uid: typing.Union[int, str],
                             offset: int = 0, limits: int = 50) -> dict:
        params = {
            'tinguid': ting_uid,
            'offset': offset,
            'limits': limits,
        }

        try:
            _resp = await self.request('GET', _API_GET_ARTIST, params=params)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('get artist: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            if resp['error_code'] != 22000:
                raise exceptions.ResponseError('get artist: {}'.format(resp.get('error_message', resp['error_code'])))
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('get artist: {}'.format(e))

        return resp

    async def get_album(self, album_id: typing.Union[int, str]) -> api.Album:
        resp = await self.get_album_raw(album_id)

        try:
            album = resp['albumInfo']
            _songs = resp['songlist']
        except KeyError:
            raise exceptions.DataError('get album: no data')

        if not _songs:
            raise exceptions.DataError('get album: no data')

        await self._patch_song_url(*_songs)
        await self._patch_song_lyric(*_songs)
        songs = _resolve(*_songs)
        return api.Album(
            name=album['title'].strip(),
            pic_url=album.get('pic_big', '').split('@')[0],
            count=len(songs),
            songs=songs
        )

    async def get_album_raw(self, album_id: typing.Union[int, str]) -> dict:
        params = {
            'album_id': album_id,
        }

        try:
            _resp = await self.request('GET', _API_GET_ALBUM, params=params)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('get album: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            if resp.get('error_code') is not None and resp['error_code'] != 22000:
                raise exceptions.ResponseError('get album: {}'.format(resp.get('error_message', resp['error_code'])))
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('get album: {}'.format(e))

        return resp

    async def get_playlist(self, playlist_id: typing.Union[int, str]) -> api.Playlist:
        resp = await self.get_playlist_raw(playlist_id)

        try:
            playlist = resp['result']['info']
            _songs = resp['result']['songlist']
        except KeyError:
            raise exceptions.DataError('get playlist: no data')

        if not _songs:
            raise exceptions.DataError('get playlist: no data')

        await self._patch_song_url(*_songs)
        await self._patch_song_lyric(*_songs)
        songs = _resolve(*_songs)
        return api.Playlist(
            name=playlist['list_title'].strip(),
            pic_url=playlist.get('list_pic', ''),
            count=len(songs),
            songs=songs
        )

    async def get_playlist_raw(self, playlist_id: typing.Union[int, str]) -> dict:
        params = {
            'list_id': playlist_id,
            'withcount': 1,
            'withsong': 1,
        }

        try:
            _resp = await self.request('GET', _API_GET_PLAYLIST, params=_sign_payload(params))
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('get playlist: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            if resp['error_code'] != 22000:
                raise exceptions.ResponseError('get playlist: {}'.format(resp.get('error_message', resp['error_code'])))
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('get playlist: {}'.format(e))

        return resp

    async def request(self, method: str, url: str, **kwargs) -> aiohttp.ClientResponse:
        headers = {
            'Origin': 'http://music.taihe.com',
            'Referer': 'http://music.taihe.com',
            'User-Agent': api.USER_AGENT,
        }
        kwargs.update({
            'headers': headers,
        })

        return await self._session.request(method, url, **kwargs)


async def search_songs(keyword: str) -> api.SearchSongsResult:
    async with BaiDu() as client:
        return await client.search_songs(keyword)


async def get_song(song_id: typing.Union[int, str]) -> api.Song:
    async with BaiDu() as client:
        return await client.get_song(song_id)


async def get_artist(artist_id: typing.Union[int, str]) -> api.Artist:
    async with BaiDu() as client:
        return await client.get_artist(artist_id)


async def get_album(album_id: typing.Union[int, str]) -> api.Album:
    async with BaiDu() as client:
        return await client.get_album(album_id)


async def get_playlist(playlist_id: typing.Union[int, str]) -> api.Playlist:
    async with BaiDu() as client:
        return await client.get_playlist(playlist_id)
