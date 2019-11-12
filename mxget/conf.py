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
    kuwo,
    xiami,
    baidu,
)

_DEFAULT_SETTINGS = {
    'download_dir': './downloads',
    'music_platform': api.PlatformId.NetEase,
}

_PLATFORM_IDS = {
    'netease': api.PlatformId.NetEase,
    'nc': api.PlatformId.NetEase,
    'tencent': api.PlatformId.QQ,
    'qq': api.PlatformId.QQ,
    'migu': api.PlatformId.MiGu,
    'mg': api.PlatformId.MiGu,
    'kugou': api.PlatformId.KuGou,
    'kg': api.PlatformId.KuGou,
    'kuwo': api.PlatformId.KuWo,
    'kw': api.PlatformId.KuWo,
    'xiami': api.PlatformId.XiaMi,
    'xm': api.PlatformId.XiaMi,
    'qianqian': api.PlatformId.BaiDu,
    'baidu': api.PlatformId.BaiDu,
    'bd': api.PlatformId.BaiDu,
}

_PLATFORM_CLIENTS = {
    api.PlatformId.NetEase: netease.NetEase,
    api.PlatformId.QQ: qq.QQ,
    api.PlatformId.MiGu: migu.MiGu,
    api.PlatformId.KuGou: kugou.KuGou,
    api.PlatformId.KuWo: kuwo.KuWo,
    api.PlatformId.XiaMi: xiami.XiaMi,
    api.PlatformId.BaiDu: baidu.BaiDu,
}

_PLATFORM_DESCS = {
    api.PlatformId.NetEase: 'netease cloud music',
    api.PlatformId.QQ: 'qq music',
    api.PlatformId.MiGu: 'migu music',
    api.PlatformId.KuGou: 'kugou music',
    api.PlatformId.KuWo: 'kuwo music',
    api.PlatformId.XiaMi: 'xiami music',
    api.PlatformId.BaiDu: 'qianqian music',
}


def _get_user_dir_path() -> pathlib.Path:
    xdg_config_home = os.environ.get('XDG_CONFIG_HOME', '~/.config')
    try:
        user_dir = pathlib.Path(xdg_config_home, 'mxget').expanduser()
    except RuntimeError:
        return pathlib.Path('.')
    return user_dir


def get_platform_id(platform_flag: str) -> typing.Optional[api.PlatformId]:
    return _PLATFORM_IDS.get(platform_flag)


def get_platform_desc(platform_id: api.PlatformId) -> typing.Optional[str]:
    return _PLATFORM_DESCS.get(platform_id)


def get_client(platform_id: api.PlatformId) -> typing.Optional[api.API]:
    client = _PLATFORM_CLIENTS.get(platform_id)
    return client() if client is not None else None


class Settings(dict):
    def __getattr__(self, item):
        return self.get(item)

    def __setattr__(self, key, value):
        self[key] = value

    def init(self) -> None:
        self._setup_user_dir()
        self._setup_settings_path()
        self._init_settings_file()

        try:
            self.update(self._settings_from_file())
        except (OSError, json.JSONDecodeError) as e:
            self.update(_DEFAULT_SETTINGS)
            raise exceptions.ClientError("Can't load settings from file: {}".format(e))

        platform_id = self.get('music_platform')
        if get_platform_desc(platform_id) is None:
            self['music_platform'] = _DEFAULT_SETTINGS['music_platform']
            raise exceptions.ClientError('Unexpected music platform: "{}"'.format(platform_id))

        self.make_download_dir()

    def _init_settings_file(self) -> None:
        if not self.settings_path.is_file():
            self.update(_DEFAULT_SETTINGS)
            self.save()

    def _setup_user_dir(self) -> None:
        user_dir = _get_user_dir_path()
        if not user_dir.is_dir():
            user_dir.mkdir(parents=True)
        self.user_dir = user_dir

    def _setup_settings_path(self) -> None:
        filename = 'mxget.json' if self.user_dir != '.' else '.mxget.json'
        self.settings_path = self.user_dir.joinpath(filename)

    def _settings_from_file(self) -> dict:
        with self.settings_path.open(mode='r') as settings_file:
            return json.load(settings_file)

    def make_download_dir(self, path: str = None) -> None:
        if path is None:
            path = self.get('download_dir')
        download_dir = pathlib.Path(path)
        if not download_dir.is_dir():
            try:
                download_dir.mkdir(parents=True)
            except OSError as e:
                self['download_dir'] = _DEFAULT_SETTINGS['download_dir']
                raise exceptions.ClientError("Can't make download dir: {}".format(e))

    def save(self, cfg: dict = None) -> None:
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

    def reset(self) -> None:
        """在配置初始化异常时调用，重置异常配置为默认值"""
        self.save()


settings = Settings()
