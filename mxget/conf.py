import json
import os
import pathlib
import typing

from mxget import (
    api,
    exceptions,
)
from mxget.provider import (
    netease,
    qq,
    migu,
    kugou,
    kuwo
)

_DEFAULT_SETTINGS = {
    'download_dir': './downloads',
    'music_platform': api.Platform.NetEase,
}

_PLATFORM_IDS = {
    'netease': api.Platform.NetEase,
    'nc': api.Platform.NetEase,
    'tencent': api.Platform.QQ,
    'qq': api.Platform.QQ,
    'migu': api.Platform.MiGu,
    'mg': api.Platform.MiGu,
    'kugou': api.Platform.KuGou,
    'kg': api.Platform.KuGou,
    'kuwo': api.Platform.KuWo,
    'kw': api.Platform.KuWo,
}

_PLATFORM_CLIENTS = {
    api.Platform.NetEase: netease.NetEase,
    api.Platform.QQ: qq.QQ,
    api.Platform.MiGu: migu.MiGu,
    api.Platform.KuGou: kugou.KuGou,
    api.Platform.KuWo: kuwo.KuWo,
}

_PLATFORM_SITES = {
    api.Platform.NetEase: 'music.163.com',
    api.Platform.QQ: 'y.qq.com',
    api.Platform.MiGu: 'music.migu.cn',
    api.Platform.KuGou: 'kugou.com',
    api.Platform.KuWo: 'kuwo.cn',
}


def _get_user_dir_path() -> pathlib.Path:
    xdg_config_home = os.environ.get('XDG_CONFIG_HOME', '~/.config')
    try:
        user_dir = pathlib.Path(xdg_config_home, 'mxget').expanduser()
    except RuntimeError:
        return pathlib.Path('.')
    return user_dir


def get_platform(platform_flag: str) -> typing.Optional[int]:
    return _PLATFORM_IDS.get(platform_flag)


def get_client(platform_id: api.Platform) -> typing.Optional[api.API]:
    client = _PLATFORM_CLIENTS.get(platform_id)
    return client() if client is not None else None


def get_site(platform_id: api.Platform) -> typing.Optional[str]:
    return _PLATFORM_SITES.get(platform_id)


class Settings(dict):
    def __getattr__(self, item):
        return self.get(item)

    def __setattr__(self, key, value):
        self[key] = value

    def init(self):
        self._setup_user_dir()
        self._setup_settings_path()
        self._init_settings_file()

        try:
            self.update(self._settings_from_file())
        except (OSError, json.JSONDecodeError) as e:
            self.update(_DEFAULT_SETTINGS)
            raise exceptions.ClientError("Can't load settings from file: {}".format(e))

        platform_id = self.get('music_platform')
        if get_site(platform_id) is None:
            self['music_platform'] = _DEFAULT_SETTINGS['music_platform']
            raise exceptions.ClientError('Unexpected music platform: "{}"'.format(platform_id))

        self.make_download_dir()

    def _init_settings_file(self):
        if not self.settings_path.is_file():
            self.update(_DEFAULT_SETTINGS)
            self.save()

    def _setup_user_dir(self):
        user_dir = _get_user_dir_path()
        if not user_dir.is_dir():
            user_dir.mkdir(parents=True)
        self.user_dir = user_dir

    def _setup_settings_path(self):
        filename = 'mxget.json' if self.user_dir != '.' else '.mxget.json'
        self.settings_path = self.user_dir.joinpath(filename)

    def _settings_from_file(self):
        with self.settings_path.open(mode='r') as settings_file:
            return json.load(settings_file)

    def make_download_dir(self, path: str = None):
        if path is None:
            path = self.get('download_dir')
        download_dir = pathlib.Path(path)
        if not download_dir.is_dir():
            try:
                download_dir.mkdir(parents=True)
            except OSError as e:
                self['download_dir'] = _DEFAULT_SETTINGS['download_dir']
                raise exceptions.ClientError("Can't make download dir: {}".format(e))

    def save(self, cfg: dict = None):
        if cfg is None:
            cfg = {
                'music_platform': self['music_platform'],
                'download_dir': self['download_dir'],
            }
        try:
            with self.settings_path.open(mode='w') as settings_file:
                json.dump(cfg, settings_file, indent=4)
        except OSError as e:
            raise exceptions.ClientError("Can't save settings to file: {}".format(e))

    def reset(self):
        """在配置初始化异常时调用，重置异常配置为默认值"""
        self.save()


settings = Settings()
