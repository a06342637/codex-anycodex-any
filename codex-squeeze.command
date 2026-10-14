#!/bin/bash
# 双击运行：盯 codex 会话 + 自动挤（上游拥堵失败自动重发「在」，TG 通知）
DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$DIR/codex-squeeze.py" ]; then
  PYFILE="$DIR/codex-squeeze.py"
else
  PYFILE="$HOME/.local/bin/codex-squeeze.py"
fi
echo "启动中…（关闭这个窗口 = 结束自动挤）"
exec /usr/bin/env python3 "$PYFILE" "$@"
