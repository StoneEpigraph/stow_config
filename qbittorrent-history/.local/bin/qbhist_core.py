#!/usr/bin/env python3
"""qbhist_core — qBittorrent 下载历史库核心。

数据来源：BT_backup 里的 .torrent / .fastresume（qBittorrent 关闭或被删除后
仍能读到 last-known 元数据），不依赖 Web API。

用法：被 qbhist / qbadd 导入，不单独运行。
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import os
import shutil
import sqlite3
import time
import urllib.parse
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------- 路径

def home() -> Path:
    return Path(os.environ.get("HOME", "/home/stone"))


def bt_backup_dir() -> Path:
    env = os.environ.get("QBT_BT_BACKUP")
    if env:
        return Path(env)
    return home() / ".local/share/qBittorrent/BT_backup"


def db_path() -> Path:
    env = os.environ.get("QBHIST_DB")
    if env:
        return Path(env)
    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg) if xdg else home() / ".local/share"
    return base / "qb-history/history.db"


# ---------------------------------------------------------------- bencode

class Bencode:
    """最小 bencode 解析器，额外记录顶层 info 值的原始字节区间（算 info_hash 用）。"""

    def __init__(self, data: bytes):
        self.data = data
        self.i = 0
        self.info_span: tuple[int, int] | None = None

    def parse(self):
        return self._value(depth=0, top=True)

    def _value(self, depth: int, top: bool):
        if depth > 64:
            raise ValueError("bencode 嵌套过深")
        if self.i >= len(self.data):
            raise ValueError("bencode 意外结束")
        c = self.data[self.i:self.i + 1]
        if c == b"i":
            end = self.data.index(b"e", self.i)
            val = int(self.data[self.i + 1:end])
            self.i = end + 1
            return val
        if c == b"l":
            self.i += 1
            out = []
            while self.data[self.i:self.i + 1] != b"e":
                out.append(self._value(depth + 1, False))
            self.i += 1
            return out
        if c == b"d":
            self.i += 1
            out = {}
            while self.data[self.i:self.i + 1] != b"e":
                key = self._value(depth + 1, False)
                if not isinstance(key, bytes):
                    raise ValueError("bencode dict key 必须是 bytes")
                start = self.i
                val = self._value(depth + 1, False)
                if top and key == b"info":
                    self.info_span = (start, self.i)
                out[key] = val
            self.i += 1
            return out
        # string: <len>:<bytes>
        colon = self.data.index(b":", self.i)
        ln = int(self.data[self.i:colon])
        start = colon + 1
        val = self.data[start:start + ln]
        self.i = start + ln
        return val


def _dec(v):
    """bencode bytes -> str（递归），便于写库。"""
    if isinstance(v, bytes):
        try:
            return v.decode("utf-8")
        except UnicodeDecodeError:
            return v.decode("utf-8", "replace")
    if isinstance(v, list):
        return [_dec(x) for x in v]
    if isinstance(v, dict):
        return {k.decode("utf-8", "replace") if isinstance(k, bytes) else k: _dec(x)
                for k, x in v.items()}
    return v


# ---------------------------------------------------------------- 解析

@dataclass
class TorrentMeta:
    info_hash: str
    name: str = ""
    total_size: int = 0
    file_count: int = 0
    creation_date: int = 0


def torrent_info_hash(raw: bytes) -> tuple[str, dict]:
    p = Bencode(raw)
    obj = p.parse()
    if p.info_span is None:
        raise ValueError("torrent 里没有 info 字典")
    a, b = p.info_span
    ih = hashlib.sha1(raw[a:b]).hexdigest()
    return ih, _dec(obj)


def read_torrent(path: Path) -> TorrentMeta:
    raw = path.read_bytes()
    ih, obj = torrent_info_hash(raw)
    info = obj.get("info", {})
    name = info.get("name", path.stem)
    if isinstance(name, bytes):
        name = name.decode("utf-8", "replace")
    if "length" in info:
        size, cnt = int(info["length"]), 1
    else:
        files = info.get("files") or []
        size = sum(int(f.get("length", 0)) for f in files)
        cnt = len(files)
    return TorrentMeta(ih, str(name), size, cnt, int(obj.get("creation date", 0) or 0))


def read_fastresume(path: Path) -> dict:
    try:
        p = Bencode(path.read_bytes())
        return _dec(p.parse())
    except Exception:
        return {}


def normalize_magnet(s: str) -> str | None:
    """取 magnet 里的 v1 info_hash（40 hex）。兼容 base32 与 btmh。"""
    try:
        q = urllib.parse.urlparse(s).query
        params = urllib.parse.parse_qs(q)
    except Exception:
        return None
    for xt in params.get("xt", []):
        low = xt.lower()
        if low.startswith("urn:btih:"):
            h = xt[9:]
            if len(h) == 40:
                try:
                    int(h, 16)
                    return h.lower()
                except ValueError:
                    continue
            if len(h) == 32:
                try:
                    return base64.b32decode(h.upper()).hex()
                except (binascii.Error, ValueError):
                    continue
        elif low.startswith("urn:btmh:1220") and len(xt) >= 9 + 4 + 64:
            # v2 only：64 hex
            return xt[9 + 4:].lower()[:64]
    return None


def resolve_input(arg: str) -> tuple[str | None, str]:
    """把 magnet / .torrent 文件 / hex hash 统一成 info_hash。返回 (hash, 说明)。"""
    a = arg.strip().strip('"').strip("'")
    if a.lower().startswith("magnet:"):
        return normalize_magnet(a), "magnet"
    for cand in (a, os.path.join(os.getcwd(), a)):
        p = Path(cand).expanduser()
        if p.is_file():
            try:
                return read_torrent(p).info_hash, f"种子文件 {p.name}"
            except Exception as e:
                return None, f"解析失败：{e}"
    if len(a) in (40, 64):
        try:
            int(a, 16)
            return a.lower(), "info_hash"
        except ValueError:
            pass
    return None, "无法识别为磁力链接、种子文件或 info_hash"


# ---------------------------------------------------------------- 数据库

SCHEMA = """
CREATE TABLE IF NOT EXISTS torrents (
    info_hash      TEXT PRIMARY KEY,
    name           TEXT,
    save_path      TEXT,
    category       TEXT,
    tags           TEXT,
    total_size     INTEGER DEFAULT 0,
    file_count     INTEGER DEFAULT 0,
    added_time     INTEGER DEFAULT 0,
    completed_time INTEGER DEFAULT 0,
    is_complete    INTEGER DEFAULT 0,
    hit_count      INTEGER DEFAULT 1,
    present        INTEGER DEFAULT 1,
    first_seen     INTEGER,
    last_seen      INTEGER,
    removed_at     INTEGER
);
CREATE INDEX IF NOT EXISTS idx_completed ON torrents(completed_time);
CREATE INDEX IF NOT EXISTS idx_present   ON torrents(present);

CREATE TABLE IF NOT EXISTS sightings (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    info_hash  TEXT NOT NULL,
    seen_at    INTEGER NOT NULL,
    event      TEXT NOT NULL,
    note       TEXT
);
CREATE INDEX IF NOT EXISTS idx_sight_hash ON sightings(info_hash);
"""


def connect(create: bool = True) -> sqlite3.Connection:
    path = db_path()
    if create:
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


# ---------------------------------------------------------------- 同步

def sync(verbose: bool = False) -> dict:
    """扫描 BT_backup，把当前在列表里的种子并入历史库。

    被删除的任务只会被标记 present=0，记录永久保留 —— 这是"记住下过"的关键。
    """
    now = int(time.time())
    bd = bt_backup_dir()
    stats = {"scanned": 0, "new": 0, "updated": 0, "marked_removed": 0,
             "errors": 0, "skipped": 0}
    if not bd.is_dir():
        raise SystemExit(f"找不到 BT_backup 目录：{bd}")

    conn = connect()
    cur = conn.cursor()
    seen_hashes: set[str] = set()

    for tf in sorted(bd.glob("*.torrent")):
        try:
            meta = read_torrent(tf)
        except Exception:
            stats["errors"] += 1
            continue
        ih = meta.info_hash
        seen_hashes.add(ih)
        stats["scanned"] += 1

        fr = read_fastresume(tf.with_suffix(".fastresume"))
        row = cur.execute(
            "SELECT info_hash, present, hit_count, first_seen, completed_time, "
            "is_complete, name, save_path FROM torrents WHERE info_hash=?",
            (ih,)).fetchone()

        save_path = (fr.get("qBt-savePath") or fr.get("save_path") or "")
        name = (fr.get("qBt-name") or meta.name)[:500]
        category = fr.get("qBt-category") or ""
        tags_raw = fr.get("qBt-tags") or ""
        tags = ", ".join(str(t) for t in tags_raw) if isinstance(tags_raw, list) else str(tags_raw)
        if isinstance(category, list):
            category = ", ".join(str(c) for c in category)
        completed = int(fr.get("completed_time", 0) or 0)
        added = int(fr.get("added_time", 0) or 0) or int(tf.stat().st_mtime)
        is_complete = 1 if (completed > 0 or (meta.total_size and
                                              int(fr.get("num_downloaded", 0) or 0) >= meta.total_size)) else 0

        # 只收"下载完成"的。还在下的不写库 —— 等它下完，自然会被下一次同步或
        # qBittorrent 的完成钩子捞进来。
        if row is None:
            if not is_complete:
                stats["skipped"] += 1
                continue
            cur.execute("""INSERT INTO torrents
                (info_hash,name,save_path,category,tags,total_size,file_count,
                 added_time,completed_time,is_complete,hit_count,present,first_seen,last_seen)
                VALUES (?,?,?,?,?,?,?,?,?,?,1,1,?,?)""",
                        (ih, name, save_path, category, tags,
                         meta.total_size, meta.file_count, added, completed, is_complete, now, now))
            cur.execute("INSERT INTO sightings(info_hash,seen_at,event,note) VALUES(?,?,?,?)",
                        (ih, now, "completed", name))
            stats["new"] += 1
        else:
            was_removed = row["present"] == 0
            hit = row["hit_count"] + (1 if was_removed else 0)
            # 完成信息只增不减：重新下载中不要把已记录的完成时间抹掉
            completed = max(completed, row["completed_time"] or 0)
            is_complete = 1 if (completed > 0 or row["is_complete"]) else 0
            name = name or row["name"]
            save_path = save_path or row["save_path"]
            cur.execute("""UPDATE torrents SET
                name=?, save_path=?, category=?, tags=?, total_size=?, file_count=?,
                added_time=?, completed_time=?, is_complete=?, hit_count=?,
                present=1, last_seen=?, removed_at=NULL
                WHERE info_hash=?""",
                        (name, save_path, category, tags,
                         meta.total_size, meta.file_count, added, completed, is_complete,
                         hit, now, ih))
            if was_removed:
                cur.execute("INSERT INTO sightings(info_hash,seen_at,event,note) VALUES(?,?,?,?)",
                            (ih, now, "re_added", name))
                stats["new"] += 1  # 视为"重新下载"
            else:
                stats["updated"] += 1

    # 不再出现在 BT_backup 里的 → 已从 qBittorrent 移除
    rows = cur.execute("SELECT info_hash FROM torrents WHERE present=1").fetchall()
    for r in rows:
        if r["info_hash"] not in seen_hashes:
            cur.execute("UPDATE torrents SET present=0, removed_at=? WHERE info_hash=?",
                        (now, r["info_hash"]))
            cur.execute("INSERT INTO sightings(info_hash,seen_at,event,note) VALUES(?,?,?,NULL)",
                        (r["info_hash"], now, "removed"))
            stats["marked_removed"] += 1

    conn.commit()
    conn.close()
    if verbose:
        print(f"扫描 {stats['scanned']} 个 · 已完成新增 {stats['new']} · 更新 {stats['updated']} "
              f"· 未完成跳过 {stats['skipped']} · 标记移除 {stats['marked_removed']} "
              f"· 解析失败 {stats['errors']}")
    return stats


# ---------------------------------------------------------------- 查询

def lookup(info_hash: str) -> sqlite3.Row | None:
    """查一条记录。历史库还是空的话先自动建一次，避免首次使用误报「没下过」。"""
    conn = connect()
    row = conn.execute("SELECT * FROM torrents WHERE info_hash=?", (info_hash.lower(),)).fetchone()
    if row is None:
        empty = conn.execute("SELECT COUNT(*) c FROM torrents").fetchone()["c"] == 0
        conn.close()
        if empty:
            try:
                sync()
            except SystemExit:
                return None
            conn = connect()
            row = conn.execute("SELECT * FROM torrents WHERE info_hash=?",
                               (info_hash.lower(),)).fetchone()
            conn.close()
            return row
    conn.close()
    return row


# ---------------------------------------------------------------- 格式化

def human_size(n: int) -> str:
    if not n:
        return "未知"
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    f = float(n)
    for u in units:
        if f < 1024 or u == units[-1]:
            return f"{f:.1f} {u}" if u != "B" else f"{int(f)} B"
        f /= 1024
    return f"{n} B"


def fmt_time(ts: int) -> str:
    if not ts:
        return "未知"
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))


def human_ago(ts: int) -> str:
    if not ts:
        return ""
    d = int(time.time()) - int(ts)
    if d < 60:
        return "刚刚"
    if d < 3600:
        return f"{d // 60} 分钟前"
    if d < 86400:
        return f"{d // 3600} 小时前"
    if d < 86400 * 30:
        return f"{d // 86400} 天前"
    return fmt_time(ts)


def data_still_there(save_path: str, name: str) -> bool:
    if not save_path or not name:
        return False
    p = Path(save_path) / name
    return p.exists()


def render_row(row: sqlite3.Row) -> str:
    lines = []
    lines.append(f"  名称    {row['name']}")
    lines.append(f"  大小    {human_size(row['total_size'])}"
                 + (f" / {row['file_count']} 个文件" if row["file_count"] > 1 else ""))
    if row["completed_time"]:
        lines.append(f"  完成于  {fmt_time(row['completed_time'])}（{human_ago(row['completed_time'])}）")
    elif row["is_complete"]:
        lines.append("  状态    已下载完成（完成时间未记录）")
    else:
        lines.append(f"  添加于  {fmt_time(row['added_time'])}（未记录为已完成）")
    if row["save_path"]:
        lines.append(f"  保存于  {row['save_path']}")
    if row["category"]:
        lines.append(f"  分类    {row['category']}")
    if row["tags"]:
        lines.append(f"  标签    {row['tags']}")
    if row["hit_count"] > 1:
        lines.append(f"  重复    {row['hit_count']} 次")
    if row["present"]:
        lines.append("  当前    仍在 qBittorrent 列表中")
    else:
        gone = "数据文件还在" if data_still_there(row["save_path"] or "", row["name"] or "") else "数据文件可能已删除"
        lines.append(f"  当前    已从 qBittorrent 移除（{gone}）")
    lines.append(f"  hash    {row['info_hash']}")
    return "\n".join(lines)


def qbittorrent_running() -> bool:
    """用 IPC socket 是否可连接来判断 qBittorrent 是否真的活着。

    比看 lockfile 里的 PID 靠谱 —— /proc 可能被隔离，PID 也可能残留。
    """
    p = home() / ".config/qBittorrent/ipc-socket"
    if not p.exists():
        return False
    import socket
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(1)
    try:
        s.connect(str(p))
        return True
    except OSError:
        return False
    finally:
        s.close()


def find_qbittorrent() -> str | None:
    for c in ("qbittorrent", "org.qbittorrent.qBittorrent"):
        p = shutil.which(c)
        if p:
            return p
    return None
