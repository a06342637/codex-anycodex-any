# Mac（macOS）使用说明

专用文件：`codex-squeeze-macos.py`。Windows 请看 [Windows 使用说明](README.windows.md)。

## 在线启动

打开系统的「终端 / Terminal」，粘贴整行（zsh 或 bash 均可）：

```sh
python3 -X utf8 -c "import urllib.request,time;u='https://raw.githubusercontent.com/a06342637/codex-anycodex-any/main/codex-squeeze-macos.py?t='+str(int(time.time()));exec(compile(urllib.request.urlopen(u,timeout=30).read(),u,'exec'))"
```

程序入口和主程序都从 GitHub 读入内存，无需手动下载或保存 `.py` / `.command` 文件，也不需要安装第三方 Python 包。命令里的 `?t=时间戳` 参数会强制读取最新版本（绕开缓存）；启动时会显示主程序版本号。

## 要求与使用

- 需要 Python 3.7+、可用并已登录的 Codex，以及 curl。可以先运行 `python3 --version` 和 `curl --version` 检查。
- **Mac 不保证预装可用的 Python 3。** 如果 `python3` 不存在，或系统提示安装开发者工具，先安装可用的 Python 3，再运行启动命令。
- Intel 和 Apple Silicon 使用相同命令；Python 和 Codex 本身需能在该电脑上运行。
- 优先使用 PATH 中的 `codex`；找不到时尝试 `~/.local/bin`、`/opt/homebrew/bin`、`/usr/local/bin`，以及 `/Applications/Codex.app/Contents/Resources/codex` 和用户 Applications 下的对应路径。桌面端路径不存在时，仍需要可用的 Codex CLI。
- 网络需能访问 `raw.githubusercontent.com`、Telegram API 和 Codex 所需服务。
- 首次按提示输入 Telegram bot token、chat_id，再选择会话；已有配置自动复用。

配置保存在 `~/.codex-squeeze.json`，日志保存在 `~/.codex-squeeze.log`。配置含 Telegram token，请勿上传到 GitHub。

程序在你的 Mac 上运行，需要保持电脑开机、终端运行及网络连接。按 `Control+C` 停止。睡眠或关闭终端后，不能指望脚本继续运行。

## 无法启动时

| 现象 | 处理 |
| --- | --- |
| `command not found: python3` | 先安装 Python 3，再重新打开终端。 |
| 提示这是 Windows 入口 | 使用本页的 Mac 命令，地址应以 `codex-squeeze-macos.py` 结尾。 |
| 没有找到 Codex | 安装并登录 Codex CLI，确保终端能运行 `codex`，再启动。 |
| `urlopen` 超时或读取失败 | 检查访问 `raw.githubusercontent.com` 的网络连接。 |
| `CERTIFICATE_VERIFY_FAILED` | 检查系统时间及 Python 的 CA 证书；若使用 python.org 安装包，可运行其附带的 `Install Certificates.command`。 |
| Telegram 校验失败 | 检查 token、chat_id，以及能否连接 Telegram API。 |
| 会话被桌面端占用 | 按脚本提示释放该会话的写锁，再重试。 |

程序会持续向所选会话发送「在」，可能消耗 Codex 用量；重试不保证能消除服务拥堵或账户限制。

验证范围：已在 Windows 环境检查 Mac 入口的语法、依赖判断、Codex 路径选择和网络失败处理；尚未在 Mac 实机验证完整会话运行。
