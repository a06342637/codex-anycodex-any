#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Windows 专用在线入口；主程序只读入内存，不保存源码文件。
每次启动都强制读取 GitHub 最新版（URL 带 ?t= 时间戳，绕开 CDN 缓存）。"""
import os
import re
import shutil
import subprocess
import sys
import time

CORE_URL = "https://raw.githubusercontent.com/a06342637/codex-anycodex-any/main/codex-squeeze.py"


def find_curl():
    """优先使用 Windows 自带的 curl（Schannel / Windows 证书库）。"""
    system_curl = os.path.join(
        os.environ.get("SystemRoot", r"C:\Windows"), "System32", "curl.exe"
    )
    if os.path.isfile(system_curl):
        return system_curl
    return shutil.which("curl.exe")


def fetch_core(curl):
    url = CORE_URL + "?t=" + str(int(time.time()))   # 绕开缓存，始终取最新
    try:
        result = subprocess.run(
            [curl, "-q", "-fsSL", "--connect-timeout", "10", "--max-time", "30", url],
            capture_output=True,
            check=True,
            timeout=35,
        )
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or b"").decode("utf-8", "replace").strip()
        if exc.returncode == 60:
            raise SystemExit(
                "ERROR: Windows curl could not verify the GitHub HTTPS certificate.\n"
                "Windows curl 也无法验证 GitHub 的 HTTPS 证书。"
                "请检查系统时间、Windows 根证书及代理/安全软件的证书配置。\n" + detail
            )
        raise SystemExit("ERROR: Failed to fetch the program from GitHub.\n无法从 GitHub 读取主程序，请检查网络：\n" + detail)
    except subprocess.TimeoutExpired:
        raise SystemExit("ERROR: GitHub download timed out.\n从 GitHub 读取主程序超时，请检查网络后重试。")
    except OSError as exc:
        raise SystemExit("ERROR: Could not start curl.\n无法启动 curl：%s" % exc)
    return result.stdout


def core_version(source):
    try:
        m = re.search(r"（v(\d+(?:\.\d+)*)", source.decode("utf-8", "replace"))
        return m.group(1) if m else "?"
    except Exception:
        return "?"


def main():
    if sys.platform != "win32":
        raise SystemExit("ERROR: Windows launcher only. On macOS use codex-squeeze-macos.py.\n这是 Windows 入口；Mac 请使用 codex-squeeze-macos.py。")
    if sys.version_info < (3, 7):
        raise SystemExit("ERROR: Python 3.7 or newer is required.\n请先安装 Python 3.7 或更高版本。")
    curl = find_curl()
    if not curl:
        raise SystemExit("ERROR: curl.exe was not found on PATH.\n没有找到 curl.exe。请安装 curl 并加入 PATH 后重试。")
    source = fetch_core(curl)
    ver = core_version(source)
    print("codex-squeeze core v%s (fetched latest from GitHub)\ncodex-squeeze 主程序 v%s（已读取 GitHub 最新版）" % (ver, ver))
    namespace = {"__name__": "codex_squeeze_core", "__file__": CORE_URL}
    exec(compile(source, CORE_URL, "exec"), namespace)
    if not namespace.get("CODEX"):
        raise SystemExit(
            "ERROR: Codex CLI was not found. Install it or add it to PATH.\n"
            "Check in this terminal: where.exe codex\n"
            "没有找到 Codex。请安装并登录 Codex CLI，确保它在 PATH 中。"
        )
    namespace["main"]()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n已停止。")
