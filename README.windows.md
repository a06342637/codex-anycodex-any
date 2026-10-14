# Windows 使用说明

专用文件：`codex-squeeze-windows.py`。Mac 请看 [Mac 使用说明](README.macos.md)。

## 在线启动

打开 CMD 或 PowerShell，粘贴整行：

```powershell
python -X utf8 -c "import os,subprocess;u='https://raw.githubusercontent.com/a06342637/codex-anycodex-any/main/codex-squeeze-windows.py';c=os.path.join(os.environ['SystemRoot'],'System32','curl.exe');exec(compile(subprocess.check_output([c,'-q','-fsSL','--connect-timeout','10','--max-time','30',u],timeout=35),u,'exec'))"
```

使用 Python 启动器的电脑也可以运行：

```powershell
py -3 -X utf8 -c "import os,subprocess;u='https://raw.githubusercontent.com/a06342637/codex-anycodex-any/main/codex-squeeze-windows.py';c=os.path.join(os.environ['SystemRoot'],'System32','curl.exe');exec(compile(subprocess.check_output([c,'-q','-fsSL','--connect-timeout','10','--max-time','30',u],timeout=35),u,'exec'))"
```

任选一条。程序源文件只读取到内存，不会保存到当前文件夹，也不需要安装第三方 Python 包。

Windows 命令使用系统自带的 `curl.exe` 读取入口，入口也优先使用系统 curl 读取主程序；系统 curl 通常通过 Schannel 使用 Windows 证书库。两个步骤均保留 HTTPS 证书验证，不使用 Python `urllib` 获取代码，也不关闭证书校验。

如果此前的命令报 `CERTIFICATE_VERIFY_FAILED: unable to get local issuer certificate`，说明 Python 在读取 GitHub 入口时无法构建可信证书链，程序尚未启动。可能与本机证书链或代理/安全软件的证书有关，不能仅凭这个报错确定是哪一种。请重新复制本页的新命令；只更新仓库里的入口文件无法修复旧命令在读取入口之前发生的错误。

## 要求与使用

- 已安装 Python 3.7+、可用并已登录的 Codex，并有 Windows 系统自带的 `%SystemRoot%\System32\curl.exe`。
- 脚本会查找 PATH、常见 npm 全局安装位置和部分 Windows Codex 桌面端路径。
- 网络能访问 `raw.githubusercontent.com`、Telegram API 和 Codex 所需服务。
- 首次使用按提示输入 Telegram bot token 和 chat_id，再选择会话；已有配置自动复用。
- 保持终端运行，按 `Ctrl+C` 停止。程序运行在本机，GitHub 不承担计算。

配置文件为 `%USERPROFILE%\.codex-squeeze.json`，日志为 `%USERPROFILE%\.codex-squeeze.log`。配置包含 Telegram token，不要上传到 GitHub。

## 无法启动时

| 现象 | 处理 |
| --- | --- |
| `python` 不是命令，或弹出 Microsoft Store | 尝试 `py -3` 命令；两者都不可用时，需要先安装 Python 3。 |
| 旧命令报 `CERTIFICATE_VERIFY_FAILED` | 改用本页通过系统 curl 读取脚本的新命令。 |
| 新命令报 `curl: (60)` 或证书链错误 | 系统 curl 同样不信任该连接。检查系统时间、Windows 根证书更新及代理/安全软件证书配置；此时仅更换启动命令无法解决。 |
| curl 超时或无法读取主程序 | 确认网络能访问 GitHub 原始文件域名 `raw.githubusercontent.com`，并检查代理设置后重试。 |
| 找不到系统 `curl.exe` | 当前系统缺少命令要求的 curl，需要先修复或安装该运行依赖。 |
| 没有找到 Codex | 安装并登录 Codex CLI，确认终端能运行 `codex`。 |
| Telegram 校验失败 | 检查 token、chat_id 和 Telegram API 网络连接。 |
| 会话被桌面端占用 | 按脚本提示释放该会话的写锁，再重试。 |

程序会持续向所选会话发送「在」，可能消耗 Codex 用量；重试不保证能消除服务拥堵或账户限制。
