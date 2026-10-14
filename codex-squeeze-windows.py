#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Windows 专用在线入口；主程序只读入内存，不保存源码文件。"""
import shutil
import sys
import urllib.request

CORE_URL = "https://raw.githubusercontent.com/a06342637/codex-anycodex-any/main/codex-squeeze.py"


def main():
    if sys.platform != "win32":
        raise SystemExit("这是 Windows 入口；Mac 请使用 codex-squeeze-macos.py。")
    if sys.version_info < (3, 7):
        raise SystemExit("请先安装 Python 3.7 或更高版本。")
    if not shutil.which("curl"):
        raise SystemExit("没有找到 curl。请安装 curl 并加入 PATH 后重试。")
    try:
        with urllib.request.urlopen(CORE_URL, timeout=30) as response:
            source = response.read()
    except (OSError, ValueError) as exc:
        raise SystemExit("无法从 GitHub 读取主程序，请检查网络：%s" % exc)
    namespace = {"__name__": "codex_squeeze_core", "__file__": CORE_URL}
    exec(compile(source, CORE_URL, "exec"), namespace)
    if not namespace.get("CODEX"):
        raise SystemExit("没有找到 Codex。请安装并登录 Codex CLI，确保它在 PATH 中。")
    namespace["main"]()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n已停止。")
