import asyncio
import logging
import sys

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


@click.group(context_settings=_CONTEXT_SETTINGS)
@click.version_option(version=mxget.__version__)
def root():
    """
\b
A simple tool that help you search and download your favorite music,
please visit https://github.com/winterssy/mxget for more detail."""
    try:
        conf.settings.init()
    except exceptions.ClientError as e:
        logging.critical("Initialize config failed, reset to defaults: {}".format(e))
        conf.settings.save()
        sys.exit(1)


@root.command(help='Specify the default behavior of mxget.')
@click.option('--from', 'platform', help='Specify the default music platform')
@click.option('--dir', 'cwd', help='Specify the default download directory')
@click.option('--show', is_flag=True, help='Show current settings')
@click.option('--reset', is_flag=True, help='Reset default settings')
def config(platform: str, cwd: str, show: bool, reset: bool) -> None:
    ctx = click.get_current_context()
    if not any(v for v in ctx.params.values()):
        click.echo(ctx.get_help())
        ctx.exit()

    if show:
        print("""
    download dir   -> {}
    music platform -> {} [{}]
""".format(conf.settings['dir'], conf.settings['platform'],
           conf.get_platform_desc(conf.settings['platform'])), end='')
        return

    if reset:
        conf.settings.reset()
        return

    if platform is not None:
        if conf.get_platform_desc(platform) is None:
            logging.critical('Unexpected music platform: "{}"'.format(platform))
            sys.exit(1)
        conf.settings['platform'] = platform

    if cwd is not None:
        try:
            conf.settings.make_download_dir(cwd)
        except exceptions.ClientError as e:
            logging.critical(e)
            sys.exit(1)
        conf.settings['dir'] = cwd

    if platform is not None or cwd is not None:
        conf.settings.save()


@root.command(help='Search songs from the specified music platform.')
@click.option('--from', 'platform', help='Music platform')
@click.option('--keyword', '-k', prompt=True, help='Search keyword')
def search(platform, keyword) -> None:
    if platform is None:
        platform = conf.settings['platform']

    client = conf.get_platform_client(platform)
    if client is None:
        logging.critical('Unexpected music platform: "{}"'.format(platform))
        sys.exit(1)

    loop = asyncio.get_event_loop()
    try:
        print('Search "{}" from [{}]...\n'.format(keyword, conf.get_platform_desc(platform)))
        resp = loop.run_until_complete(client.search_songs(keyword))
        for i, v in enumerate(resp.songs):
            print('[{:02d}] {} - {} - {}'.format(i + 1, v.name, v.artist, v.id))
        if platform is None:
            print('\nCommand: mxget song --id [id]')
        else:
            print('\nCommand: mxget song --from {} --id [id]'.format(platform))
    except exceptions.ClientError as e:
        logging.critical(e)
    finally:
        loop.run_until_complete(client.close())


@root.command(help='Fetch and download single song via its id.')
@click.option('--from', 'platform', help='Music platform')
@click.option('--id', 'song_id', prompt=True, help='Song id')
@click.option('--tag', is_flag=True, help='Update music metadata')
@click.option('--lyric', is_flag=True, help='Download lyric')
@click.option('--force', is_flag=True, help='Overwrite already downloaded music')
def song(platform: str, song_id: str, **kwargs) -> None:
    if platform is None:
        platform = conf.settings['platform']

    client = conf.get_platform_client(platform)
    if client is None:
        logging.critical('Unexpected music platform: "{}"'.format(platform))
        sys.exit(1)

    conf.settings.update(kwargs)
    loop = asyncio.get_event_loop()
    try:
        logging.info('Fetch song [{}] from [{}]'.format(song_id, conf.get_platform_desc(platform)))
        resp = loop.run_until_complete(client.get_song(song_id))
        loop.run_until_complete(cli.concurrent_download(client, '.', resp))
    except exceptions.ClientError as e:
        logging.critical(e)
    finally:
        loop.run_until_complete(client.close())


@root.command(help="Fetch and download artist's hot songs via its id.")
@click.option('--from', 'platform', help='Music platform')
@click.option('--id', 'artist_id', prompt=True, help='Artist id')
@click.option('--tag', is_flag=True, help='Update music metadata')
@click.option('--lyric', is_flag=True, help='Download lyric')
@click.option('--force', is_flag=True, help='Overwrite already downloaded music')
@click.option('--limit', type=int, help='Concurrent download limit')
def artist(platform: str, artist_id: str, **kwargs) -> None:
    if platform is None:
        platform = conf.settings['platform']

    client = conf.get_platform_client(platform)
    if client is None:
        logging.critical('Unexpected music platform: "{}"'.format(platform))
        sys.exit(1)

    conf.settings.update(kwargs)
    loop = asyncio.get_event_loop()
    try:
        logging.info('Fetch artist [{}] from [{}]'.format(artist_id, conf.get_platform_desc(platform)))
        resp = loop.run_until_complete(client.get_artist(artist_id))
        loop.run_until_complete(cli.concurrent_download(client, resp.name, *resp.songs))
    except exceptions.ClientError as e:
        logging.critical(e)
    finally:
        loop.run_until_complete(client.close())


@root.command(help="Fetch and download album's songs via its id.")
@click.option('--from', 'platform', help='Music platform')
@click.option('--id', 'album_id', prompt=True, help='Album id')
@click.option('--tag', is_flag=True, help='Update music metadata')
@click.option('--lyric', is_flag=True, help='Download lyric')
@click.option('--force', is_flag=True, help='Overwrite already downloaded music')
@click.option('--limit', type=int, help='Concurrent download limit')
def album(platform: str, album_id: str, **kwargs) -> None:
    if platform is None:
        platform = conf.settings['platform']

    client = conf.get_platform_client(platform)
    if client is None:
        logging.critical('Unexpected music platform: "{}"'.format(platform))
        sys.exit(1)

    conf.settings.update(kwargs)
    loop = asyncio.get_event_loop()
    try:
        logging.info('Fetch album [{}] from [{}]'.format(album_id, conf.get_platform_desc(platform)))
        resp = loop.run_until_complete(client.get_album(album_id))
        loop.run_until_complete(cli.concurrent_download(client, resp.name, *resp.songs))
    except exceptions.ClientError as e:
        logging.critical(e)
    finally:
        loop.run_until_complete(client.close())


@root.command(help="Fetch and download playlist's songs via its id.")
@click.option('--from', 'platform', help='Music platform')
@click.option('--id', 'playlist_id', prompt=True, help='Playlist id')
@click.option('--tag', is_flag=True, help='Update music metadata')
@click.option('--lyric', is_flag=True, help='Download lyric')
@click.option('--force', is_flag=True, help='Overwrite already downloaded music')
@click.option('--limit', type=int, show_default=True, help='Concurrent download limit')
def playlist(platform: str, playlist_id: str, **kwargs) -> None:
    if platform is None:
        platform = conf.settings['platform']

    client = conf.get_platform_client(platform)
    if client is None:
        logging.critical('Unexpected music platform: "{}"'.format(platform))
        sys.exit(1)

    conf.settings.update(kwargs)
    loop = asyncio.get_event_loop()
    try:
        logging.info('Fetch playlist [{}] from [{}]'.format(playlist_id, conf.get_platform_desc(platform)))
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
