#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""macOS 专用在线入口；支持 Intel 和 Apple Silicon 的常见安装目录。"""
import os
import shutil
import sys
import urllib.request

CORE_URL = "https://raw.githubusercontent.com/a06342637/codex-anycodex-any/main/codex-squeeze.py"


def find_codex():
    codex = shutil.which("codex")
    if codex:
        return codex
    candidates = (
        "~/.local/bin/codex",
        "/opt/homebrew/bin/codex",
        "/usr/local/bin/codex",
        "/Applications/Codex.app/Contents/Resources/codex",
        "~/Applications/Codex.app/Contents/Resources/codex",
    )
    for candidate in candidates:
        path = os.path.expanduser(candidate)
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    return None


def main():
    if sys.platform != "darwin":
        raise SystemExit("这是 Mac 入口；Windows 请使用 codex-squeeze-windows.py。")
    if sys.version_info < (3, 7):
        raise SystemExit("请先安装 Python 3.7 或更高版本，并确保 python3 命令可用。")
    if not shutil.which("curl"):
        raise SystemExit("没有找到 curl。请确认 /usr/bin 在 PATH 中，或安装 curl。")
    codex = find_codex()
    if not codex:
        raise SystemExit("没有找到 Codex。请安装并登录 Codex CLI，确保终端能运行 codex。")
    try:
        with urllib.request.urlopen(CORE_URL, timeout=30) as response:
            source = response.read()
    except (OSError, ValueError) as exc:
        raise SystemExit("无法从 GitHub 读取主程序，请检查网络：%s" % exc)
    namespace = {"__name__": "codex_squeeze_core", "__file__": CORE_URL}
    exec(compile(source, CORE_URL, "exec"), namespace)
    namespace["CODEX"] = codex
    namespace["main"]()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n已停止。")
