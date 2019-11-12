import asyncio
import hashlib
import json
import time
import typing

import aiohttp
import yarl

from mxget import (
    api,
    exceptions,
)

_API_SEARCH = "https://acs.m.xiami.com/h5/mtop.alimusic.search.searchservice.searchsongs" \
              "/1.0/?appKey=23649156"
_API_GET_SONG_DETAIL = "https://acs.m.xiami.com/h5/mtop.alimusic.music.songservice.getsongdetail" \
                       "/1.0/?appKey=23649156"
_API_GET_SONG_LYRIC = "https://acs.m.xiami.com/h5/mtop.alimusic.music.lyricservice.getsonglyrics" \
                      "/1.0/?appKey=23649156"
_API_GET_SONGS = "https://acs.m.xiami.com/h5/mtop.alimusic.music.songservice.getsongs" \
                 "/1.0/?appKey=23649156"
_API_GET_ARTIST_INFO = "https://acs.m.xiami.com/h5/mtop.alimusic.music.artistservice.getartistdetail" \
                       "/1.0/?appKey=23649156"
_API_GET_ARTIST_SONGS = "https://acs.m.xiami.com/h5/mtop.alimusic.music.songservice.getartistsongs" \
                        "/1.0/?appKey=23649156"
_API_GET_ALBUM = "https://acs.m.xiami.com/h5/mtop.alimusic.music.albumservice.getalbumdetail" \
                 "/1.0/?appKey=23649156"
_API_GET_PLAYLIST_DETAIL = "https://h5api.m.xiami.com/h5/mtop.alimusic.music.list.collectservice.getcollectdetail" \
                           "/1.0/?appKey=23649156"
_API_GET_PLAYLIST_SONGS = "https://h5api.m.xiami.com/h5/mtop.alimusic.music.list.collectservice.getcollectsongs" \
                          "/1.0/?appKey=23649156"

_REQ_HEADER = {
    'appId': 200,
    'platformId': 'h5',
}
_APP_KEY = '23649156'

_SONG_REQUEST_LIMIT = 200


def _sign_payload(token: str, model: typing.Any) -> dict:
    payload = {
        'header': _REQ_HEADER,
        'model': model,
    }
    data = {
        'requestStr': json.dumps(payload),
    }
    data_str = json.dumps(data)
    t = int(time.time() * 1000)
    sign_str = '{}&{}&{}&{}'.format(token, t, _APP_KEY, data_str)
    sign = hashlib.md5(sign_str.encode('utf-8')).hexdigest()
    return {
        't': t,
        'sign': sign,
        'data': data_str,
    }


def _check(ret: typing.List[str], msg: str):
    for s in ret:
        if s.startswith('FAIL'):
            raise exceptions.ResponseError('{}: {}'.format(msg, s))


def _song_url(listen_files: typing.List[dict]) -> typing.Optional[str]:
    for i in listen_files:
        if i.get('quality') == 'l':
            return i.get('url', '') + i.get('listenFile', '')

    return None


def _resolve(*songs: dict) -> typing.List[api.Song]:
    return [
        api.Song(
            song_id=song['songId'],
            name=song['songName'].strip(),
            artist=song['singers'].replace(' / ', '/').strip(),
            album=song.get('albumName', '').strip(),
            pic_url=song.get('albumLogo'),
            lyric=song.get('lyric'),
            url=_song_url(song['listenFiles']),
        ) for song in songs
    ]


class XiaMi(api.API):
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

    def platform_id(self) -> api.PlatformId:
        return api.PlatformId.XiaMi

    async def _get_token(self, url: str) -> str:
        xm_tk = self._session.cookie_jar.filter_cookies(yarl.URL(url)).get('_m_h5_tk')
        if xm_tk is None:
            resp = await self.request('GET', url)
            xm_tk = resp.cookies.get('_m_h5_tk')
        return xm_tk.value.split('_')[0] if xm_tk is not None else None

    async def search_songs(self, keyword: str) -> api.SearchSongsResult:
        resp = await self.search_songs_raw(keyword)
        try:
            _songs = resp['data']['data']['songs']
        except KeyError:
            raise exceptions.DataError('search songs: no data')

        if not _songs:
            raise exceptions.DataError('search songs: no data')

        songs = [
            api.SearchSongsData(
                song_id=_song['songId'],
                name=_song['songName'].strip(),
                artist=_song['singers'].replace(' / ', '/').strip(),
                album=_song['albumName'].strip(),
            ) for _song in _songs
        ]
        return api.SearchSongsResult(keyword=keyword, count=len(songs), songs=songs)

    async def search_songs_raw(self, keyword: str, page: int = 1, page_size: int = 50) -> dict:
        token = await self._get_token(_API_SEARCH)
        if token is None:
            raise exceptions.ClientError("search songs: can't get token")

        model = {
            'key': keyword,
            'pagingVO': {
                'page': page,
                'pageSize': page_size,
            },
        }

        try:
            _resp = await self.request('GET', _API_SEARCH, params=_sign_payload(token, model))
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('search songs: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            _check(resp['ret'], 'search songs')
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('search songs: {}'.format(e))

        return resp

    async def get_song(self, song_id: typing.Union[int, str]) -> api.Song:
        resp = await self.get_song_detail_raw(song_id)
        try:
            _song = resp['data']['data']['songDetail']
        except KeyError:
            raise exceptions.DataError('get song: no data')

        await self._patch_song_lyric(_song)
        songs = _resolve(_song)
        return songs[0]

    async def get_song_detail_raw(self, song_id: typing.Union[int, str]) -> dict:
        token = await self._get_token(_API_GET_SONG_DETAIL)
        if token is None:
            raise exceptions.ClientError("get song detail: can't get token")

        model = {}
        if song_id.isdigit():
            model['songId'] = song_id
        else:
            model['songStringId'] = song_id

        try:
            _resp = await self.request('GET', _API_GET_SONG_DETAIL, params=_sign_payload(token, model))
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('get song detail: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            _check(resp['ret'], 'get song detail')
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('get song detail: {}'.format(e))

        return resp

    async def get_songs_raw(self, *song_ids: typing.Union[int, str]) -> dict:
        token = await self._get_token(_API_GET_SONGS)
        if token is None:
            raise exceptions.ClientError("get songs: can't get token")

        if len(song_ids) > _SONG_REQUEST_LIMIT:
            song_ids = song_ids[:_SONG_REQUEST_LIMIT]

        model = {
            'songIds': song_ids,
        }

        try:
            _resp = await self.request('GET', _API_GET_SONGS, params=_sign_payload(token, model))
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('get songs: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            _check(resp['ret'], 'get songs')
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('get songs: {}'.format(e))

        return resp

    async def get_song_lyric(self, mid: typing.Union[int, str]) -> typing.Optional[str]:
        resp = await self.get_song_lyric_raw(mid)
        try:
            lyrics = resp['data']['data']['lyrics']
        except KeyError:
            return None

        if not lyrics:
            return None

        for i in lyrics:
            if i.get('flagOfficial') == '1' and i.get('type') == '2':
                return i.get('content')

        return None

    async def get_song_lyric_raw(self, song_id: typing.Union[int, str]) -> dict:
        token = await self._get_token(_API_GET_SONG_LYRIC)
        if token is None:
            raise exceptions.ClientError("get song lyric: can't get token")

        model = {}
        if song_id.isdigit():
            model['songId'] = song_id
        else:
            model['songStringId'] = song_id

        try:
            _resp = await self.request('GET', _API_GET_SONG_LYRIC, params=_sign_payload(token, model))
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('get song lyric: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            _check(resp['ret'], 'get song lyric')
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('get song lyric: {}'.format(e))

        return resp

    async def _patch_song_lyric(self, *songs: dict) -> None:
        sem = asyncio.Semaphore(32)

        async def worker(song: dict):
            async with sem:
                song['lyric'] = await self.get_song_lyric(song['songId'])

        tasks = [asyncio.ensure_future(worker(song)) for song in songs]
        await asyncio.gather(*tasks)

    async def get_artist(self, artist_id: typing.Union[int, str]) -> api.Artist:
        artist_info = await self.get_artist_info_raw(artist_id)
        artist_song = await self.get_artist_songs_raw(artist_id)

        try:
            artist = artist_info['data']['data']['artistDetailVO']
            _songs = artist_song['data']['data']['songs']
        except KeyError:
            raise exceptions.DataError('get artist: no data')

        if not _songs:
            raise exceptions.DataError('get artist: no data')

        await self._patch_song_lyric(*_songs)
        songs = _resolve(*_songs)
        return api.Artist(
            artist_id=artist['artistId'],
            name=artist['artistName'].strip(),
            pic_url=artist.get('artistLogo', ''),
            count=len(songs),
            songs=songs,
        )

    async def get_artist_info_raw(self, artist_id: typing.Union[int, str]) -> dict:
        token = await self._get_token(_API_SEARCH)
        if token is None:
            raise exceptions.ClientError("get artist info: can't get token")

        model = {}
        if artist_id.isdigit():
            model['artistId'] = artist_id
        else:
            model['artistStringId'] = artist_id

        try:
            _resp = await self.request('GET', _API_GET_ARTIST_INFO, params=_sign_payload(token, model))
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('get artist info: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            _check(resp['ret'], 'get artist info')
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('get artist info: {}'.format(e))

        return resp

    async def get_artist_songs_raw(self, artist_id: typing.Union[int, str],
                                   page: int = 1, page_size: int = 50) -> dict:
        token = await self._get_token(_API_SEARCH)
        if token is None:
            raise exceptions.ClientError("get artist songs: can't get token")

        model = {
            'pagingVO': {
                'page': page,
                'pageSize': page_size,
            },
        }
        if artist_id.isdigit():
            model['artistId'] = artist_id
        else:
            model['artistStringId'] = artist_id

        try:
            _resp = await self.request('GET', _API_GET_ARTIST_SONGS, params=_sign_payload(token, model))
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('get artist songs: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            _check(resp['ret'], 'get artist songs')
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('get artist songs: {}'.format(e))

        return resp

    async def get_album(self, album_id: typing.Union[int, str]) -> api.Album:
        resp = await self.get_album_raw(album_id)

        try:
            album = resp['data']['data']['albumDetail']
            _songs = album['songs']
        except KeyError:
            raise exceptions.DataError('get album: no data')

        if not _songs:
            raise exceptions.DataError('get album: no data')

        await self._patch_song_lyric(*_songs)
        songs = _resolve(*_songs)
        return api.Album(
            album_id=album['albumId'],
            name=album['albumName'].strip(),
            pic_url=album.get('albumLogo', ''),
            count=len(songs),
            songs=songs,
        )

    async def get_album_raw(self, album_id: typing.Union[int, str]) -> dict:
        token = await self._get_token(_API_SEARCH)
        if token is None:
            raise exceptions.ClientError("get album: can't get token")

        model = {}
        if album_id.isdigit():
            model['albumId'] = album_id
        else:
            model['albumStringId'] = album_id

        try:
            _resp = await self.request('GET', _API_GET_ALBUM, params=_sign_payload(token, model))
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('get album: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            _check(resp['ret'], 'get album')
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('get album: {}'.format(e))

        return resp

    async def get_playlist(self, playlist_id: typing.Union[int, str]) -> api.Playlist:
        resp = await self.get_playlist_detail_raw(playlist_id)

        try:
            playlist = resp['data']['data']['collectDetail']
            total = int(playlist['songCount'])
            tracks = playlist['songs']
            track_ids = playlist['allSongs']
        except (KeyError, ValueError):
            raise exceptions.DataError('get playlist: no data')

        if total == 0:
            raise exceptions.DataError('get playlist: no data')

        if total > _SONG_REQUEST_LIMIT:
            async def patch_tracks(*ids: typing.Union[int, str]):
                return await self.get_songs_raw(*ids)

            tasks = []
            for i in range(_SONG_REQUEST_LIMIT, total, _SONG_REQUEST_LIMIT):
                song_ids = track_ids[i:min(i + _SONG_REQUEST_LIMIT, total)]
                tasks.append(asyncio.ensure_future(patch_tracks(*song_ids)))

            await asyncio.gather(*tasks)
            for task in tasks:
                if not task.exception():
                    try:
                        data = task.result()['data']['data']
                        _songs = data.get('songs', [])
                        tracks.extend(_songs)
                    except KeyError:
                        continue

        await self._patch_song_lyric(*tracks)
        songs = _resolve(*tracks)
        return api.Playlist(
            playlist_id=playlist['listId'],
            name=playlist['collectName'].strip(),
            pic_url=playlist.get('collectLogo', ''),
            count=len(songs),
            songs=songs,
        )

    async def get_playlist_detail_raw(self, playlist_id: typing.Union[int, str],
                                      page: int = 1, page_size: int = _SONG_REQUEST_LIMIT) -> dict:
        token = await self._get_token(_API_GET_PLAYLIST_DETAIL)
        if token is None:
            raise exceptions.ClientError("get playlist detail: can't get token")

        model = {
            'listid': playlist_id,
            'pagingVO': {
                'page': page,
                'pageSize': page_size,
            },
        }

        try:
            _resp = await self.request('GET', _API_GET_PLAYLIST_DETAIL, params=_sign_payload(token, model))
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('get playlist detail: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            _check(resp['ret'], 'get playlist detail')
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('get playlist detail: {}'.format(e))

        return resp

    async def get_playlist_songs_raw(self, playlist_id: typing.Union[int, str],
                                     page: int = 1, page_size: int = 200) -> dict:
        token = await self._get_token(_API_GET_PLAYLIST_SONGS)
        if token is None:
            raise exceptions.ClientError("get playlist songs: can't get token")

        model = {
            'listid': playlist_id,
            'pagingVO': {
                'page': page,
                'pageSize': page_size,
            },
        }

        try:
            _resp = await self.request('GET', _API_GET_PLAYLIST_DETAIL, params=_sign_payload(token, model))
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('get playlist songs: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            _check(resp['ret'], 'get playlist songs')
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('get playlist songs: {}'.format(e))

        return resp

    async def request(self, method: str, url: str, **kwargs) -> aiohttp.ClientResponse:
        headers = {
            'Origin': 'https://h.xiami.com',
            'Referer': 'https://h.xiami.com',
            'User-Agent': api.USER_AGENT,
        }
        kwargs.update({
            'headers': headers,
        })

        return await self._session.request(method, url, **kwargs)
