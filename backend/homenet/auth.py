"""Parent login.

* Passwords are stored only as Argon2 hashes (pwdlib, FastAPI's recommendation).
* A login gives the browser a random session token in a cookie that is HttpOnly (page scripts
  cannot read it), SameSite=Strict (other sites cannot send it) and has no expiry date, so it
  ends when the browser closes (owner decision D20). The server keeps only a SHA-256 hash of
  the token and also ends a session after 8 hours without use.
* At most 2 parent accounts. 5 wrong passwords for a username lock its login for 1 minute.
* Unknown usernames are checked against a dummy hash, so the answer takes the same time and
  does not reveal which usernames exist.

Contract for the API:
  current_parent(request) -> dict   FastAPI dependency: {"id", "username", "display_name"};
                                    raises 401 when not logged in.
"""
from __future__ import annotations

import hashlib
import secrets
import sqlite3
import threading
import time
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pwdlib import PasswordHash
from pydantic import BaseModel, Field

COOKIE = "hg_session"
MAX_PARENTS = 2
IDLE_SECONDS = 8 * 3600
MAX_FAILURES = 5
LOCK_SECONDS = 60

_hasher = PasswordHash.recommended()
_DUMMY_HASH = _hasher.hash("not-a-real-password")
_failures: dict[str, list[float]] = {}
_lock = threading.Lock()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password, password_hash)
    except Exception:          # unknown or broken hash format
        return False


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _conn(request: Request) -> sqlite3.Connection:
    return request.app.state.runtime.conn


def _unauthorized() -> HTTPException:
    return HTTPException(status.HTTP_401_UNAUTHORIZED, "Not logged in")


# --- parents -------------------------------------------------------------------------------

def create_parent(conn: sqlite3.Connection, username: str, display_name: str, password: str) -> int:
    count = conn.execute("SELECT COUNT(*) FROM parents").fetchone()[0]
    if count >= MAX_PARENTS:
        raise ValueError(f"at most {MAX_PARENTS} parent accounts")
    pid = conn.execute(
        "INSERT INTO parents(username, display_name, password_hash, created_at) VALUES (?,?,?,?)",
        (username.strip().lower(), display_name.strip(), hash_password(password),
         datetime.now().replace(microsecond=0).isoformat())).lastrowid
    conn.commit()
    return pid


# --- sessions --------------------------------------------------------------------------------

def _locked(username: str, now: float) -> bool:
    with _lock:
        recent = [t for t in _failures.get(username, []) if now - t < LOCK_SECONDS]
        _failures[username] = recent
        return len(recent) >= MAX_FAILURES


def _record_failure(username: str, now: float) -> None:
    with _lock:
        _failures.setdefault(username, []).append(now)


def reset_failures() -> None:
    with _lock:
        _failures.clear()


def login(conn: sqlite3.Connection, username: str, password: str, now: float | None = None) -> str:
    """Returns a new session token, or raises PermissionError."""
    now = time.time() if now is None else now
    username = username.strip().lower()
    if _locked(username, now):
        raise PermissionError("locked")
    row = conn.execute("SELECT * FROM parents WHERE username = ?", (username,)).fetchone()
    ok = verify_password(password, row["password_hash"] if row else _DUMMY_HASH) and row is not None
    if not ok:
        _record_failure(username, now)
        raise PermissionError("wrong")
    with _lock:
        _failures.pop(username, None)
    token = secrets.token_urlsafe(32)
    conn.execute("INSERT INTO sessions(token_hash, parent_id, created_at, last_seen) VALUES (?,?,?,?)",
                 (_token_hash(token), row["id"], now, now))
    conn.execute("DELETE FROM sessions WHERE last_seen < ?", (now - IDLE_SECONDS,))
    conn.commit()
    return token


def parent_for_token(conn: sqlite3.Connection, token: str | None, now: float | None = None) -> dict | None:
    if not token:
        return None
    now = time.time() if now is None else now
    th = _token_hash(token)
    row = conn.execute(
        "SELECT s.last_seen, p.id, p.username, p.display_name FROM sessions s "
        "JOIN parents p ON p.id = s.parent_id WHERE s.token_hash = ?", (th,)).fetchone()
    if row is None:
        return None
    if now - row["last_seen"] > IDLE_SECONDS:
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (th,))
        conn.commit()
        return None
    conn.execute("UPDATE sessions SET last_seen = ? WHERE token_hash = ?", (now, th))
    conn.commit()
    return {"id": row["id"], "username": row["username"], "display_name": row["display_name"]}


def logout(conn: sqlite3.Connection, token: str | None) -> None:
    if token:
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_token_hash(token),))
        conn.commit()


# --- FastAPI ---------------------------------------------------------------------------------

def current_parent(request: Request) -> dict:
    rt = request.app.state.runtime
    if rt is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "The server is still starting")
    with rt.lock:
        parent = parent_for_token(rt.conn, request.cookies.get(COOKIE))
    if parent is None:
        raise _unauthorized()
    return parent


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class ParentIn(BaseModel):
    username: str = Field(min_length=2, max_length=32, pattern=r"^[A-Za-z0-9_.-]+$")
    display_name: str = Field(min_length=1, max_length=40)
    password: str = Field(min_length=8, max_length=256)


router = APIRouter(prefix="/api/auth")


@router.post("/login")
def login_route(body: LoginIn, request: Request, response: Response) -> dict:
    rt = request.app.state.runtime
    if rt is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "The server is still starting")
    try:
        with rt.lock:
            token = login(rt.conn, body.username, body.password)
    except PermissionError as e:
        if str(e) == "locked":
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS,
                                "Too many wrong passwords. Try again in a minute.")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong username or password")
    response.set_cookie(COOKIE, token, httponly=True, samesite="strict", path="/", secure=False)
    with rt.lock:
        parent = parent_for_token(rt.conn, token)
    return {"parent": parent}


@router.post("/logout")
def logout_route(request: Request, response: Response) -> dict:
    rt = request.app.state.runtime
    with rt.lock:
        logout(rt.conn, request.cookies.get(COOKIE))
    response.delete_cookie(COOKIE, path="/")
    return {"ok": True}


@router.get("/me")
def me(parent: dict = Depends(current_parent)) -> dict:
    return {"parent": parent}


@router.get("/parents")
def list_parents(request: Request, parent: dict = Depends(current_parent)) -> dict:
    rt = request.app.state.runtime
    with rt.lock:
        rows = rt.conn.execute("SELECT id, username, display_name FROM parents ORDER BY id").fetchall()
    return {"parents": [dict(r) for r in rows], "max": MAX_PARENTS}


@router.post("/parents", status_code=201)
def add_parent(body: ParentIn, request: Request, parent: dict = Depends(current_parent)) -> dict:
    rt = request.app.state.runtime
    with rt.lock:
        try:
            pid = create_parent(rt.conn, body.username, body.display_name, body.password)
        except ValueError as e:
            raise HTTPException(status.HTTP_409_CONFLICT, str(e))
        except sqlite3.IntegrityError:
            raise HTTPException(status.HTTP_409_CONFLICT, "username already taken")
    return {"id": pid}
