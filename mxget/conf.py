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
    'dir': './downloads',
    'platform': 'nc',
}

_PLATFORM_CLIENTS = {
    'netease': netease.NetEase,
    'nc': netease.NetEase,
    'tencent': qq.QQ,
    'qq': qq.QQ,
    'migu': migu.MiGu,
    'mg': migu.MiGu,
    'kugou': kugou.KuGou,
    'kg': kugou.KuGou,
    'kuwo': kuwo.KuWo,
    'kw': kuwo.KuWo,
    'xiami': xiami.XiaMi,
    'xm': xiami.XiaMi,
    'qianqian': baidu.BaiDu,
    'baidu': baidu.BaiDu,
    'bd': baidu.BaiDu,
}

_PLATFORM_DESCS = {
    'netease': 'netease cloud music',
    'nc': 'netease cloud music',
    'tencent': 'qq music',
    'qq': 'qq music',
    'migu': 'migu music',
    'mg': 'migu music',
    'kugou': 'kugou music',
    'kg': 'kugou music',
    'kuwo': 'kuwo music',
    'kw': 'kuwo music',
    'xiami': 'xiami music',
    'xm': 'xiami music',
    'qianqian': 'qianqian music',
    'baidu': 'qianqian music',
    'bd': 'qianqian music',
}


def _get_user_dir_path() -> pathlib.Path:
    xdg_config_home = os.environ.get('XDG_CONFIG_HOME', '~/.config')
    try:
        user_dir = pathlib.Path(xdg_config_home, 'mxget').expanduser()
    except RuntimeError:
        return pathlib.Path('.')
    return user_dir


def get_platform_desc(platform: str) -> typing.Optional[str]:
    return _PLATFORM_DESCS.get(platform)


def get_platform_client(platform: str) -> typing.Optional[api.API]:
    client = _PLATFORM_CLIENTS.get(platform)
    return client() if client is not None else None


class Settings(dict):
    def __getattr__(self, item):
        return self.get(item)

    def __setattr__(self, key, value):
        self[key] = value

    def init(self) -> None:
        self._setup_user_dir()
        self._setup_settings_path()

        if not self.settings_path.is_file():
            self._init_settings_file()

        try:
            self.update(self._settings_from_file())
        except (OSError, json.JSONDecodeError) as e:
            self.update(_DEFAULT_SETTINGS)
            raise exceptions.ClientError("can't load settings from file: {}".format(e))

        platform = self.get('platform')
        if get_platform_desc(platform) is None:
            self['platform'] = _DEFAULT_SETTINGS['platform']
            raise exceptions.ClientError('unexpected music platform: "{}"'.format(platform))

        self.make_download_dir()

    def _init_settings_file(self) -> None:
        self.save(_DEFAULT_SETTINGS)

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
            path = self.get('dir')
        download_dir = pathlib.Path(path)
        if not download_dir.is_dir():
            try:
                download_dir.mkdir(parents=True)
            except OSError as e:
                self['dir'] = _DEFAULT_SETTINGS['dir']
                raise exceptions.ClientError("can't make download dir: {}".format(e))

    def save(self, cfg: dict = None) -> None:
        if cfg is None:
            cfg = {
                'platform': self['platform'],
                'dir': self['dir'],
            }
        try:
            with self.settings_path.open(mode='w') as settings_file:
                json.dump(cfg, settings_file, indent=4)
        except OSError as e:
            raise exceptions.ClientError("can't save settings to file: {}".format(e))

    def reset(self) -> None:
        self._init_settings_file()


settings = Settings()
