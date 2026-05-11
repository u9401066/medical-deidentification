"""SQLite-backed authentication service."""

import hashlib
import hmac
import os
import secrets
import sqlite3
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from config import DATA_DIR, MIN_PASSWORD_LENGTH
from models.auth import AuthUser

PBKDF2_ITERATIONS = 260_000


class AuthService:
    """Manage local users and HttpOnly-cookie sessions."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DATA_DIR / "auth.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._init_db()
        self._bootstrap_from_env()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('admin', 'user')),
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_login_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    token_hash TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS anonymous_sessions (
                    token_hash TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    username TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_anonymous_sessions_user ON anonymous_sessions(user_id)")
            conn.commit()

    def _bootstrap_from_env(self) -> None:
        username = os.getenv("MEDICAL_DEID_BOOTSTRAP_ADMIN_USER", "").strip()
        password = os.getenv("MEDICAL_DEID_BOOTSTRAP_ADMIN_PASSWORD", "")
        if username and password:
            try:
                self.bootstrap_first_admin(username=username, password=password)
            except ValueError:
                return

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _serialize_dt(value: datetime) -> str:
        return value.astimezone(timezone.utc).isoformat()

    @staticmethod
    def _parse_dt(value: str | None) -> datetime | None:
        if not value:
            return None
        return datetime.fromisoformat(value)

    @staticmethod
    def _hash_password(password: str) -> str:
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
        return (
            f"pbkdf2_sha256${PBKDF2_ITERATIONS}$"
            f"{salt.hex()}${digest.hex()}"
        )

    @staticmethod
    def _verify_password(password: str, password_hash: str) -> bool:
        try:
            algorithm, iterations, salt_hex, digest_hex = password_hash.split("$", 3)
            if algorithm != "pbkdf2_sha256":
                return False
            expected = bytes.fromhex(digest_hex)
            actual = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                bytes.fromhex(salt_hex),
                int(iterations),
            )
            return hmac.compare_digest(actual, expected)
        except Exception:
            return False

    @staticmethod
    def hash_session_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def _row_to_user(row: sqlite3.Row | dict[str, Any]) -> AuthUser:
        return AuthUser(
            user_id=row["user_id"],
            username=row["username"],
            role=row["role"],
            is_active=bool(row["is_active"]),
            created_at=AuthService._parse_dt(row["created_at"]),
            last_login_at=AuthService._parse_dt(row["last_login_at"]),
        )

    def count_users(self) -> int:
        with self._connect() as conn:
            return int(conn.execute("SELECT COUNT(*) FROM users").fetchone()[0])

    def count_active_admins(self) -> int:
        with self._connect() as conn:
            return int(
                conn.execute(
                    "SELECT COUNT(*) FROM users WHERE role = 'admin' AND is_active = 1"
                ).fetchone()[0]
            )

    def create_user(self, username: str, password: str, role: str = "user") -> AuthUser:
        if role not in {"admin", "user"}:
            raise ValueError("role must be admin or user")
        if len(password) < MIN_PASSWORD_LENGTH:
            raise ValueError(f"password must be at least {MIN_PASSWORD_LENGTH} characters")

        now = self._serialize_dt(self._now())
        user_id = str(uuid.uuid4())
        with self._lock, self._connect() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO users
                    (user_id, username, password_hash, role, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, 1, ?, ?)
                    """,
                    (user_id, username.strip(), self._hash_password(password), role, now, now),
                )
                conn.commit()
            except sqlite3.IntegrityError as exc:
                raise ValueError("username already exists") from exc
        user = self.get_user(user_id)
        if not user:
            raise RuntimeError("created user could not be loaded")
        return user

    def bootstrap_first_admin(self, username: str, password: str) -> AuthUser:
        """Atomically create the first admin account."""
        if len(password) < MIN_PASSWORD_LENGTH:
            raise ValueError(f"password must be at least {MIN_PASSWORD_LENGTH} characters")

        now = self._serialize_dt(self._now())
        user_id = str(uuid.uuid4())
        with self._lock, self._connect() as conn:
            try:
                conn.execute("BEGIN IMMEDIATE")
                if int(conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]) > 0:
                    raise ValueError("bootstrap already completed")
                conn.execute(
                    """
                    INSERT INTO users
                    (user_id, username, password_hash, role, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, 'admin', 1, ?, ?)
                    """,
                    (user_id, username.strip(), self._hash_password(password), now, now),
                )
                conn.commit()
            except sqlite3.IntegrityError as exc:
                conn.rollback()
                raise ValueError("username already exists") from exc
            except Exception:
                conn.rollback()
                raise
        user = self.get_user(user_id)
        if not user:
            raise RuntimeError("created bootstrap admin could not be loaded")
        return user

    def authenticate(self, username: str, password: str) -> AuthUser | None:
        with self._lock, self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username = ?",
                (username.strip(),),
            ).fetchone()
            if not row or not bool(row["is_active"]):
                return None
            if not self._verify_password(password, row["password_hash"]):
                return None
            now = self._serialize_dt(self._now())
            conn.execute(
                "UPDATE users SET last_login_at = ?, updated_at = ? WHERE user_id = ?",
                (now, now, row["user_id"]),
            )
            conn.commit()
            updated = conn.execute(
                "SELECT * FROM users WHERE user_id = ?",
                (row["user_id"],),
            ).fetchone()
            return self._row_to_user(updated)

    def get_user(self, user_id: str) -> AuthUser | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return self._row_to_user(row) if row else None

    def list_users(self) -> list[AuthUser]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
        return [self._row_to_user(row) for row in rows]

    def update_user(
        self,
        user_id: str,
        role: str | None = None,
        is_active: bool | None = None,
    ) -> AuthUser:
        if role is not None:
            if role not in {"admin", "user"}:
                raise ValueError("role must be admin or user")
        if role is None and is_active is None:
            user = self.get_user(user_id)
            if not user:
                raise ValueError("user not found")
            return user

        now = self._serialize_dt(self._now())
        with self._lock, self._connect() as conn:
            if role is not None and is_active is not None:
                cur = conn.execute(
                    "UPDATE users SET role = ?, is_active = ?, updated_at = ? WHERE user_id = ?",
                    (role, 1 if is_active else 0, now, user_id),
                )
            elif role is not None:
                cur = conn.execute(
                    "UPDATE users SET role = ?, updated_at = ? WHERE user_id = ?",
                    (role, now, user_id),
                )
            else:
                cur = conn.execute(
                    "UPDATE users SET is_active = ?, updated_at = ? WHERE user_id = ?",
                    (1 if is_active else 0, now, user_id),
                )
            if cur.rowcount == 0:
                raise ValueError("user not found")
            if is_active is False:
                conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
            conn.commit()
        user = self.get_user(user_id)
        if not user:
            raise ValueError("user not found")
        return user

    def create_session(self, user_id: str) -> tuple[str, datetime]:
        token = secrets.token_urlsafe(48)
        token_hash = self.hash_session_token(token)
        now = self._now()
        expires_at = now + timedelta(days=int(os.getenv("MEDICAL_DEID_SESSION_DAYS", "7")))
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO sessions (token_hash, user_id, created_at, expires_at)
                VALUES (?, ?, ?, ?)
                """,
                (
                    token_hash,
                    user_id,
                    self._serialize_dt(now),
                    self._serialize_dt(expires_at),
                ),
            )
            conn.commit()
        return token, expires_at

    def create_anonymous_session(self) -> tuple[AuthUser, str, datetime]:
        """Create an isolated browser session without a username/password account."""
        token = secrets.token_urlsafe(48)
        token_hash = self.hash_session_token(token)
        now = self._now()
        expires_at = now + timedelta(hours=float(os.getenv("MEDICAL_DEID_ANON_SESSION_HOURS", "12")))
        anon_id = f"anon-{uuid.uuid4()}"
        username = f"guest-{anon_id[-8:]}"
        with self._lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO anonymous_sessions
                (token_hash, user_id, username, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    token_hash,
                    anon_id,
                    username,
                    self._serialize_dt(now),
                    self._serialize_dt(expires_at),
                ),
            )
            conn.commit()
        user = AuthUser(
            user_id=anon_id,
            username=username,
            role="user",
            is_active=True,
            created_at=now,
        )
        return user, token, expires_at

    def get_user_by_session(self, token: str) -> AuthUser | None:
        token_hash = self.hash_session_token(token)
        now = self._serialize_dt(self._now())
        with self._lock, self._connect() as conn:
            row = conn.execute(
                """
                SELECT u.*
                FROM sessions s
                JOIN users u ON u.user_id = s.user_id
                WHERE s.token_hash = ? AND s.expires_at > ? AND u.is_active = 1
                """,
                (token_hash, now),
            ).fetchone()
            conn.execute("DELETE FROM sessions WHERE expires_at <= ?", (now,))
            anon_row = None
            if row is None:
                anon_row = conn.execute(
                    """
                    SELECT user_id, username, created_at
                    FROM anonymous_sessions
                    WHERE token_hash = ? AND expires_at > ?
                    """,
                    (token_hash, now),
                ).fetchone()
            conn.execute("DELETE FROM anonymous_sessions WHERE expires_at <= ?", (now,))
            conn.commit()
        if row:
            return self._row_to_user(row)
        if anon_row:
            return AuthUser(
                user_id=anon_row["user_id"],
                username=anon_row["username"],
                role="user",
                is_active=True,
                created_at=self._parse_dt(anon_row["created_at"]),
            )
        return None

    def delete_session(self, token: str) -> None:
        with self._lock, self._connect() as conn:
            token_hash = self.hash_session_token(token)
            conn.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))
            conn.execute("DELETE FROM anonymous_sessions WHERE token_hash = ?", (token_hash,))
            conn.commit()


_auth_service: AuthService | None = None


def get_auth_service() -> AuthService:
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service


__all__ = ["AuthService", "get_auth_service"]
