# codex-anycodex-any

存放 `codex-squeeze`：通过本机 Codex CLI 重试会话、定时发送「在」，并通过 Telegram 通知和控制。

## Windows 一条命令启动

在 **CMD 或 PowerShell** 中粘贴下面整行，按回车：

```powershell
python -X utf8 -c "import urllib.request;u='https://raw.githubusercontent.com/a06342637/codex-anycodex-any/main/codex-squeeze.py';exec(compile(urllib.request.urlopen(u,timeout=30).read(),u,'exec'))"
```

如果电脑使用 Python 启动器，把开头的 `python` 换成 `py -3`：

```powershell
py -3 -X utf8 -c "import urllib.request;u='https://raw.githubusercontent.com/a06342637/codex-anycodex-any/main/codex-squeeze.py';exec(compile(urllib.request.urlopen(u,timeout=30).read(),u,'exec'))"
```

这两条命令任选一条。每次启动都会读取仓库 `main` 分支上的当前脚本，无需克隆仓库、下载压缩包或保存 `.py` 文件，也不需要安装第三方 Python 包。

**这是从网络读取代码，在你的电脑上运行。GitHub 提供代码存储，不承担程序运行。** 脚本运行期间需要保持电脑开机、终端运行和网络连接。按 `Ctrl+C` 停止。

## 本机要求与首次使用

- 已安装 Python 3；上面的命令使用 UTF-8 模式，需要 Python 3.7 或更高版本。
- 已安装并登录可用的 Codex CLI。脚本也会尝试查找部分 Codex 桌面端安装路径和 npm 全局安装路径。
- 系统能调用 `curl`，且能连接 `raw.githubusercontent.com`、Telegram API 和 Codex 所需服务。
- 首次运行按提示输入 Telegram bot token 和 chat_id，然后选择要操作的会话；已有配置会自动复用。

程序会向所选会话发送消息，并在完成一轮后每隔 60 秒继续发送「在」，可能消耗 Codex 用量。重试能否成功取决于服务可用性和账户状态，上传到 GitHub 不会消除服务拥堵或额度限制。

原程序仍会在 Windows 用户目录下保存以下文件：

- `%USERPROFILE%\.codex-squeeze.json`：Telegram 配置，包含 bot token。
- `%USERPROFILE%\.codex-squeeze.log`：运行日志。

因此，“不用下载文件”指不用手动下载或保存程序源文件；并不意味着运行时完全不写本地数据。配置、日志和 Codex 登录信息不属于本仓库的上传内容。

## 常见问题

| 现象 | 原因和处理 |
| --- | --- |
| `python` 不是命令，或弹出 Microsoft Store | 尝试上面的 `py -3` 命令。两者都不可用时，需要先安装 Python 3；纯 Python 脚本无法在没有 Python 运行环境的电脑上直接执行。 |
| `urlopen` 超时或连接失败 | 当前网络无法连接 GitHub 原始文件域名。先确认能访问 `raw.githubusercontent.com`，再重试。 |
| 提示没有找到 `codex` 命令 | 本机需要可用的 Codex CLI，或脚本能够识别的桌面端安装路径。 |
| Telegram 校验失败 | 检查 token、chat_id，以及电脑是否能连接 Telegram API。 |
| 提示会话被桌面端占用 | 需要释放该会话的写锁，脚本才有机会继续操作；具体提示由原脚本给出。 |

## 文件

- `codex-squeeze.py`：原始主程序。
- `codex-squeeze.bat`：下载到本地后使用的 Windows 启动器。
- `codex-squeeze.command`：下载到本地后使用的 macOS 启动器。

三个程序文件按原样上传。在线启动使用上面的一行 Python 命令，不需要使用 `.bat` 或 `.command` 文件。
