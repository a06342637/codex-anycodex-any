# Windows 使用说明

专用文件：`codex-squeeze-windows.py`。Mac 请看 [Mac 使用说明](README.macos.md)。

## 在线启动

打开 CMD 或 PowerShell，粘贴整行：

```powershell
python -X utf8 -c "import urllib.request;u='https://raw.githubusercontent.com/a06342637/codex-anycodex-any/main/codex-squeeze-windows.py';exec(compile(urllib.request.urlopen(u,timeout=30).read(),u,'exec'))"
```

使用 Python 启动器的电脑也可以运行：

```powershell
py -3 -X utf8 -c "import urllib.request;u='https://raw.githubusercontent.com/a06342637/codex-anycodex-any/main/codex-squeeze-windows.py';exec(compile(urllib.request.urlopen(u,timeout=30).read(),u,'exec'))"
```

任选一条。程序源文件只读取到内存，不会保存到当前文件夹，也不需要安装第三方 Python 包。

## 要求与使用

- 已安装 Python 3.7+、curl，以及可用并已登录的 Codex。
- 脚本会查找 PATH、常见 npm 全局安装位置和部分 Windows Codex 桌面端路径。
- 网络能访问 `raw.githubusercontent.com`、Telegram API 和 Codex 所需服务。
- 首次使用按提示输入 Telegram bot token 和 chat_id，再选择会话；已有配置自动复用。
- 保持终端运行，按 `Ctrl+C` 停止。程序运行在本机，GitHub 不承担计算。

配置文件为 `%USERPROFILE%\.codex-squeeze.json`，日志为 `%USERPROFILE%\.codex-squeeze.log`。配置包含 Telegram token，不要上传到 GitHub。

## 无法启动时

| 现象 | 处理 |
| --- | --- |
| `python` 不是命令，或弹出 Microsoft Store | 尝试 `py -3` 命令；两者都不可用时，需要先安装 Python 3。 |
| `urlopen` 超时或无法读取主程序 | 确认网络能访问 GitHub 原始文件域名 `raw.githubusercontent.com`，再重试。 |
| 没有找到 Codex | 安装并登录 Codex CLI，确认终端能运行 `codex`。 |
| Telegram 校验失败 | 检查 token、chat_id 和 Telegram API 网络连接。 |
| 会话被桌面端占用 | 按脚本提示释放该会话的写锁，再重试。 |

程序会持续向所选会话发送「在」，可能消耗 Codex 用量；重试不保证能消除服务拥堵或账户限制。
