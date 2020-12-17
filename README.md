# StudentDB Bot

(WIP) StudentDB 的 Telegram 查询界面

## 关于

StudentDB Bot 以一个 [Telegram Bot](https://core.telegram.org/bots) 的形式实现了 StudentDB 的查询功能，用户可以在使用 Telegram 时方便快捷地从
StudentDB 查询信息。

### 技术栈

- 使用 [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) 制成。**It's a really awesome
  wrapper!**

- 以 [GitHub App](https://docs.github.com/developers/apps) 的形式访问 GitHub API，来查询 StudentDB 在 GitHub 上的存储库。

- 使用 [Algolia](http://algolia.com/) 作为搜索引擎，实现高性能高精度搜索。

## 安装和使用

### 软件需求

- 一个不错的网络连接，能快速访问 [github.com](https://github.com/) 和 [api.telegram.org](https://api.telegram.org/) 。

- 至少 3.8 版本的 [Python](https://www.python.org/) ，3.9 更佳。

- **不一定** 要能被公网访问。如果有，可以运行 Webhook 模式。

### 安装步骤

```bash
# 1. 下载代码
$ git clone https://github.com/ScoreDB/StudentDB_bot.git
$ cd StudentDB_bot

# 2.（可选）创建虚拟环境
$ virtualenv venv
$ source ./venv/bin/activate

# 3. 安装依赖
(venv) $ pip install -r requirements.txt

# 4. 复制并编辑配置文件（见下方）
(venv) $ cp .env.example .env
(venv) $ nano .env  # Or any other editor

# 5. 将 GitHub App 的私钥文件放入 `keys`（见下方）
(venv) $ cp ~/my-key.pem keys/private-key.pem

# 6. 运行程序
(venv) $ python run.py --help
```

### 配置

如上面第 `4` 步所示，复制一份 `.env.example` 到 `.env` 并按照其中注释的说明编辑。

如上面第 `5` 步所示，将 GitHub App 的私钥文件复制到 `keys` 目录中。

### 用法

```bash
(venv) $ python run.py --help
usage: run.py [-h] [-u] [-w] [--debug]

optional arguments:
  -h, --help     show this help message and exit
  -u, --update   update the data and exit
  -w, --webhook  run in webhook mode
  --debug        enable debug mode
```

### Debug 模式

Debug 模式下会输出更多 log 信息。

可以通过命令行传入 `--debug` 或者设置环境变量 `DEBUG=TRUE` 来开启 Debug 模式。

### 网络代理

StudentDB Bot 使用 [`requests`](https://requests.readthedocs.io/) 库发送 HTTP 请求，所以会遵照 `HTTP_PROXY` 和 `HTTPS_PROXY`
环境变量使用代理。要使用代理，可以在命令行或 `.env` 文件中设置上述环境变量。
