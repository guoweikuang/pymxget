import asyncio
import json
import typing

import aiohttp

from mxget import (
    api,
    exceptions,
)

_API_SEARCH = 'https://app.c.nf.migu.cn/MIGUM2.0/v1.0/content/search_all.do?isCopyright=1&isCorrect=1'
_API_GET_SONG_ID = 'http://music.migu.cn/v3/api/music/audioPlayer/songs?type=1'
_API_GET_SONG = 'https://app.c.nf.migu.cn/MIGUM2.0/v2.0/content/querySongBySongId.do?contentId=0'
_API_GET_SONG_URL = 'https://app.c.nf.migu.cn/MIGUM2.0/v2.0/content/listen-url?copyrightId=0&netType=01&toneFlag=HQ'
_API_GET_SONG_PIC = 'http://music.migu.cn/v3/api/music/audioPlayer/getSongPic'
_API_GET_SONG_LYRIC = 'http://music.migu.cn/v3/api/music/audioPlayer/getLyric'
_API_GET_ARTIST_INFO = 'https://app.c.nf.migu.cn/MIGUM2.0/v1.0/content/resourceinfo.do?' \
                       'needSimple=01&resourceType=2002'
_API_GET_ARTIST_SONGS = 'https://app.c.nf.migu.cn/MIGUM3.0/v1.0/template/singerSongs/release?templateVersion=2'
_API_GET_ALBUM = 'https://app.c.nf.migu.cn/MIGUM2.0/v1.0/content/resourceinfo.do?needSimple=01&resourceType=2003'
_API_GET_PLAYLIST = 'https://app.c.nf.migu.cn/MIGUM2.0/v1.0/content/resourceinfo.do?needSimple=01&resourceType=2021'

_SONG_URL = "https://app.pd.nf.migu.cn/MIGUM2.0/v1.0/content/sub/listenSong.do?contentId={content_id}" \
            "&copyrightId=0&netType=01&resourceType={resource_type}&toneFlag={tone_flag}&channel=0"


def _code_rate(br: int) -> str:
    return {
        64: 'LQ',
        128: 'PQ',
        320: 'HQ',
        999: 'SQ'
    }.get(br, 'HQ')


def _get_song_url(content_id: typing.Union[int, str], br: int = 128) -> typing.Optional[str]:
    return _SONG_URL.format(content_id=content_id, resource_type='E', tone_flag=_code_rate(br))


def _get_pic_url(imgs: typing.List[dict]) -> str:
    for i in imgs:
        if i['imgSizeType'] == '03':
            return i['img']
    return ''


def _patch_song_url(*songs: dict) -> None:
    for song in songs:
        song['url'] = _get_song_url(song['contentId'])


def _patch_song_info(*songs: dict) -> None:
    for song in songs:
        imgs = song.get('albumImgs')
        if imgs is None:
            continue
        song['pic_url'] = _get_pic_url(imgs)


def _resolve(*songs: dict) -> typing.List[api.Song]:
    return [
        api.Song(
            song_id=song['songId'],
            name=song['songName'].strip(),
            artist=song['singer'].replace('|', '/').strip(),
            album=song.get('album', '').strip(),
            pic_url=song.get('pic_url'),
            lyric=song.get('lyric'),
            url=song.get('url'),
        ) for song in songs
    ]


class MiGu(api.API):
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
        return api.PlatformId.MiGu

    async def search_songs(self, keyword: str) -> api.SearchSongsResult:
        resp = await self.search_songs_raw(keyword)
        try:
            _songs = resp['songResultData']['result']
        except KeyError:
            raise exceptions.DataError('search songs: no data')

        if not _songs:
            raise exceptions.DataError('search songs: no data')

        songs = [
            api.SearchSongsData(
                song_id=_song['id'],
                name=_song['name'].strip(),
                artist='/'.join([s['name'].strip() for s in _song['singers']]),
                album='/'.join([a['name'].strip() for a in _song['albums']]) if _song.get('album') is not None else '',
            ) for _song in _songs
        ]
        return api.SearchSongsResult(keyword=keyword, count=len(songs), songs=songs)

    async def search_songs_raw(self, keyword: str, page: int = 1, page_size: int = 50) -> dict:
        switch_option = {
            'song': 1,
            'album': 0,
            'singer': 0,
            'tagSong': 0,
            'mvSong': 0,
            'songlist': 0,
            'bestShow': 0,
        }
        params = {
            'searchSwitch': json.dumps(switch_option),
            'text': keyword,
            'pageNo': page,
            'pageSize': page_size,
        }

        try:
            _resp = await self.request('GET', _API_SEARCH, params=params)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('search songs: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            if resp['code'] != '000000':
                raise exceptions.ResponseError('search songs: {}'.format(resp['info']))
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('search songs: {}'.format(e))

        return resp

    async def get_song_id(self, copyright_id: typing.Union[int, str]) -> typing.Optional[str]:
        resp = await self.get_song_id_raw(copyright_id)
        try:
            song_id = resp['items'][0]['songId']
        except (KeyError, IndexError):
            return None
        return song_id

    async def get_song_id_raw(self, copyright_id: typing.Union[int, str]) -> dict:
        params = {
            'copyrightId': copyright_id,
        }

        try:
            _resp = await self.request('GET', _API_GET_SONG_ID, params=params)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('get song id: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            if resp['returnCode'] != '000000':
                raise exceptions.ResponseError('get song id: {}'.format(resp['msg']))
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('get song id: {}'.format(e))

        return resp

    async def get_song(self, mid: typing.Union[int, str]) -> api.Song:
        if mid.isdigit():
            mid = str(mid)
        if len(str(mid)) > 10 and mid.startswith('6'):
            song_id = await self.get_song_id(mid)
            if song_id is None:
                raise exceptions.DataError('get song: no data')
        else:
            song_id = mid

        resp = await self.get_song_raw(song_id)
        try:
            _song = resp['resource'][0]
        except (KeyError, IndexError):
            raise exceptions.DataError('get song: no data')

        await self._patch_song_lyric(_song)
        _patch_song_url(_song)
        _patch_song_info(_song)
        songs = _resolve(_song)
        return songs[0]

    async def get_song_raw(self, song_id: typing.Union[int, str]) -> dict:
        params = {
            'songId': song_id,
        }

        try:
            _resp = await self.request('GET', _API_GET_SONG, params=params)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('get song: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            if resp['code'] != '000000':
                raise exceptions.ResponseError('get song: {}'.format(resp.get('error', resp['info'])))
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.ResponseError('get song: {}'.format(e))

        return resp

    async def get_song_url_raw(self, content_id: str, resource_type: str) -> dict:
        params = {
            'contentId': content_id,
            'lowerQualityContentId': content_id,
            'resourceType': resource_type,
        }

        try:
            _resp = await self.request('GET', _API_GET_SONG_URL, params=params)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('get song url: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            if resp['code'] != '000000':
                raise exceptions.ResponseError('get song url: {}'.format(resp['info']))
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('get song url: {}'.format(e))

        return resp

    async def get_song_pic(self, song_id: typing.Union[int, str]) -> typing.Optional[str]:
        try:
            resp = await self.get_song_pic_raw(song_id)
            pic_url = resp['largePic']
        except (exceptions.RequestError, exceptions.ResponseError, KeyError):
            return None

        if not pic_url.startswith('http:'):
            pic_url = 'http:' + pic_url
        return pic_url

    async def get_song_pic_raw(self, song_id: typing.Union[int, str]) -> dict:
        params = {
            'songId': song_id,
        }

        try:
            _resp = await self.request('GET', _API_GET_SONG_PIC, params=params)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('get song pic: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            if resp['returnCode'] != '000000':
                raise exceptions.ResponseError('get song pic: {}'.format(resp['msg']))
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('get song pic: {}'.format(e))

        return resp

    async def get_song_lyric(self, copyright_id: typing.Union[int, str]) -> typing.Optional[str]:
        try:
            resp = await self.get_song_lyric_raw(copyright_id)
            lyric = resp['lyric']
        except (exceptions.RequestError, exceptions.ResponseError, KeyError):
            return None
        return lyric if lyric else None

    async def get_song_lyric_raw(self, copyright_id: typing.Union[int, str]) -> dict:
        params = {
            'copyrightId': copyright_id,
        }

        try:
            _resp = await self.request('GET', _API_GET_SONG_LYRIC, params=params)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('get song lyric: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            if resp['returnCode'] != '000000':
                raise exceptions.ResponseError('get song lyric: {}'.format(resp['msg']))
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('get song lyric: {}'.format(e))

        return resp

    async def _patch_song_lyric(self, *songs: dict) -> None:
        sem = asyncio.Semaphore(32)

        async def worker(song: dict):
            async with sem:
                lrc_url = song.get('lrcUrl', '')
                if not lrc_url:
                    return
                try:
                    resp = await self.request('GET', lrc_url)
                    song['lyric'] = await resp.text()
                except (aiohttp.ClientError, asyncio.TimeoutError):
                    pass

        tasks = [asyncio.ensure_future(worker(song)) for song in songs]
        await asyncio.gather(*tasks)

    async def get_artist(self, singer_id: typing.Union[int, str]) -> api.Artist:
        artist_info = await self.get_artist_info_raw(singer_id)
        artist_song = await self.get_artist_songs_raw(singer_id)

        try:
            artist = artist_info['resource'][0]
            item_list = artist_song['data']['contentItemList'][0]['itemList']
        except (KeyError, IndexError):
            raise exceptions.DataError('get artist: no data')

        if not item_list:
            raise exceptions.DataError('get artist: no data')

        _songs = [v['song'] for i, v in enumerate(item_list) if i % 2 == 0]
        await self._patch_song_lyric(*_songs)
        _patch_song_url(*_songs)
        _patch_song_info(*_songs)
        songs = _resolve(*_songs)
        return api.Artist(
            artist_id=artist['singerId'],
            name=artist['singer'].strip(),
            pic_url=_get_pic_url(artist['imgs']),
            count=len(songs),
            songs=songs,
        )

    async def get_artist_info_raw(self, singer_id: typing.Union[int, str]) -> dict:
        params = {
            'resourceId': singer_id,
        }

        try:
            _resp = await self.request('GET', _API_GET_ARTIST_INFO, params=params)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('get artist info: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            if resp['code'] != '000000':
                raise exceptions.ResponseError('get artist info: {}'.format(resp['info']))
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('get artist info: {}'.format(e))

        return resp

    async def get_artist_songs_raw(self, singer_id: typing.Union[int, str],
                                   page: int = 1, page_size: int = 20) -> dict:
        params = {
            'singerId': singer_id,
            'pageNo': page,
            'pageSize': page_size,
        }

        try:
            resp = await self.request('GET', _API_GET_ARTIST_SONGS, params=params)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('get artist songs: {}'.format(e))

        try:
            resp = await resp.json(content_type=None)
            if resp['code'] != '000000':
                raise exceptions.ResponseError('get artist songs: {}'.format(resp['info']))
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('get artist songs: {}'.format(e))

        return resp

    async def get_album(self, album_id: typing.Union[int, str]) -> api.Album:
        resp = await self.get_album_raw(album_id)

        try:
            album = resp['resource'][0]
            _songs = album['songItems']
        except (KeyError, IndexError):
            raise exceptions.DataError('get album: no data')

        if not _songs:
            raise exceptions.DataError('get album: no data')

        await self._patch_song_lyric(*_songs)
        _patch_song_url(*_songs)
        _patch_song_info(*_songs)
        songs = _resolve(*_songs)
        return api.Album(
            album_id=album['albumId'],
            name=album['title'].strip(),
            pic_url=_get_pic_url(album['imgItems']),
            count=len(songs),
            songs=songs,
        )

    async def get_album_raw(self, album_id: typing.Union[int, str]) -> dict:
        params = {
            'resourceId': album_id,
        }

        try:
            _resp = await self.request('GET', _API_GET_ALBUM, params=params)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('get album: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            if resp['code'] != '000000':
                raise exceptions.ResponseError('get album: {}'.format(resp.get('error', resp['errcode'])))
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('get album: {}'.format(e))

        return resp

    async def get_playlist(self, playlist_id: typing.Union[int, str]) -> api.Playlist:
        resp = await self.get_playlist_raw(playlist_id)

        try:
            playlist = resp['resource'][0]
            _songs = playlist['songItems']
        except (KeyError, IndexError):
            raise exceptions.DataError('get playlist: no data')

        if not _songs:
            raise exceptions.DataError('get playlist: no data')

        await self._patch_song_lyric(*_songs)
        _patch_song_url(*_songs)
        _patch_song_info(*_songs)
        songs = _resolve(*_songs)
        return api.Playlist(
            playlist_id=playlist['musicListId'],
            name=playlist['title'].strip(),
            pic_url=playlist['imgItem']['img'],
            count=len(songs),
            songs=songs,
        )

    async def get_playlist_raw(self, playlist_id: typing.Union[int, str]) -> dict:
        params = {
            'resourceId': playlist_id,
        }

        try:
            _resp = await self.request('GET', _API_GET_PLAYLIST, params=params)
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            raise exceptions.RequestError('get playlist: {}'.format(e))

        try:
            resp = await _resp.json(content_type=None)
            if resp['code'] != '000000':
                raise exceptions.ResponseError('get playlist: {}'.format(resp['info']))
        except (aiohttp.ClientResponseError, json.JSONDecodeError, KeyError) as e:
            raise exceptions.ResponseError('get playlist: {}'.format(e))

        return resp

    async def request(self, method: str, url: str, **kwargs) -> aiohttp.ClientResponse:
        headers = {
            'channel': '0',
            'Origin': 'http://music.migu.cn/v3',
            'Referer': 'http://music.migu.cn/v3',
            'User-Agent': api.USER_AGENT,
        }
        kwargs.update({
            'headers': headers,
        })
        return await self._session.request(method, url, **kwargs)
