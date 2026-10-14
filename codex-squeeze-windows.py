#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Windows 专用在线入口；主程序只读入内存，不保存源码文件。"""
import os
import shutil
import subprocess
import sys

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
    try:
        result = subprocess.run(
            [curl, "-q", "-fsSL", "--connect-timeout", "10", "--max-time", "30", CORE_URL],
            capture_output=True,
            check=True,
            timeout=35,
        )
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or b"").decode("utf-8", "replace").strip()
        if exc.returncode == 60:
            raise SystemExit(
                "Windows curl 也无法验证 GitHub 的 HTTPS 证书。"
                "请检查系统时间、Windows 根证书及代理/安全软件的证书配置。\n" + detail
            )
        raise SystemExit("无法从 GitHub 读取主程序，请检查网络：\n" + detail)
    except subprocess.TimeoutExpired:
        raise SystemExit("从 GitHub 读取主程序超时，请检查网络后重试。")
    except OSError as exc:
        raise SystemExit("无法启动 curl：%s" % exc)
    return result.stdout


def main():
    if sys.platform != "win32":
        raise SystemExit("这是 Windows 入口；Mac 请使用 codex-squeeze-macos.py。")
    if sys.version_info < (3, 7):
        raise SystemExit("请先安装 Python 3.7 或更高版本。")
    curl = find_curl()
    if not curl:
        raise SystemExit("没有找到 curl.exe。请安装 curl 并加入 PATH 后重试。")
    source = fetch_core(curl)
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
