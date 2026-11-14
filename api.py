#!/usr/bin/env python3
"""YanYun relationship-graph data API. Reads/writes MySQL yanyun DB, serves JSON on 127.0.0.1.
Read endpoints are public; write endpoints require Bearer token (see /opt/yanyun/admin-token).
"""
import base64
import configparser
import json
import os
from urllib.parse import urlparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pymysql

CONF_PATH = "/opt/yanyun/db.conf"
TOKEN_PATH = "/opt/yanyun/admin-token"
HOST = "127.0.0.1"
PORT = 39002
AVATAR_DIR = "/www/wwwroot/wenhxy.dpdns.org/yanyun/avatars"
# data URL 前缀 -> (扩展名, 文件头魔数)
AVATAR_FORMATS = {
    "data:image/jpeg;base64,": (".jpg", b"\xff\xd8\xff"),
    "data:image/png;base64,": (".png", b"\x89PNG"),
    "data:image/webp;base64,": (".webp", b"RIFF"),
}
AVATAR_MAX_BYTES = 2 * 1024 * 1024  # 解码后最大 2MB

REL_TYPES = {"xiayuan", "shitu", "jieyi"}
SYMMETRIC_TYPES = {"xiayuan", "jieyi"}


def load_db_conf():
    cp = configparser.ConfigParser()
    cp.read(CONF_PATH)
    return {
        "host": cp.get("client", "host", fallback="localhost"),
        "user": cp.get("client", "user"),
        "password": cp.get("client", "password"),
        "database": cp.get("client", "database", fallback="yanyun"),
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.DictCursor,
        "connect_timeout": 5,
        "read_timeout": 5,
    }


def load_token():
    try:
        with open(TOKEN_PATH, "r", encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def db_conn():
    return pymysql.connect(**load_db_conf())


def fetch_data():
    conn = db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, pid, name, surname, color, x, y, mx, my, tag, role, "
                "center, bio, avatar FROM people ORDER BY id"
            )
            people = cur.fetchall()
            cur.execute(
                "SELECT id, from_id, to_id, type, label, bend, note "
                "FROM relationships ORDER BY id"
            )
            relationships = cur.fetchall()
    finally:
        conn.close()
    for p in people:
        p["center"] = bool(p.get("center"))
    return {"people": people, "relationships": relationships}


class Handler(BaseHTTPRequestHandler):
    # ---------- helpers ----------
    def _send(self, code, body):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False).encode("utf-8")
        elif isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _err(self, code, msg):
        self._send(code, {"ok": False, "error": msg})

    def _read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return None
        return data if isinstance(data, dict) else None

    def _check_auth(self):
        token = load_token()
        if not token:
            return False
        auth = self.headers.get("Authorization") or ""
        if auth.startswith("Bearer "):
            return auth[7:].strip() == token
        return False

    # ---------- read ----------
    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        if path == "/yanyun/api/data":
            try:
                data = fetch_data()
            except Exception as exc:  # noqa: BLE001 - surface as 500
                self._err(500, str(exc))
                return
            self._send(200, data)
        elif path == "/yanyun/api/health":
            self._send(200, {"ok": True})
        elif path == "/yanyun/api/auth-check":
            if not self._check_auth():
                self._err(401, "密码错误")
                return
            self._send(200, {"ok": True})
        else:
            self._err(404, "not found")

    # ---------- write: people ----------
    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        if not self._check_auth():
            self._err(401, "密码错误")
            return
        parts = [p for p in path.split("/") if p]
        if path == "/yanyun/api/people":
            self._add_person()
        elif path == "/yanyun/api/relationships":
            self._add_relationship()
        elif len(parts) == 5 and parts[:3] == ["yanyun", "api", "people"] and parts[4] == "avatar":
            self._upload_avatar(parts[3])
        else:
            self._err(404, "not found")

    def do_PUT(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        if not self._check_auth():
            self._err(401, "密码错误")
            return
        parts = [p for p in path.split("/") if p]
        # /yanyun/api/people/<id>
        if len(parts) == 4 and parts[:3] == ["yanyun", "api", "people"]:
            self._update_person(parts[3])
        elif len(parts) == 4 and parts[:3] == ["yanyun", "api", "relationships"]:
            self._update_relationship(parts[3])
        else:
            self._err(404, "not found")

    def do_DELETE(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        if not self._check_auth():
            self._err(401, "密码错误")
            return
        parts = [p for p in path.split("/") if p]
        if len(parts) == 4 and parts[:3] == ["yanyun", "api", "people"]:
            self._delete_person(parts[3])
        elif len(parts) == 4 and parts[:3] == ["yanyun", "api", "relationships"]:
            self._delete_relationship(parts[3])
        elif len(parts) == 5 and parts[:3] == ["yanyun", "api", "people"] and parts[4] == "avatar":
            self._delete_avatar(parts[3])
        else:
            self._err(404, "not found")

    def _add_person(self):
        data = self._read_json()
        if data is None:
            self._err(400, "请求不是合法 JSON")
            return
        name = (data.get("name") or "").strip()
        if not name:
            self._err(400, "名字不能为空")
            return
        role = (data.get("role") or "").strip() or None
        bio = (data.get("bio") or "").strip() or None
        try:
            conn = db_conn()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO people (name, surname, role, bio) "
                        "VALUES (%s, %s, %s, %s)",
                        (name, name[0], role, bio),
                    )
                    new_id = cur.lastrowid
                conn.commit()
            finally:
                conn.close()
        except pymysql.err.IntegrityError:
            self._err(409, "该名字已存在")
            return
        except Exception as exc:  # noqa: BLE001
            self._err(500, str(exc))
            return
        self._send(200, {"ok": True, "id": new_id})

    def _update_person(self, pid):
        try:
            pid = int(pid)
        except ValueError:
            self._err(400, "id 不合法")
            return
        data = self._read_json()
        if data is None:
            self._err(400, "请求不是合法 JSON")
            return
        sets, vals = [], []
        if "name" in data:
            name = (data.get("name") or "").strip()
            if not name:
                self._err(400, "名字不能为空")
                return
            sets.append("name=%s")
            vals.append(name)
            sets.append("surname=%s")
            vals.append(name[0])
        if "role" in data:
            sets.append("role=%s")
            vals.append((data.get("role") or "").strip() or None)
        if "bio" in data:
            sets.append("bio=%s")
            vals.append((data.get("bio") or "").strip() or None)
        if not sets:
            self._err(400, "没有要改的字段")
            return
        try:
            conn = db_conn()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE people SET " + ", ".join(sets) + " WHERE id=%s",
                        (*vals, pid),
                    )
                    if cur.rowcount == 0:
                        conn.rollback()
                        self._err(404, "没有这个人")
                        return
                conn.commit()
            finally:
                conn.close()
        except pymysql.err.IntegrityError:
            self._err(409, "该名字已存在")
            return
        except Exception as exc:  # noqa: BLE001
            self._err(500, str(exc))
            return
        self._send(200, {"ok": True})

    def _upload_avatar(self, pid):
        """上传头像：JSON {image: "data:image/jpeg;base64,..."}，浏览器端已裁成
        200x200。校验魔数后按 <id>.<ext> 存到 avatars 目录，DB 记文件名。"""
        try:
            pid = int(pid)
        except ValueError:
            self._err(400, "id 不合法")
            return
        data = self._read_json()
        if data is None:
            self._err(400, "请求不是合法 JSON")
            return
        img = (data.get("image") or "").strip()
        if not img:
            self._err(400, "没有图片数据")
            return
        fmt = None
        for prefix, spec in AVATAR_FORMATS.items():
            if img.startswith(prefix):
                fmt = spec
                b64 = img[len(prefix):]
                break
        if fmt is None:
            self._err(400, "只支持 JPEG / PNG / WebP")
            return
        ext, magic = fmt
        try:
            raw = base64.b64decode(b64, validate=True)
        except Exception:  # noqa: BLE001
            self._err(400, "图片数据损坏")
            return
        if len(raw) > AVATAR_MAX_BYTES:
            self._err(400, "图片太大（超过 2MB）")
            return
        if not raw.startswith(magic):
            self._err(400, "图片数据损坏")
            return
        if ext == ".webp" and not raw[8:12] == b"WEBP":
            self._err(400, "图片数据损坏")
            return
        try:
            conn = db_conn()
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT id, avatar FROM people WHERE id=%s", (pid,))
                    row = cur.fetchone()
                    if not row:
                        self._err(404, "没有这个人")
                        return
                    os.makedirs(AVATAR_DIR, exist_ok=True)
                    # 换格式时删掉旧文件
                    old = row.get("avatar")
                    filename = "%d%s" % (pid, ext)
                    if old and old != filename:
                        try:
                            os.remove(os.path.join(AVATAR_DIR, old))
                        except OSError:
                            pass
                    with open(os.path.join(AVATAR_DIR, filename), "wb") as f:
                        f.write(raw)
                    os.chmod(os.path.join(AVATAR_DIR, filename), 0o644)
                    cur.execute("UPDATE people SET avatar=%s WHERE id=%s", (filename, pid))
                conn.commit()
            finally:
                conn.close()
        except Exception as exc:  # noqa: BLE001
            self._err(500, str(exc))
            return
        self._send(200, {"ok": True, "avatar": filename})

    def _delete_avatar(self, pid):
        try:
            pid = int(pid)
        except ValueError:
            self._err(400, "id 不合法")
            return
        try:
            conn = db_conn()
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT avatar FROM people WHERE id=%s", (pid,))
                    row = cur.fetchone()
                    if not row:
                        self._err(404, "没有这个人")
                        return
                    old = row.get("avatar")
                    if old:
                        try:
                            os.remove(os.path.join(AVATAR_DIR, old))
                        except OSError:
                            pass
                    cur.execute("UPDATE people SET avatar=NULL WHERE id=%s", (pid,))
                conn.commit()
            finally:
                conn.close()
        except Exception as exc:  # noqa: BLE001
            self._err(500, str(exc))
            return
        self._send(200, {"ok": True})

    def _delete_person(self, pid):
        try:
            pid = int(pid)
        except ValueError:
            self._err(400, "id 不合法")
            return
        try:
            conn = db_conn()
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT id, avatar FROM people WHERE id=%s", (pid,))
                    row = cur.fetchone()
                    if not row:
                        self._err(404, "没有这个人")
                        return
                    if row.get("avatar"):
                        try:
                            os.remove(os.path.join(AVATAR_DIR, row["avatar"]))
                        except OSError:
                            pass
                    cur.execute(
                        "DELETE FROM relationships WHERE from_id=%s OR to_id=%s",
                        (pid, pid),
                    )
                    cur.execute("DELETE FROM people WHERE id=%s", (pid,))
                conn.commit()
            finally:
                conn.close()
        except Exception as exc:  # noqa: BLE001
            self._err(500, str(exc))
            return
        self._send(200, {"ok": True})

    def _insert_relationship(self, cur, from_id, to_id, typ):
        """Core insert with rules. Returns (new_id, None) on success,
        (None, error_msg) on failure. Does not commit."""
        cur.execute(
            "SELECT COUNT(*) AS n FROM people "
            "WHERE id IN (%s, %s)", (from_id, to_id))
        if cur.fetchone()["n"] != 2:
            return None, "选的人不存在"
        if typ == "xiayuan":
            # 每人最多 5 个侠缘（互为侠缘，任一方向都算）
            for pid in (from_id, to_id):
                cur.execute(
                    "SELECT COUNT(*) AS n FROM relationships "
                    "WHERE type='xiayuan' "
                    "AND (from_id=%s OR to_id=%s)",
                    (pid, pid))
                if cur.fetchone()["n"] >= 5:
                    cur.execute(
                        "SELECT name FROM people WHERE id=%s",
                        (pid,))
                    nm = cur.fetchone()["name"]
                    return None, "「%s」已有 5 个侠缘，不能再加" % nm
            cur.execute(
                "SELECT COUNT(*) AS n FROM relationships WHERE type=%s "
                "AND ((from_id=%s AND to_id=%s) "
                "OR (from_id=%s AND to_id=%s))",
                (typ, from_id, to_id, to_id, from_id))
            if cur.fetchone()["n"] > 0:
                return None, "这条关系已存在"
            cur.execute(
                "INSERT INTO relationships (from_id, to_id, type) "
                "VALUES (%s, %s, %s)", (from_id, to_id, typ))
            return cur.lastrowid, None
        elif typ == "jieyi":
            # 结义是成组的关系：把两边的结义组并成一组，全组互相结义
            cur.execute(
                "SELECT from_id, to_id FROM relationships "
                "WHERE type='jieyi'")
            adj = {}
            for row in cur.fetchall():
                a, b = row["from_id"], row["to_id"]
                adj.setdefault(a, set()).add(b)
                adj.setdefault(b, set()).add(a)
            def group_of(start):
                seen = {start}
                stack = [start]
                while stack:
                    n = stack.pop()
                    for m in adj.get(n, ()):
                        if m not in seen:
                            seen.add(m)
                            stack.append(m)
                return seen
            merged = group_of(from_id) | group_of(to_id)
            if len(merged) > 10:
                return None, "一个结义最多 10 个人，合并后有 %d 个人" % len(merged)
            cur.execute(
                "SELECT from_id, to_id FROM relationships "
                "WHERE type='jieyi'")
            have = set()
            for row in cur.fetchall():
                a, b = row["from_id"], row["to_id"]
                have.add((a, b))
                have.add((b, a))
            members = sorted(merged)
            new_id = None
            for i in range(len(members)):
                for j in range(i + 1, len(members)):
                    a, b = members[i], members[j]
                    if (a, b) in have:
                        if {a, b} == {from_id, to_id}:
                            cur.execute(
                                "SELECT id FROM relationships "
                                "WHERE type='jieyi' "
                                "AND ((from_id=%s AND to_id=%s) "
                                "OR (from_id=%s AND to_id=%s))",
                                (a, b, b, a))
                            row = cur.fetchone()
                            if row:
                                new_id = row["id"]
                        continue
                    cur.execute(
                        "INSERT INTO relationships "
                        "(from_id, to_id, type) "
                        "VALUES (%s, %s, %s)", (a, b, "jieyi"))
                    if new_id is None:
                        new_id = cur.lastrowid
                    if {a, b} == {from_id, to_id}:
                        new_id = cur.lastrowid
            if new_id is None:
                return None, "这条关系已存在"
            return new_id, None
        else:  # shitu
            # 每人最多 5 个徒弟（from_id 是师傅）
            cur.execute(
                "SELECT COUNT(*) AS n FROM relationships "
                "WHERE type='shitu' AND from_id=%s",
                (from_id,))
            if cur.fetchone()["n"] >= 5:
                cur.execute(
                    "SELECT name FROM people WHERE id=%s",
                    (from_id,))
                nm = cur.fetchone()["name"]
                return None, "「%s」已有 5 个徒弟，不能再加" % nm
            cur.execute(
                "SELECT COUNT(*) AS n FROM relationships WHERE type=%s "
                "AND from_id=%s AND to_id=%s",
                (typ, from_id, to_id))
            if cur.fetchone()["n"] > 0:
                return None, "这条关系已存在"
            cur.execute(
                "INSERT INTO relationships (from_id, to_id, type) "
                "VALUES (%s, %s, %s)", (from_id, to_id, typ))
            return cur.lastrowid, None

    def _add_relationship(self):
        data = self._read_json()
        if data is None:
            self._err(400, "请求不是合法 JSON")
            return
        try:
            from_id = int(data.get("from_id"))
            to_id = int(data.get("to_id"))
        except (TypeError, ValueError):
            self._err(400, "from_id / to_id 不合法")
            return
        typ = (data.get("type") or "").strip()
        if typ not in REL_TYPES:
            self._err(400, "type 只能是 xiayuan / shitu / jieyi")
            return
        if from_id == to_id:
            self._err(400, "不能和自己建立关系")
            return
        try:
            conn = db_conn()
            try:
                with conn.cursor() as cur:
                    new_id, err = self._insert_relationship(cur, from_id, to_id, typ)
                    if err:
                        code = 404 if "不存在" in err else (400 if ("已有" in err or "最多" in err) else 409)
                        self._err(code, err)
                        return
                conn.commit()
            finally:
                conn.close()
        except Exception as exc:  # noqa: BLE001
            self._err(500, str(exc))
            return
        self._send(200, {"ok": True, "id": new_id})

    def _update_relationship(self, rid):
        """改一条关系（类型 / 对方）。做法：删掉旧边，按新值重新走一遍
        建边规则；新边建不起来就把旧边原样恢复并报错。"""
        try:
            rid = int(rid)
        except ValueError:
            self._err(400, "id 不合法")
            return
        data = self._read_json()
        if data is None:
            self._err(400, "请求不是合法 JSON")
            return
        try:
            conn = db_conn()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT from_id, to_id, type FROM relationships WHERE id=%s",
                        (rid,))
                    old = cur.fetchone()
                    if not old:
                        self._err(404, "没有这条关系")
                        return
                    new_from = int(data.get("from_id", old["from_id"]))
                    new_to = int(data.get("to_id", old["to_id"]))
                    new_type = (data.get("type") or old["type"]).strip()
                    if new_type not in REL_TYPES:
                        self._err(400, "type 只能是 xiayuan / shitu / jieyi")
                        return
                    if new_from == new_to:
                        self._err(400, "不能和自己建立关系")
                        return
                    if (new_from, new_to, new_type) == (old["from_id"], old["to_id"], old["type"]) \
                            or (new_type in SYMMETRIC_TYPES
                                and (new_to, new_from, new_type) == (old["from_id"], old["to_id"], old["type"])):
                        self._send(200, {"ok": True, "id": rid})
                        return
                    cur.execute("DELETE FROM relationships WHERE id=%s", (rid,))
                    new_id, err = self._insert_relationship(cur, new_from, new_to, new_type)
                    if err:
                        # 建不起来，旧边原样恢复
                        cur.execute(
                            "INSERT INTO relationships (id, from_id, to_id, type) "
                            "VALUES (%s, %s, %s, %s)",
                            (rid, old["from_id"], old["to_id"], old["type"]))
                        conn.commit()
                        self._err(400, err)
                        return
                conn.commit()
            finally:
                conn.close()
        except (TypeError, ValueError):
            self._err(400, "from_id / to_id 不合法")
            return
        except Exception as exc:  # noqa: BLE001
            self._err(500, str(exc))
            return
        self._send(200, {"ok": True, "id": new_id})

    def _delete_relationship(self, rid):
        try:
            rid = int(rid)
        except ValueError:
            self._err(400, "id 不合法")
            return
        try:
            conn = db_conn()
            try:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM relationships WHERE id=%s", (rid,))
                    if cur.rowcount == 0:
                        conn.rollback()
                        self._err(404, "没有这条关系")
                        return
                conn.commit()
            finally:
                conn.close()
        except Exception as exc:  # noqa: BLE001
            self._err(500, str(exc))
            return
        self._send(200, {"ok": True})

    def log_message(self, fmt, *args):
        pass  # keep journal quiet


if __name__ == "__main__":
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
