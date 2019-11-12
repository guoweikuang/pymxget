from aiohttp import web

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

routes = web.RouteTableDef()


def success_response(client: api.API, data: dict):
    return web.json_response(data={
        'code': 200,
        'data': data,
        'platform': client.platform_id(),
    }, status=200)


def error_response(client: api.API, e: exceptions.ClientError):
    return web.json_response(data={
        'code': 500,
        'msg': str(e),
        'platform': client.platform_id(),
    }, status=500)


async def search_songs(client: api.API, keyword: str):
    try:
        resp = await client.search_songs(keyword)
    except exceptions.ClientError as e:
        await client.close()
        return error_response(client, e)

    await client.close()
    return success_response(client, resp.serialize())


async def get_song(client: api.API, song_id: str):
    try:
        resp = await client.get_song(song_id)
    except exceptions.ClientError as e:
        await client.close()
        return error_response(client, e)

    await client.close()
    return success_response(client, resp.serialize())


async def get_artist(client: api.API, artist_id: str):
    try:
        resp = await client.get_artist(artist_id)
    except exceptions.ClientError as e:
        await client.close()
        return error_response(client, e)

    await client.close()
    return success_response(client, resp.serialize())


async def get_album(client: api.API, album_id: str):
    try:
        resp = await client.get_album(album_id)
    except exceptions.ClientError as e:
        await client.close()
        return error_response(client, e)

    await client.close()
    return success_response(client, resp.serialize())


async def get_playlist(client: api.API, playlist_id: str):
    try:
        resp = await client.get_playlist(playlist_id)
    except exceptions.ClientError as e:
        await client.close()
        return error_response(client, e)

    await client.close()
    return success_response(client, resp.serialize())


@routes.get('/api/netease/search/{keyword}')
async def search_songs_from_netease(request: web.Request):
    return await search_songs(netease.NetEase(), request.match_info['keyword'])


@routes.get('/api/netease/song/{song_id}')
async def get_song_from_netease(request: web.Request):
    return await get_song(netease.NetEase(), request.match_info['song_id'])


@routes.get('/api/netease/artist/{artist_id}')
async def get_artist_from_netease(request: web.Request):
    return await get_artist(netease.NetEase(), request.match_info['artist_id'])


@routes.get('/api/netease/album/{album_id}')
async def get_album_from_netease(request: web.Request):
    return await get_album(netease.NetEase(), request.match_info['album_id'])


@routes.get('/api/netease/playlist/{playlist_id}')
async def get_playlist_from_netease(request: web.Request):
    return await get_playlist(netease.NetEase(), request.match_info['playlist_id'])


@routes.get('/api/qq/search/{keyword}')
async def search_songs_from_qq(request: web.Request):
    return await search_songs(qq.QQ(), request.match_info['keyword'])


@routes.get('/api/qq/song/{song_id}')
async def get_song_from_qq(request: web.Request):
    return await get_song(qq.QQ(), request.match_info['song_id'])


@routes.get('/api/qq/artist/{artist_id}')
async def get_artist_from_qq(request: web.Request):
    return await get_artist(qq.QQ(), request.match_info['artist_id'])


@routes.get('/api/qq/album/{album_id}')
async def get_album_from_qq(request: web.Request):
    return await get_album(qq.QQ(), request.match_info['album_id'])


@routes.get('/api/qq/playlist/{playlist_id}')
async def get_playlist_from_qq(request: web.Request):
    return await get_playlist(qq.QQ(), request.match_info['playlist_id'])


@routes.get('/api/migu/search/{keyword}')
async def search_songs_from_migu(request: web.Request):
    return await search_songs(migu.MiGu(), request.match_info['keyword'])


@routes.get('/api/migu/song/{song_id}')
async def get_song_from_migu(request: web.Request):
    return await get_song(migu.MiGu(), request.match_info['song_id'])


@routes.get('/api/migu/artist/{artist_id}')
async def get_artist_from_migu(request: web.Request):
    return await get_artist(migu.MiGu(), request.match_info['artist_id'])


@routes.get('/api/migu/album/{album_id}')
async def get_album_from_migu(request: web.Request):
    return await get_album(migu.MiGu(), request.match_info['album_id'])


@routes.get('/api/migu/playlist/{playlist_id}')
async def get_playlist_from_migu(request: web.Request):
    return await get_playlist(migu.MiGu(), request.match_info['playlist_id'])


@routes.get('/api/kugou/search/{keyword}')
async def search_songs_from_kugou(request: web.Request):
    return await search_songs(kugou.KuGou(), request.match_info['keyword'])


@routes.get('/api/kugou/song/{song_id}')
async def get_song_from_kugou(request: web.Request):
    return await get_song(kugou.KuGou(), request.match_info['song_id'])


@routes.get('/api/kugou/artist/{artist_id}')
async def get_artist_from_kugou(request: web.Request):
    return await get_artist(kugou.KuGou(), request.match_info['artist_id'])


@routes.get('/api/kugou/album/{album_id}')
async def get_album_from_kugou(request: web.Request):
    return await get_album(kugou.KuGou(), request.match_info['album_id'])


@routes.get('/api/kugou/playlist/{playlist_id}')
async def get_playlist_from_kugou(request: web.Request):
    return await get_playlist(kugou.KuGou(), request.match_info['playlist_id'])


@routes.get('/api/kuwo/search/{keyword}')
async def search_songs_from_kuwo(request: web.Request):
    return await search_songs(kuwo.KuWo(), request.match_info['keyword'])


@routes.get('/api/kuwo/song/{song_id}')
async def get_song_from_kuwo(request: web.Request):
    return await get_song(kuwo.KuWo(), request.match_info['song_id'])


@routes.get('/api/kuwo/artist/{artist_id}')
async def get_artist_from_kuwo(request: web.Request):
    return await get_artist(kuwo.KuWo(), request.match_info['artist_id'])


@routes.get('/api/kuwo/album/{album_id}')
async def get_album_from_kuwo(request: web.Request):
    return await get_album(kuwo.KuWo(), request.match_info['album_id'])


@routes.get('/api/kuwo/playlist/{playlist_id}')
async def get_playlist_from_kuwo(request: web.Request):
    return await get_playlist(kuwo.KuWo(), request.match_info['playlist_id'])


@routes.get('/api/xiami/search/{keyword}')
async def search_songs_from_xiami(request: web.Request):
    return await search_songs(xiami.XiaMi(), request.match_info['keyword'])


@routes.get('/api/xiami/song/{song_id}')
async def get_song_from_xiami(request: web.Request):
    return await get_song(xiami.XiaMi(), request.match_info['song_id'])


@routes.get('/api/xiami/artist/{artist_id}')
async def get_artist_from_xiami(request: web.Request):
    return await get_artist(xiami.XiaMi(), request.match_info['artist_id'])


@routes.get('/api/xiami/album/{album_id}')
async def get_album_from_xiami(request: web.Request):
    return await get_album(xiami.XiaMi(), request.match_info['album_id'])


@routes.get('/api/xiami/playlist/{playlist_id}')
async def get_playlist_from_xiami(request: web.Request):
    return await get_playlist(xiami.XiaMi(), request.match_info['playlist_id'])


@routes.get('/api/qianqian/search/{keyword}')
async def search_songs_from_qianqian(request: web.Request):
    return await search_songs(baidu.BaiDu(), request.match_info['keyword'])


@routes.get('/api/qianqian/song/{song_id}')
async def get_song_from_qianqian(request: web.Request):
    return await get_song(baidu.BaiDu(), request.match_info['song_id'])


@routes.get('/api/qianqian/artist/{artist_id}')
async def get_artist_from_qianqian(request: web.Request):
    return await get_artist(baidu.BaiDu(), request.match_info['artist_id'])


@routes.get('/api/qianqian/album/{album_id}')
async def get_album_from_qianqian(request: web.Request):
    return await get_album(baidu.BaiDu(), request.match_info['album_id'])


@routes.get('/api/qianqian/playlist/{playlist_id}')
async def get_playlist_from_qianqian(request: web.Request):
    return await get_playlist(baidu.BaiDu(), request.match_info['playlist_id'])


async def init():
    app = web.Application()
    app.add_routes(routes)
    return app


def run(port: int = None, debug: bool = False):
    app = init()
    if debug:
        web.run_app(app, port=port)
    else:
        web.run_app(app, port=port, access_log=None)


if __name__ == '__main__':
    run(debug=True)
