# codex-anycodex-any

`codex-squeeze`：通过本机 Codex CLI 重试会话、定时发送「在」，并通过 Telegram 通知和控制。

Windows 和 Mac 使用**不同的入口文件和命令**。按自己的系统选择即可，不用下载压缩包、克隆仓库或保存脚本。

## Windows

专用入口：[codex-squeeze-windows.py](codex-squeeze-windows.py) · [Windows 详细说明](README.windows.md)

打开 **CMD 或 PowerShell**，复制整行运行：

```powershell
python -X utf8 -c "import os,subprocess;u='https://raw.githubusercontent.com/a06342637/codex-anycodex-any/main/codex-squeeze-windows.py';c=os.path.join(os.environ['SystemRoot'],'System32','curl.exe');exec(compile(subprocess.check_output([c,'-q','-fsSL','--connect-timeout','10','--max-time','30',u],timeout=35),u,'exec'))"
```

如果 `python` 不可用，但安装了 Python 启动器，把开头的 `python` 换成 `py -3`。

Windows 使用系统自带的 `curl.exe` 获取代码，保留 HTTPS 证书校验，避免依赖 Python 的证书验证环境。旧命令若报 `CERTIFICATE_VERIFY_FAILED`，请重新复制上面的新命令。

## Mac（macOS）

专用入口：[codex-squeeze-macos.py](codex-squeeze-macos.py) · [Mac 详细说明](README.macos.md)

打开 **终端 Terminal**，复制整行运行（系统默认 zsh 或 bash 均可）：

```sh
python3 -X utf8 -c "import urllib.request;u='https://raw.githubusercontent.com/a06342637/codex-anycodex-any/main/codex-squeeze-macos.py';exec(compile(urllib.request.urlopen(u,timeout=30).read(),u,'exec'))"
```

需要本机已有 Python 3.7+、可用并已登录的 Codex，以及 curl。Mac 不保证预装 Python；如果提示找不到 `python3`，需先安装 Python 3。

## 运行方式

两个专用入口分别检查对应系统的依赖，然后从 GitHub 读取同一份 `codex-squeeze.py` 主程序。入口和主程序都在内存中执行；每次启动读取 `main` 分支当前版本。

**GitHub 只保存代码，程序在你的电脑上运行。** 运行期间需要保持电脑开机、终端运行和网络连接。按 `Ctrl+C` 停止。

首次运行需要按提示配置 Telegram bot token、chat_id，再选择会话；已有配置会自动复用。程序会向所选会话发送「在」，并在一轮完成后隔 60 秒继续发送，可能消耗 Codex 用量。能否成功取决于服务可用性和账户状态。

配置和日志仍保存在本机用户目录的 `.codex-squeeze.json` 和 `.codex-squeeze.log` 中。配置含 Telegram token，请勿上传。无需保存源文件不代表完全不写本地数据。

原有 `codex-squeeze.bat` 和 `codex-squeeze.command` 是配合本地 `codex-squeeze.py` 使用的启动器；在线运行请使用上面各系统的专用命令。
