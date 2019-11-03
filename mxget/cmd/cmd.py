import asyncio
import logging
import sys
import typing

import click

import mxget
from mxget import (
    cli,
    conf,
    exceptions,
    server,
)

_CONTEXT_SETTINGS = {
    "help_option_names": ["-h", "--help"],
}


def _get_platform_id(platform_flag: str = None) -> typing.Optional[int]:
    if platform_flag is None:
        platform_id = conf.settings['music_platform']
    else:
        platform_id = conf.get_platform(platform_flag)
        if platform_id is None:
            return None
    return platform_id


@click.group(context_settings=_CONTEXT_SETTINGS)
@click.version_option(version=mxget.__version__)
def root():
    """
\b
A simple tool that help you download your favorite music,
please visit https://github.com/winterssy/pymxget for more detail."""
    try:
        conf.settings.init()
    except exceptions.ClientError as e:
        logging.critical('Failed to initialize client, reset to defaults: {}'.format(e))
        conf.settings.reset()
        sys.exit(1)


@root.command(help='Specify the default behavior of mxget.')
@click.option('--from', 'platform_flag', help='Specify the default music platform')
@click.option('--cwd', help='Specify the default download directory')
def config(platform_flag: str, cwd: str) -> None:
    if platform_flag is None and cwd is None:
        print("""
Current settings:
    download dir -> {}
    music platform -> {} [{}]
""".format(conf.settings['download_dir'], conf.settings['music_platform'],
           conf.get_site(conf.settings['music_platform'])), end='')
        return

    if platform_flag is not None:
        platform_id = conf.get_platform(platform_flag)
        if platform_id is None:
            logging.critical('Unexpected music platform: "{}"'.format(platform_flag))
            sys.exit(1)
        conf.settings['music_platform'] = platform_id

    if cwd is not None:
        try:
            conf.settings.make_download_dir(cwd)
        except exceptions.ClientError as e:
            logging.critical(e)
            sys.exit(1)
        conf.settings['download_dir'] = cwd

    conf.settings.save()


@root.command(help='Search song from the Internet.')
@click.option('--from', 'platform_flag', help='Music platform')
@click.option('--keyword', '-k', prompt=True, help='Search keyword')
def search(platform_flag, keyword) -> None:
    platform_id = _get_platform_id(platform_flag)
    if platform_id is None:
        logging.critical('Unexpected music platform: "{}"'.format(platform_flag))
        sys.exit(1)

    client = conf.get_client(platform_id)
    loop = asyncio.get_event_loop()
    try:
        resp = loop.run_until_complete(client.search_song(keyword))
        for i, v in enumerate(resp.songs):
            print('[{:02d}] {} - {} - {} - {}'.format(i + 1, v.name, v.artist, v.album, v.id))
        if platform_flag is None:
            print('\nCommand: mxget song --id [id]')
        else:
            print('\nCommand: mxget song --from {} --id [id]'.format(platform_flag))
    except exceptions.ClientError as e:
        logging.critical(e)
    finally:
        loop.run_until_complete(client.close())


@root.command(help='Fetch and download song via its id.')
@click.option('--from', 'platform_flag', help='Music platform')
@click.option('--id', 'song_id', prompt=True, help='Song id')
@click.option('--tag', is_flag=True, help='Update music metadata')
@click.option('--lyric', is_flag=True, help='Download lyric')
@click.option('--force', is_flag=True, help='Overwrite already downloaded music')
def song(platform_flag: str, song_id: str, **kwargs) -> None:
    platform_id = _get_platform_id(platform_flag)
    if platform_id is None:
        logging.critical('Unexpected music platform: "{}"'.format(platform_flag))
        sys.exit(1)

    conf.settings.update(kwargs)
    client = conf.get_client(platform_id)
    loop = asyncio.get_event_loop()
    try:
        logging.info('Fetch song {} from {}'.format(song_id, conf.get_site(platform_id)))
        resp = loop.run_until_complete(client.get_song(song_id))
        loop.run_until_complete(cli.concurrent_download(client, '.', resp))
    except exceptions.ClientError as e:
        logging.critical(e)
    finally:
        loop.run_until_complete(client.close())


@root.command(help='Fetch and download artist hot songs via its id.')
@click.option('--from', 'platform_flag', help='Music platform')
@click.option('--id', 'artist_id', prompt=True, help='Artist id')
@click.option('--tag', is_flag=True, help='Update music metadata')
@click.option('--lyric', is_flag=True, help='Download lyric')
@click.option('--force', is_flag=True, help='Overwrite already downloaded music')
@click.option('--limit', type=int, help='Concurrent download limit')
def artist(platform_flag: str, artist_id: str, **kwargs) -> None:
    platform_id = _get_platform_id(platform_flag)
    if platform_id is None:
        logging.critical('Unexpected music platform: "{}"'.format(platform_flag))
        sys.exit(1)

    conf.settings.update(kwargs)
    client = conf.get_client(platform_id)
    loop = asyncio.get_event_loop()
    try:
        logging.info('Fetch artist {} from {}'.format(artist_id, conf.get_site(platform_id)))
        resp = loop.run_until_complete(client.get_artist(artist_id))
        loop.run_until_complete(cli.concurrent_download(client, resp.name, *resp.songs))
    except exceptions.ClientError as e:
        logging.critical(e)
    finally:
        loop.run_until_complete(client.close())


@root.command(help='Fetch and download album songs via its id.')
@click.option('--from', 'platform_flag', help='Music platform')
@click.option('--id', 'album_id', prompt=True, help='Album id')
@click.option('--tag', is_flag=True, help='Update music metadata')
@click.option('--lyric', is_flag=True, help='Download lyric')
@click.option('--force', is_flag=True, help='Overwrite already downloaded music')
@click.option('--limit', type=int, help='Concurrent download limit')
def album(platform_flag: str, album_id: str, **kwargs) -> None:
    platform_id = _get_platform_id(platform_flag)
    if platform_id is None:
        logging.critical('Unexpected music platform: "{}"'.format(platform_flag))
        sys.exit(1)

    conf.settings.update(kwargs)
    client = conf.get_client(platform_id)
    loop = asyncio.get_event_loop()
    try:
        logging.info('Fetch album {} from {}'.format(album_id, conf.get_site(platform_id)))
        resp = loop.run_until_complete(client.get_album(album_id))
        loop.run_until_complete(cli.concurrent_download(client, resp.name, *resp.songs))
    except exceptions.ClientError as e:
        logging.critical(e)
    finally:
        loop.run_until_complete(client.close())


@root.command(help='Fetch and download playlist songs via its id.')
@click.option('--from', 'platform_flag', help='Music platform')
@click.option('--id', 'playlist_id', prompt=True, help='Playlist id')
@click.option('--tag', is_flag=True, help='Update music metadata')
@click.option('--lyric', is_flag=True, help='Download lyric')
@click.option('--force', is_flag=True, help='Overwrite already downloaded music')
@click.option('--limit', type=int, show_default=True, help='Concurrent download limit')
def playlist(platform_flag: str, playlist_id: str, **kwargs) -> None:
    platform_id = _get_platform_id(platform_flag)
    if platform_id is None:
        logging.critical('Unexpected music platform: "{}"'.format(platform_flag))
        sys.exit(1)

    conf.settings.update(kwargs)
    client = conf.get_client(platform_id)
    loop = asyncio.get_event_loop()
    try:
        logging.info('Fetch playlist {} from {}'.format(playlist_id, conf.get_site(platform_id)))
        resp = loop.run_until_complete(client.get_playlist(playlist_id))
        loop.run_until_complete(cli.concurrent_download(client, resp.name, *resp.songs))
    except exceptions.ClientError as e:
        logging.critical(e)
    finally:
        loop.run_until_complete(client.close())


@root.command(help='Run mxget as an API server.')
@click.option('--port', type=int, default=8080, show_default=True, help='server listening port')
@click.option('--debug', is_flag=True, hidden=True, help='debug mode')
def serve(port: int, debug: bool) -> None:
    server.run(port, debug)
