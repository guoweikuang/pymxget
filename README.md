# pymxget

**[mxget](https://github.com/winterssy/mxget)** 的Python实现，优雅地下载你喜欢的音乐。

[![Actions Status](https://github.com/winterssy/pymxget/workflows/Publish%20Docker/badge.svg)](https://github.com/winterssy/pymxget/actions) [![Python Version](https://img.shields.io/pypi/pyversions/mxget.svg)](https://github.com/winterssy/pymxget) [![License](https://img.shields.io/github/license/winterssy/pymxget.svg)](LICENSE)

## 功能特性

- [网易云音乐](https://music.163.com) / [QQ音乐](https://y.qq.com) / [咪咕音乐](http://music.migu.cn/v3) / [酷狗音乐](http://www.kugou.com) / [酷我音乐](http://www.kuwo.cn/) 一站式音乐搜索和下载。
- 单曲、专辑、歌单以及歌手热门歌曲，只需一步，就能搞定！
- 支持自动嵌入音乐标签/下载歌词。
- 利用协程实现快速并发下载。
- 支持库调用和RESTful API。

## 下载安装

```sh
$ pip3 install -U mxget
```

> `mxget` 要求Python版本不低于 `3.5.3` 。

## 使用说明

> `mxget` 并不是为破解音乐平台的数字版权限制而生的，仅提供试听版音质下载，如果你喜欢高音质/无损资源，请支持正版。

### 作为CLI使用

这是 `mxget` 的基础功能，你可以通过终端调用 `mxget` 实现音乐搜索、下载功能。以网易云音乐为例，

- 搜索歌曲

```sh
$ mxget search --from nc -k Faded
```

>如果你的搜索关键词包含空格，请用双引号 `""` 包围起来。

- 下载歌曲

```sh
$ mxget song --from nc --id 36990266
```

- 下载专辑

```sh
$ mxget album --from nc --id 3406843
```

- 下载歌单

```sh
$ mxget playlist --from nc --id 156934569
```

- 下载歌手热门歌曲

```sh
$ mxget artist --from nc --id 1045123
```

- 自动更新音乐标签/下载歌词

如果你希望 `mxget` 为你自动更新音乐标签，可使用 `--tag` 指令，如：

```sh
$ mxget song --from nc --id 36990266 --tag
```

当使用 `--tag` 指令时，`mxget` 会同时将歌词内嵌到音乐文件中，一般而言你无须再额外下载歌词。如果你确实需要 `.lrc` 格式的歌词文件，可使用 `--lyric` 指令，如：

```sh
$ mxget song --from nc --id 36990266 --lyric
```

- 设置默认下载目录

默认情况下，`mxget` 会下载音乐到当前目录下的 `downloads` 文件夹，如果你想要更改此行为，可以这样做：

```sh
$ mxget config --cwd [directory]
```

>  `directory` 必须为绝对路径。

- 设置默认音乐平台

`mxget` 默认使用的音乐平台为网易云音乐，你可以通过以下命令更改：

```sh
$ mxget config --from qq
```

这样，如果你不通过 `--from` 指令指定音乐平台，`mxget` 便会使用默认值。

在上述命令中，你会经常用到 `--from` 以及 `--id` 这两个指令，它们分别表示音乐平台标识和音乐id。`mxget` 使用的平台标识如下：

|  音乐平台  |     音乐标识     | 识别码 |
| :--------: | :--------------: | :----: |
| 网易云音乐 | `netease` / `nc` |  1000  |
|   QQ音乐   |       `qq`       |  1001  |
|  咪咕音乐  |  `migu` / `mg`   |  1002  |
|  酷狗音乐  |  `kugou` / `kg`  |  1003  |
|  酷我音乐  |  `kuwo` / `kw`   |  1004  |

音乐id为音乐平台为对应资源分配的唯一id，当使用 `mxget` 进行搜索时，歌曲id会显示在每条结果的后面。你也可以通过各大音乐平台的网页版在线搜索相关资源，然后从结果详情页的URL中获取其音乐id。值得注意的是，酷狗音乐对应的歌曲id即为文件哈希 `hash` 。

- 多任务下载

`mxget` 支持多任务快速并发下载，你可以通过 `--limit` 参数指定同时下载的任务数，如不指定默认为CPU核心数。

```sh
$ mxget playlist --from nc --id 156934569 --limit 16
```

> 尽管 `mxget` 允许设置的最高并发数是32，但使用时建议不要超过16，请根据网络状况适当调整。

### 作为库调用

`mxget` 封装了一些便捷的API，Python开发者可以直接调用，举个例子：

```python
import asyncio

from mxget.provider import netease


def main():
    loop = asyncio.get_event_loop()
    resp = loop.run_until_complete(netease.get_song('36990266'))
    print(resp)


if __name__ == '__main__':
    main()
```

### 作为API服务部署

`mxget` 提供了简易的RESTful API，允许你基于其开发web应用。启动服务：

```sh
$ mxget serve
```

Docker版：

```sh
$ docker pull winterssy/pymxget
$ docker run -d --name mxget -p 8080:8080 winterssy/pymxget
```

请求方法均为 `GET` ，统一调用路径为 `/api/{platform}/{type}/{param}` ，示例：

- 从QQ音乐获取 `周杰伦` 的搜索结果

```sh
$ curl -X GET "http://127.0.0.1:8080/api/qq/search/周杰伦" -H "accept: application/json"
```

- 从网易云音乐获取id为 `36990266` 的歌曲资源

```sh
$ curl -X GET "http://127.0.0.1:8080/api/netease/song/36990266" -H "accept: application/json"
```

- 从咪咕音乐获取id为 `1121438701` 的专辑资源

```sh
$ curl -X GET "http://127.0.0.1:8080/api/migu/album/1121438701" -H "accept: application/json"
```

- 从酷狗音乐获取id为 `547134` 的歌单资源

```sh
$ curl -X GET "http://127.0.0.1:8080/api/kugou/playlist/547134" -H "accept: application/json"
```

- 从酷我音乐获取id为 `336` 的歌手资源

```sh
$ curl -X GET "http://127.0.0.1:8080/api/kuwo/artist/336" -H "accept: application/json"
```

**注：** 由于音乐平台的限制，`mxget` 的API服务仅在本地测试通过。如果你将 `mxget` 部署到公网，特别是海外VPS上，开发者不保证能工作，遇到的问题需要你自行解决。

## FAQ

- 抓取（Fetch）歌单数据耗时较长？

> `mxget` 会将音乐标签、歌词等内容聚合之后才返回数据，耗时时长跟歌单歌曲数成正比。

- 为什么部分音乐不支持下载？

> API请求本身没有返回相应数据，原因可能是音乐平台的版权限制，这不是开发者能够解决的，请尝试更换音乐平台。

- 下载MV？

> 经过调研，`mxget` 已明确不支持下载MV。

## 免责声明

- 本项目仅供学习研究使用，禁止商业用途。
- 本项目使用的接口如无特别说明均为官方接口，音乐版权归源音乐平台所有，侵删。

## License

GPLv3。