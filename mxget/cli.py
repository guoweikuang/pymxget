import asyncio
import logging
import multiprocessing
import pathlib

import aiofiles
import aiohttp
import mutagen
from mutagen import (
    id3,
)

from mxget import (
    api,
    conf,
    utils,
    exceptions,
)


async def concurrent_download(client: api.API, save_path: str, *songs: api.Song) -> None:
    limit = conf.settings.get('limit')
    if limit is None:
        limit = multiprocessing.cpu_count()
    if limit < 1:
        limit = 1
    if limit > 32:
        limit = 32

    save_path = pathlib.Path(conf.settings['download_dir']).joinpath(
        utils.trim_invalid_file_path_chars(save_path))

    if not save_path.is_dir():
        try:
            save_path.mkdir(parents=True)
        except OSError as e:
            raise exceptions.ClientError("Can't make download dir: {}".format(e))

    sem = asyncio.Semaphore(limit)

    async def worker(song: api.Song):
        async with sem:
            song_info = '{} - {}'.format(song.artist, song.name)
            if not song.playable:
                logging.error('Download [{}] failed: song unavailable'.format(song_info))
                return

            logging.info('Start download: [{}]'.format(song_info))
            filename = utils.trim_invalid_file_path_chars(song_info)
            mp3_file_path = save_path.joinpath(filename + '.mp3')
            if mp3_file_path.is_file() and not conf.settings.get('force', False):
                logging.info('Song already downloaded: [{}]'.format(song_info))
                return

            try:
                resp = await client.request('GET', song.url)
                f = await aiofiles.open(mp3_file_path, 'wb')
                await f.write(await resp.read())
                await f.close()
            except (aiohttp.ClientError, asyncio.TimeoutError) as err:
                logging.error('Download [{}] failed: {}'.format(song_info, err))
                if mp3_file_path.is_file():
                    try:
                        mp3_file_path.unlink()
                    except OSError:
                        pass
                return

            logging.info('Download [{}] complete'.format(song_info))

            if conf.settings.get('tag'):
                logging.info('Update music metadata: [{}]'.format(song_info))
                await _write_tag(client, mp3_file_path, song)

            if conf.settings.get('lyric'):
                logging.info('Save lyric: [{}]'.format(song_info))
                lrc_file_path = save_path.joinpath(filename + '.lrc')
                await _save_lyric(lrc_file_path, song.lyric)

    tasks = [asyncio.ensure_future(worker(song)) for song in songs]
    await asyncio.gather(*tasks)


async def _save_lyric(file_path: pathlib.Path, lyric: str) -> None:
    try:
        f = await aiofiles.open(file_path, 'w', encoding='utf-8')
        await f.write(lyric)
        await f.close()
    except OSError:
        pass


async def _write_tag(client: api.API, file_path: pathlib.Path, song: api.Song) -> None:
    audio = id3.ID3(file_path)
    audio.add(id3.TIT2(encoding=id3.Encoding.UTF8, text=song.name))
    audio.add(id3.TPE1(encoding=id3.Encoding.UTF8, text=song.artist))
    audio.add(id3.TALB(encoding=id3.Encoding.UTF8, text=song.album))

    if song.lyric:
        audio.add(id3.ULT(
            encoding=id3.Encoding.UTF8,
            lang='eng',
            desc=song.name,
            text=song.lyric,
        ))

    if song.pic_url:
        try:
            resp = await client.request('GET', song.pic_url)
            data = await resp.read()
        except (aiohttp.ClientError, asyncio.TimeoutError):
            pass
        else:
            audio.add(id3.APIC(
                encoding=id3.Encoding.UTF8,
                mime='image/jpeg',
                type=id3.PictureType.COVER_FRONT,
                desc='Front cover',
                data=data,
            ))

    try:
        audio.save()
    except mutagen.MutagenError:
        pass
