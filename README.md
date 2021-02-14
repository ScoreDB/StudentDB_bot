# ScoreDB Telegram Bot

ScoreDB v3 的 Telegram 查询 Bot

## 关于

一个 [Telegram Bot](https://core.telegram.org/bots) 形式实现的 ScoreDB 的查询功能，用户可以在使用 Telegram 时方便快捷地从 ScoreDB 查询信息。

本 bot 使用 [`python-telegram-bot`](https://github.com/python-telegram-bot/python-telegram-bot) 制成。**It's a really awesome
wrapper!**

## 安装和使用

### 软件需求

- 一个不错的网络连接，能快速访问 [Telegram API](https://api.telegram.org/)

- 3.9 版本的 [Python](https://www.python.org/)

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

# 4. 复制并填写配置文件
(venv) $ cp .env.example .env
(venv) $ nano .env  # Or any other editor

# 5. 运行程序
(venv) $ python run.py
```

### Debug 模式

Debug 模式下会输出更多 log 信息。

可以通过设置环境变量 `DEBUG=TRUE` 来开启 Debug 模式。

### 网络代理

我们使用 [`requests`](https://requests.readthedocs.io/) 库发送 HTTP 请求，所以会遵照 `HTTP_PROXY` 和 `HTTPS_PROXY`
环境变量使用代理。要使用代理，可以在命令行或 `.env` 文件中设置上述环境变量。
