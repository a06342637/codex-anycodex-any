#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
codex-squeeze —— codex 会话自动挤 + 保持会话 + Telegram 通知（v2.1，跨平台 mac/Win）

用法：
    python3 codex-squeeze.py        # Windows：双击 codex-squeeze.bat
（无需参数；脚本自己扫描会话让你选一个）

· 首次运行：向导要你粘贴 TG bot token 和 chat_id（各自当场验证，只问一次）
· 每次运行：扫描会话选一个（也可以输 0/n 新建一个会话来挤）→ 开始服务它
· TG 消息下面有「⏸ 停止挤会话 / ▶️ 继续挤会话」按钮；继续时可以在 TG 里选会话或新建会话
· 每次没挤进去 TG 都会报「❌ 第 N 次：没挤进去…」；挤上和跑完也带第几次
· 上游拥堵失败（Reconnecting 5/5 之后报 high demand）→ 立刻重试，一直挤到进去为止
· 挤进去后：跑完一轮隔 60 秒再发一次「在」，保持会话（例行的心跳不打扰 TG）
· 打回后重新挤进去 → 马上 TG 通知；该轮跑完 → TG 通知
· 会话被 Codex 桌面端占用（写锁）时 → TG 提醒关掉桌面端那个会话，脚本自动继续重试
· 系统通知一律不用，全走 Telegram（手机能看到）

依赖：机器上有 Python 3、codex 和 curl；macOS 不保证预装可用的 python3。
Windows 上 PATH 里没有 codex 时，自动使用 npm 全局安装或 Codex 桌面端自带的 codex.exe。
"""
import os
import sys
import json
import time
import queue
import threading
import subprocess
import shutil as _shutil

IS_WIN = (os.name == "nt")

# ───────────────────────── codex 定位 ─────────────────────────
def _npm_native_codex():
    """npm 全局包里 codex-win32-*/vendor/.../bin/codex.exe（绕开 .cmd/node 包装，进程树干净）。"""
    npm = os.path.join(os.environ.get("APPDATA") or "", "npm", "node_modules", "@openai")
    roots = [os.path.join(npm, "codex", "node_modules", "@openai"), npm]
    for root in roots:
        try:
            for d in os.listdir(root):
                if not d.startswith("codex-win32"):
                    continue
                for cur, _dirs, files in os.walk(os.path.join(root, d)):
                    for f in files:
                        if f.lower() == "codex.exe":
                            return os.path.join(cur, f)
        except Exception:
            pass
    return None

def _find_codex():
    for name in ("codex", "codex.cmd", "codex.exe"):
        p = _shutil.which(name)
        if p:
            if p.lower().endswith(".cmd"):
                native = _npm_native_codex()
                if native:
                    return native
            return p
    if IS_WIN:
        base = os.path.join(os.environ.get("LOCALAPPDATA") or "", "OpenAI", "Codex", "bin")
        cands = []
        try:
            for d in os.listdir(base):
                p = os.path.join(base, d, "codex.exe")
                if os.path.exists(p):
                    cands.append(p)
        except Exception:
            pass
        if cands:
            cands.sort(key=lambda p: os.path.getmtime(p), reverse=True)
            return cands[0]
        appdata = os.environ.get("APPDATA") or ""
        p = os.path.join(appdata, "npm", "codex.cmd")
        if appdata and os.path.exists(p):
            return p
    p = os.path.expanduser("~/.local/bin/codex")
    if os.path.exists(p):
        return p
    return None

CODEX = _find_codex()

CONFIG = os.path.expanduser("~/.codex-squeeze.json")
LOGF   = os.path.expanduser("~/.codex-squeeze.log")

SQUEEZE_MSG = "在"      # 发进会话的消息（挤 + 保持会话都用它）
HEARTBEAT_SECS = 60     # 挤进去后，跑完一轮隔多久再发一次「在」保持会话
LOCK_RETRY_SECS = 60    # 会话被桌面端占用时，隔多久重试一次
FALLBACK_IN_SECS = 150  # 一直不报错也不出内容，安静超过这个时间也算挤进去了

def log(msg):
    try:
        with open(LOGF, "a", encoding="utf-8") as f:
            f.write(time.strftime("[%m-%d %H:%M:%S] ") + msg + "\n")
    except Exception:
        pass

# ───────────────────────── 配置与 TG ─────────────────────────
def tg_api(method, timeout_m=20, **params):
    cfg = load_cfg()
    tok = cfg.get("token")
    if not tok:
        return {}
    url = "https://api.telegram.org/bot%s/%s" % (tok, method)
    args = ["curl", "-s", "-m", str(timeout_m), "-X", "POST", url]
    for k, v in params.items():
        args += ["--data-urlencode", "%s=%s" % (k, v)]
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=25)
        return json.loads(r.stdout or "{}")
    except Exception:
        return {}

def tg_send(text, silent=False, kb="default"):
    cfg = load_cfg()
    if not cfg.get("chat"):
        return
    p = {"chat_id": cfg["chat"], "text": text}
    if silent:
        p["disable_notification"] = True
    if kb == "default":
        kb = _kb()
    if kb:
        p["reply_markup"] = kb
    tg_api("sendMessage", **p)

def load_cfg():
    try:
        with open(CONFIG, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_cfg(c):
    with open(CONFIG, "w", encoding="utf-8") as f:
        json.dump(c, f, ensure_ascii=False, indent=1)

def tg_api_raw(tok, method, **params):
    url = "https://api.telegram.org/bot%s/%s" % (tok, method)
    args = ["curl", "-s", "-m", "20", "-X", "POST", url]
    for k, v in params.items():
        args += ["--data-urlencode", "%s=%s" % (k, v)]
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=25)
        return json.loads(r.stdout or "{}")
    except Exception:
        return {}

# ───────────────────────── 首次配置向导（两步，各自验证）─────────────────────────
def wizard():
    print("── 首次配置（只需一次，之后跳过）──")
    while True:
        tok = input("1/2 粘贴你的 Telegram bot token：").strip()
        r = tg_api_raw(tok, "getMe")
        if r.get("ok"):
            print("  ✓ 机器人：@%s" % (r["result"].get("username") or "?"))
            break
        print("  ✗ 校验失败：%s，请重新粘贴" % str(r.get("description") or r)[:80])
    while True:
        chat = input("2/2 粘贴你的 chat_id（和机器人聊天的那个对话 ID）：").strip()
        r = tg_api_raw(tok, "getChat", chat_id=chat)
        if r.get("ok"):
            t = (r["result"] or {}).get("type")
            print("  ✓ 已验证（%s）" % t)
            break
        print("  ✗ 验证失败：%s，请重新粘贴" % str(r.get("description") or r)[:80])
    cfg = {"token": tok, "chat": chat}
    save_cfg(cfg)
    tg_send("✅ codex-squeeze 配置完成，以后失败会自动挤并在这里通知你")
    print("  ✓ 已保存到 %s，以后直接用，不再询问" % CONFIG)
    return cfg

# ───────────────────────── app-server（读会话状态）─────────────────────────
class AppServer:
    """一个常驻的 codex app-server 子进程 + JSON-RPC 客户端（用于读会话状态）。"""

    def __init__(self):
        self._wlock = threading.Lock()
        self.proc = subprocess.Popen(
            [CODEX, "app-server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        self.q = queue.Queue()
        self.reqs = queue.Queue()
        self.pending = []
        self._next_id = 1
        threading.Thread(target=self._pump, daemon=True).start()
        self._request("initialize", {
            "clientInfo": {"name": "codex-squeeze", "version": "2.1.0"}
        })

    def _write(self, payload):
        with self._wlock:
            try:
                self.proc.stdin.write((json.dumps(payload) + "\n").encode())
                self.proc.stdin.flush()
            except Exception as e:
                raise RuntimeError("写入 app-server 失败：%s" % e)

    def _pump(self):
        for line in iter(self.proc.stdout.readline, b""):
            line = line.decode("utf-8", "replace").rstrip()
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if "method" in obj and "id" in obj:
                self.reqs.put(obj)
                continue
            self.q.put(line)

    def _request(self, method, params=None, timeout=30):
        mid = self._next_id
        self._next_id += 1
        payload = {"id": mid, "method": method}
        if params is not None:
            payload["params"] = params
        self._write(payload)

        end = time.time() + timeout
        while time.time() < end:
            try:
                line = self.q.get(timeout=max(0.1, end - time.time()))
            except queue.Empty:
                break
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if obj.get("id") == mid:
                if "error" in obj:
                    raise RuntimeError("%s 失败: %s" % (method, obj["error"]))
                return obj.get("result")
            self.pending.append(obj)
        raise RuntimeError("%s 超时（%ss 无响应）" % (method, timeout))

    def close(self):
        try:
            self.proc.terminate()
        except Exception:
            pass

def latest_turn(api, thread_id):
    res = api._request("thread/turns/list", {"threadId": thread_id, "limit": 1})
    data = (res or {}).get("data") or []
    return data[0] if data else None

# ───────────────────────── 会话扫描 ─────────────────────────
def pick_session(api):
    res = api._request("thread/list", {"limit": 8, "sortKey": "updated_at"})
    rows = (res or {}).get("data") or []
    print("── 会话列表 ──")
    for i, t in enumerate(rows):
        ts = t.get("updatedAt") or 0
        if ts > 1e12:
            ts = ts / 1000.0
        when = time.strftime("%m-%d %H:%M", time.localtime(ts)) if ts else "?"
        name = t.get("name") or ""
        prev = (t.get("preview") or "").replace("\n", " ")[:36]
        print("  %d. %s %s %s" % (i + 1, when, ("【%s】" % name) if name else "", prev))
    print("  0. 🆕 新建一个会话来挤")
    raw = input("选哪个？回车=第 1 个；输序号；或输 0/n 新建会话：").strip()
    if raw == "0" or raw.lower() in ("n", "new", "新建"):
        dflt = (rows[0].get("cwd") if rows else "") or os.path.expanduser("~")
        d = input("新会话放在哪个目录？回车= %s ：" % dflt).strip() or dflt
        print("  正在新建会话…", flush=True)
        tid = new_session(d)
        if not tid:
            print("  ✗ 没拿到新会话 id（可能上游太拥塞），再来一次吧")
            return None, None
        print("  ✓ 新会话建好了：%s" % tid[:8], flush=True)
        return tid, d
    if not raw:
        sel = rows[0] if rows else None
    elif raw.isdigit() and 1 <= int(raw) <= len(rows):
        sel = rows[int(raw) - 1]
    else:
        return raw, None
    if not sel:
        return None, None
    return sel.get("id"), sel.get("cwd")

# ───────────────────────── 挤（codex exec resume 直发）─────────────────────────
_STATUS_CN = {"failed": "失败", "completed": "已完成", "inprogress": "运行中",
              "interrupted": "已中断", "notLoaded": "未加载"}

def _display_line(s):
    """把 exec 输出行整理成要在控制台显示的内容；不需要显示的返回 None。"""
    t = s.strip()
    if not t or t == SQUEEZE_MSG or t == "user" or t == "codex":
        return None
    if t.startswith("warning:") or t.startswith("user (") or "disable_response_storage" in t:
        return None
    if len(t) > 10 and t[:4].isdigit() and t[4] == "-" and t[7] == "-":
        return None
    for pref in ("OpenAI Codex", "--------", "workdir:", "model:", "provider:",
                 "approval:", "sandbox:", "reasoning", "session id:"):
        if t.startswith(pref):
            return None
    if t.startswith("tokens used"):
        return "本轮用量：%s tokens" % t.split(":", 1)[-1].strip()
    if t.startswith("ERROR") or t.startswith("WARN") or t.startswith("Error:"):
        return None
    return s

def _looks_like_content(line):
    """exec 输出里，这行是否像模型开始输出的内容（=挤进去了）。"""
    s = line.strip()
    if not s:
        return False
    if s == SQUEEZE_MSG:
        return False
    if " ERROR " in s or " WARN " in s:
        return False
    if len(s) > 10 and s[:4].isdigit() and s[4] == "-" and s[7] == "-":
        return False   # 带时间戳的日志行
    for pref in ("OpenAI Codex", "--------", "workdir:", "model:", "provider:",
                 "approval:", "sandbox:", "reasoning", "session id:", "warning:",
                 "user", "codex", "tokens used", "ERROR", "WARN", "Reconnecting",
                 "Error:", "thread-store conflict"):
        if s.startswith(pref):
            return False
    return True

def squeeze(tid, scwd, notify_in=False, n=None):
    """跑一次「codex exec resume <tid> 在」。
    返回 (kind, rc)：kind = 'in'（挤进去了）/ 'fail'（没挤进去）/ 'locked'（被桌面端占用）。
    notify_in=True 时，看到模型开始输出就马上 TG「挤进去了」。"""
    args = [CODEX, "exec", "resume", "--skip-git-repo-check", tid, SQUEEZE_MSG]
    try:
        proc = subprocess.Popen(args, cwd=scwd or None, stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, encoding="utf-8", errors="replace", bufsize=1)
    except Exception as e:
        log("启动 codex exec 失败：%s" % str(e)[:150])
        return ("fail", -1)
    q = queue.Queue()
    def pump():
        try:
            for line in proc.stdout:
                q.put(line)
        except Exception:
            pass
        q.put(None)
    threading.Thread(target=pump, daemon=True).start()

    got_in = False
    locked = False
    archived = False
    fatal = False
    rc = None
    last_line_time = time.time()
    while True:
        if rc is None:
            rc = proc.poll()
        try:
            line = q.get(timeout=0.5)
        except queue.Empty:
            line = ""
        if line is None:
            if rc is None:
                try:
                    rc = proc.wait(timeout=10)
                except Exception:
                    rc = -1
            break
        if line:
            last_line_time = time.time()
            s = line.rstrip()
            if s.strip().startswith("ERROR: Reconnecting"):
                tail = s.strip()[len("ERROR: Reconnecting"):].strip().lstrip(".").strip()
                print("  …正在重连 %s" % tail, flush=True)
            else:
                disp = _display_line(s)
                if disp is not None:
                    print("  │ " + disp, flush=True)
                elif s.strip().startswith("Error:") or s.strip().startswith("ERROR"):
                    log("exec 报错：%s" % s.strip()[:220])
            if "already has an active writer" in s:
                locked = True
            if " is archived" in s:
                archived = True
            if "high demand" in s:
                fatal = True
            if not got_in and not locked and not archived and not fatal and _looks_like_content(s):
                got_in = True
                print("  ✅ 挤进去了，Codex 正在跑", flush=True)
                if notify_in:
                    tg_send(("✅ 第 %d 次：挤进去了，Codex 正在跑" % n) if n else "✅ 挤进去了，Codex 正在跑")
                log("看到模型开始输出 → 判定挤进去了")
        if not got_in and not locked and not fatal and time.time() - last_line_time > FALLBACK_IN_SECS:
            got_in = True
            print("  ✅ 挤进去了（长时间无报错），Codex 正在跑", flush=True)
            if notify_in:
                tg_send(("✅ 第 %d 次：挤进去了（长时间无报错），Codex 正在跑" % n) if n else "✅ 挤进去了（长时间无报错），Codex 正在跑")
            log("长时间无报错 → 判定挤进去了")
    if got_in:
        return ("in", rc if rc is not None else -1)
    if archived:
        return ("archived", rc if rc is not None else -1)
    if locked:
        return ("locked", rc if rc is not None else -1)
    if rc == 0:
        return ("in", 0)
    return ("fail", rc if rc is not None else -1)

def _thread_locked(tid):
    """检查这个会话的写锁是否被占用（被 Codex 桌面端打开时会占用）。"""
    if not IS_WIN:
        return False
    lf = os.path.expanduser("~/.codex/thread-writer-locks/%s.lock" % tid)
    if not os.path.exists(lf):
        return False
    try:
        import msvcrt
        fd = os.open(lf, os.O_RDWR)
        try:
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
            return False
        finally:
            os.close(fd)
    except OSError:
        return True
    except Exception:
        return False

# ───────────────────────── TG 控制（按钮：停止 / 继续 / 选会话 / 新建）─────────────────────────
class Control:
    """主循环与 TG 按钮轮询线程之间的共享状态。"""
    def __init__(self, tid, scwd):
        self.lock = threading.Lock()
        self.tid = tid
        self.scwd = scwd
        self.paused = False
        self.switch = None        # (tid, cwd)：TG 选了新会话，等主循环接手
        self.offset = None        # getUpdates 的 offset
        self.pick_map = {}        # tid -> cwd（列表按钮用）
        self.pick_list = []       # [(tid, 按钮文字)]

def _kb():
    return json.dumps({"inline_keyboard": [[
        {"text": "⏸ 停止挤会话", "callback_data": "stop"},
        {"text": "▶️ 继续挤会话", "callback_data": "resume"}]]}, ensure_ascii=False)

def _picker_kb(ctl):
    rows = []
    for tid, label in ctl.pick_list:
        text = ("当前·" if tid == ctl.tid else "") + label
        rows.append([{"text": text[:44], "callback_data": "pk:%s" % tid}])
    rows.append([{"text": "🆕 新建会话", "callback_data": "new"}])
    rows.append([{"text": "⏸ 停止挤会话", "callback_data": "stop"},
                 {"text": "▶️ 继续挤会话", "callback_data": "resume"}])
    return json.dumps({"inline_keyboard": rows}, ensure_ascii=False)

def recent_threads(limit=8):
    try:
        api = AppServer()
        res = api._request("thread/list", {"limit": limit, "sortKey": "updated_at"})
        api.close()
        return (res or {}).get("data") or []
    except Exception:
        return []

def send_picker(ctl):
    lst = []
    for t in recent_threads():
        tid = t.get("id")
        if not tid:
            continue
        ts = t.get("updatedAt") or 0
        if ts > 1e12:
            ts = ts / 1000.0
        when = time.strftime("%m-%d %H:%M", time.localtime(ts)) if ts else "?"
        name = t.get("name") or (t.get("preview") or "").replace("\n", " ")[:14]
        lst.append((tid, "%s %s" % (when, name)))
        ctl.pick_map[tid] = t.get("cwd")
    with ctl.lock:
        ctl.pick_list = lst
    tg_send("要挤哪个会话？点下面按钮选（🆕 = 新建一个会话来挤）", kb=_picker_kb(ctl))

def new_session(scwd):
    """在 scwd 里新建一个会话（发「在」），返回新会话 id。"""
    try:
        proc = subprocess.Popen([CODEX, "exec", "--skip-git-repo-check", SQUEEZE_MSG],
                                cwd=scwd or None, stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, encoding="utf-8", errors="replace", bufsize=1)
    except Exception as e:
        log("新建会话启动失败：%s" % str(e)[:150])
        return None
    tid = None
    try:
        for line in proc.stdout:
            s = line.rstrip()
            if s.strip().startswith("session id:"):
                tid = s.split("session id:", 1)[1].strip()
            if s.strip().startswith("ERROR: Reconnecting"):
                tail = s.strip()[len("ERROR: Reconnecting"):].strip().lstrip(".").strip()
                print("  …正在重连 %s" % tail, flush=True)
            else:
                disp = _display_line(s)
                if disp is not None:
                    print("  │ " + disp, flush=True)
        proc.wait(timeout=15)
    except Exception:
        pass
    return tid

def handle_tg_update(ctl, u):
    """处理一条 TG 更新（按钮回调）。独立成函数方便测试。"""
    cq = u.get("callback_query")
    if not cq:
        return
    data = cq.get("data") or ""
    cid = cq.get("id")
    if data == "stop":
        with ctl.lock:
            ctl.paused = True
        tg_api("answerCallbackQuery", callback_query_id=cid, text="已暂停")
        print("[%s] ⏸ 收到 TG：停止挤会话" % time.strftime("%H:%M:%S"), flush=True)
        log("TG：暂停")
        tg_send("⏸ 已暂停挤会话。点「继续挤会话」可以选继续哪个会话，或新建一个来挤。")
    elif data == "resume":
        tg_api("answerCallbackQuery", callback_query_id=cid, text="选一个会话")
        print("[%s] ▶️ 收到 TG：继续（选会话）" % time.strftime("%H:%M:%S"), flush=True)
        log("TG：继续")
        send_picker(ctl)
    elif data.startswith("pk:") and len(data) > 3:
        tid = data[3:]
        with ctl.lock:
            cwd = ctl.pick_map.get(tid) or ctl.scwd
            ctl.switch = (tid, cwd)
            ctl.paused = False
        tg_api("answerCallbackQuery", callback_query_id=cid, text="开始挤")
        tg_send("▶️ 好，换成会话 %s，马上开始挤" % tid[:8])
    elif data == "new":
        tg_api("answerCallbackQuery", callback_query_id=cid, text="正在新建")
        def worker():
            with ctl.lock:
                cwd = ctl.scwd
            print("[%s] 🆕 收到 TG：新建会话（目录：%s）" % (time.strftime("%H:%M:%S"), cwd or "默认"), flush=True)
            tg_send("🆕 正在新建一个会话（目录：%s）…" % (cwd or "默认"), kb=None)
            tid = new_session(cwd)
            if tid:
                with ctl.lock:
                    ctl.switch = (tid, cwd)
                    ctl.paused = False
                    ctl.pick_map[tid] = cwd
                tg_send("🆕 新会话 %s 建好了，开始挤" % tid[:8])
            else:
                tg_send("⚠️ 新建会话失败（没拿到会话 id），可以再点一次，或选一个现有会话")
        threading.Thread(target=worker, daemon=True).start()

def tg_poller(ctl):
    """常驻线程：长轮询 TG，处理按钮回调。"""
    offset = ctl.offset
    if offset is None:
        try:
            r = tg_api("getUpdates", offset=-1, timeout=0)
            for u in (r.get("result") or []):
                offset = u.get("update_id", 0) + 1
        except Exception:
            pass
    while True:
        try:
            params = {"timeout": 25}
            if offset is not None:
                params["offset"] = offset
            r = tg_api("getUpdates", timeout_m=35, **params)
            if not r:
                time.sleep(2)
                continue
            for u in (r.get("result") or []):
                offset = u.get("update_id", 0) + 1
                handle_tg_update(ctl, u)
        except Exception:
            time.sleep(3)

# ───────────────────────── 主循环：失败立刻重试；进去后 60 秒心跳 ─────────────────────────
def main_loop(ctl, lock_warned=False, arch_warned=False):
    n = 0
    failing = False
    paused_shown = False
    while True:
        with ctl.lock:
            sw = ctl.switch
            ctl.switch = None
            if sw:
                ctl.tid, ctl.scwd = sw
            tid, scwd, paused = ctl.tid, ctl.scwd, ctl.paused
        if sw:
            n = 0
            failing = False
            lock_warned = False
            arch_warned = False
            print("[%s] ▶️ 换会话：%s（%s）" % (time.strftime("%H:%M:%S"), tid[:8], scwd or ""), flush=True)
            log("TG 换成会话 %s" % tid)
        if paused:
            if not paused_shown:
                paused_shown = True
                print("  ⏸ 已暂停（在 TG 点「继续挤会话」恢复或换会话）", flush=True)
            time.sleep(1.5)
            continue
        if paused_shown:
            paused_shown = False
            print("  ▶️ 继续", flush=True)
        n += 1
        print("[%s] 第 %d 次发「%s」" % (time.strftime("%H:%M:%S"), n, SQUEEZE_MSG), flush=True)
        was_failing = failing
        t0 = time.time()
        kind, rc = squeeze(tid, scwd, notify_in=was_failing, n=n)
        dur = time.time() - t0
        if kind == "locked":
            if not lock_warned:
                lock_warned = True
                tg_send("⚠️ 会话被 Codex 桌面端占用（写锁）\n请在桌面端关掉这个会话（或退出桌面端），我会自动重试")
            print("  ⚠ 被桌面端占用，%d 秒后重试（可在桌面端关掉该会话解除）" % LOCK_RETRY_SECS, flush=True)
            log("被桌面端占用（active writer）")
            time.sleep(LOCK_RETRY_SECS)
            continue
        if kind == "archived":
            if not arch_warned:
                arch_warned = True
                tg_send("⚠️ 盯的会话被归档了，挤不进去\n请在 Codex 桌面端取消归档（恢复）这个会话，我会自动重试")
            print("  ⚠ 会话已被归档，%d 秒后重试（在桌面端取消归档即可恢复）" % LOCK_RETRY_SECS, flush=True)
            log("会话已被归档")
            time.sleep(LOCK_RETRY_SECS)
            continue
        lock_warned = False
        arch_warned = False
        if kind == "in" and rc == 0:
            if was_failing:
                failing = False
                tg_send("🏁 第 %d 次：本轮跑完了，%d 秒后再发「%s」保持会话" % (n, HEARTBEAT_SECS, SQUEEZE_MSG))
                log("本轮跑完了（第 %d 次）" % n)
                print("  🏁 本轮跑完了，%d 秒后发下一个「%s」保持会话" % (HEARTBEAT_SECS, SQUEEZE_MSG), flush=True)
            else:
                log("例行「%s」完成（第 %d 次）" % (SQUEEZE_MSG, n))
            time.sleep(HEARTBEAT_SECS)
            continue
        failing = True
        log("第 %d 次没成（kind=%s rc=%s），立刻重试" % (n, kind, rc))
        if kind == "in":
            print("  本轮又被打回，立刻重试", flush=True)
            tg_send("❌ 第 %d 次：挤进去后又被上游打回，立刻重试" % n)
        else:
            print("  上游还是高负载，没挤进去，立刻重试", flush=True)
            tg_send("❌ 第 %d 次：没挤进去（上游还是高负载），立刻重试" % n)
        if dur < 10:
            time.sleep(3)

# ───────────────────────── 启动器 ─────────────────────────
def run():
    cfg = load_cfg()
    if not cfg.get("token") or not cfg.get("chat"):
        cfg = wizard()
    api = AppServer()
    tid, scwd = pick_session(api)
    t0st = None
    if tid:
        try:
            t0st = (latest_turn(api, tid) or {}).get("status")
            if isinstance(t0st, dict):
                t0st = t0st.get("type")
        except Exception:
            pass
    api.close()
    if not tid:
        print("没有会话")
        return
    print("─" * 52)
    print("  codex-squeeze 已启动 | 会话 %s" % tid[:8])
    print("  目录：%s" % (scwd or "(未知)"))
    print("  当前状态：%s" % (_STATUS_CN.get(str(t0st), t0st or "?")))
    print("  失败后立刻重试；跑完一轮隔 %d 秒发一次「%s」保持会话 | 通知走 Telegram" % (HEARTBEAT_SECS, SQUEEZE_MSG))
    print("  TG 消息下面有按钮：⏸ 停止挤会话 / ▶️ 继续挤会话（继续可选会话或新建）")
    print("─" * 52, flush=True)

    ctl = Control(tid, scwd)
    try:
        r = tg_api("getUpdates", offset=-1, timeout=0)
        for u in (r.get("result") or []):
            ctl.offset = u.get("update_id", 0) + 1
    except Exception:
        pass
    threading.Thread(target=tg_poller, args=(ctl,), daemon=True).start()

    tg_send("🚀 codex-squeeze 已启动，盯的会话：%s（消息下面有「停止 / 继续」按钮）" % tid[:8])
    log("==== 启动，盯 %s ====" % tid)

    lw = _thread_locked(tid)
    if lw:
        print("  ⚠ 会话正被 Codex 桌面端占用：请关掉桌面端里这个会话，脚本会自动重试", flush=True)
        tg_send("⚠️ 会话被 Codex 桌面端占用（写锁）\n请在桌面端关掉这个会话（或退出桌面端），我会自动重试")
    main_loop(ctl, lw)
    tg_send("🏁 codex-squeeze 结束")
    print("  codex-squeeze 结束")

def main():
    if not CODEX:
        print("✗ 没有找到 codex 命令。")
        print("  Windows：装好 Codex 桌面端即可（自动用它自带的 CLI），或 npm install -g @openai/codex；")
        print("  macOS：npm install -g @openai/codex，或把 codex 放到 ~/.local/bin/。")
        return
    run()

if __name__ == "__main__":
    main()
