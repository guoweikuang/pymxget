import abc
import enum
import json
import typing

import aiohttp

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ' \
             'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'


class Platform(enum.IntEnum):
    NetEase = 1000
    QQ = 1001
    MiGu = 1002
    KuGou = 1003
    KuWo = 1004


class SearchSongsData:
    def __init__(self, song_id: typing.Union[int, str], name: str, artist: str, album: str):
        self.id = song_id
        self.name = name
        self.artist = artist
        self.album = album

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'artist': self.artist,
            'album': self.album,
        }

    def __str__(self):
        return json.dumps(self, default=lambda o: o.__dict__, indent=4, ensure_ascii=False)


class SearchSongsResult:
    def __init__(self, keyword: str, count: int = 0, songs: typing.List[SearchSongsData] = None):
        if songs is None:
            songs = []
        self.keyword: str = keyword
        self.count: int = count
        self.songs = songs

    def serialize(self):
        return {
            'keyword': self.keyword,
            'count': self.count,
            'songs': [song.serialize() for song in self.songs],
        }

    def __str__(self):
        return json.dumps(self, default=lambda o: o.__dict__, indent=4, ensure_ascii=False)


class Song:
    def __init__(self, name: str, artist: str, album: str = '',
                 pic_url: str = None, lyric: str = None, url: str = None):
        self.name = name
        self.artist = artist
        self.album = album
        self.pic_url = pic_url if pic_url is not None else ''
        self.lyric = lyric if lyric is not None else ''
        self.url = url if url is not None else ''
        self.playable = self.url != ''

    def serialize(self):
        data = {
            'name': self.name,
            'artist': self.artist,
            'album': self.album,
            'pic_url': self.pic_url,
            'lyric': self.lyric,
            'playable': self.playable,
            'url': self.url,
        }
        if not self.playable:
            data.pop('url')
        return data

    def __str__(self):
        return json.dumps(self, default=lambda o: o.__dict__, indent=4, ensure_ascii=False)


class Artist:
    def __init__(self, name: str, pic_url: str = '', count: int = 0, songs: typing.List[Song] = None):
        if songs is None:
            songs = []
        self.name = name
        self.pic_url = pic_url
        self.count = count
        self.songs = songs

    def serialize(self):
        return {
            'name': self.name,
            'count': self.count,
            'pic_url': self.pic_url,
            'songs': [song.serialize() for song in self.songs],
        }

    def __str__(self):
        return json.dumps(self, default=lambda o: o.__dict__, indent=4, ensure_ascii=False)


class Album:
    def __init__(self, name: str, pic_url: str = '', count: int = 0, songs: typing.List[Song] = None):
        if songs is None:
            songs = []
        self.name = name
        self.pic_url = pic_url
        self.count = count
        self.songs = songs

    def serialize(self):
        return {
            'name': self.name,
            'count': self.count,
            'pic_url': self.pic_url,
            'songs': [song.serialize() for song in self.songs],
        }

    def __str__(self):
        return json.dumps(self, default=lambda o: o.__dict__, indent=4, ensure_ascii=False)


class Playlist:
    def __init__(self, name: str, pic_url: str = '', count: int = 0, songs: typing.List[Song] = None):
        if songs is None:
            songs = []
        self.name = name
        self.pic_url = pic_url
        self.count = count
        self.songs = songs

    def serialize(self):
        return {
            'name': self.name,
            'count': self.count,
            'pic_url': self.pic_url,
            'songs': [song.serialize() for song in self.songs],
        }

    def __str__(self):
        return json.dumps(self, default=lambda o: o.__dict__, indent=4, ensure_ascii=False)


class API(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def __aenter__(self):
        pass

    @abc.abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    @abc.abstractmethod
    def platform(self) -> Platform:
        """平台标识"""

    @abc.abstractmethod
    async def search_songs(self, keyword: str) -> SearchSongsResult:
        """搜索歌曲"""

    @abc.abstractmethod
    async def get_song(self, song_id: str) -> Song:
        """获取单曲"""

    @abc.abstractmethod
    async def get_artist(self, artist_id: str) -> Artist:
        """获取歌手热门歌曲"""

    @abc.abstractmethod
    async def get_album(self, album_id: str) -> Album:
        """获取专辑"""

    @abc.abstractmethod
    async def get_playlist(self, playlist_id: str) -> Playlist:
        """获取歌单"""

    @abc.abstractmethod
    async def request(self, method: str, url: str, **kwargs) -> aiohttp.ClientResponse:
        """网络请求"""

    @abc.abstractmethod
    async def close(self):
        """释放资源"""
