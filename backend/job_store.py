from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any


class JobStore:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()
        self.mark_incomplete_jobs_as_interrupted()

    def _init_schema(self) -> None:
        with self._conn:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    action TEXT NOT NULL,
                    command_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at_utc TEXT NOT NULL,
                    started_at_utc TEXT,
                    finished_at_utc TEXT,
                    return_code INTEGER,
                    error TEXT,
                    retried_from_job_id TEXT
                );

                CREATE TABLE IF NOT EXISTS job_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    line_no INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    created_at_utc TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (job_id) REFERENCES jobs(id)
                );

                CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at_utc DESC);
                CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
                CREATE INDEX IF NOT EXISTS idx_job_logs_job_id ON job_logs(job_id, line_no);
                """
            )

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def mark_incomplete_jobs_as_interrupted(self) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                """
                UPDATE jobs
                SET status = 'error',
                    error = COALESCE(error, 'server restarted before job completed')
                WHERE status IN ('queued', 'running')
                """
            )

    def create_job(
        self,
        *,
        job_id: str,
        action: str,
        command: list[str],
        status: str,
        created_at_utc: str,
        retried_from_job_id: str | None = None,
    ) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                """
                INSERT INTO jobs (
                    id, action, command_json, status, created_at_utc, retried_from_job_id
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (job_id, action, json.dumps(command, ensure_ascii=False), status, created_at_utc, retried_from_job_id),
            )

    def update_job(self, job_id: str, **kwargs: Any) -> None:
        if not kwargs:
            return
        allowed = {
            "status",
            "started_at_utc",
            "finished_at_utc",
            "return_code",
            "error",
            "retried_from_job_id",
        }
        fields = []
        values = []
        for key, value in kwargs.items():
            if key not in allowed:
                continue
            fields.append(f"{key} = ?")
            values.append(value)
        if not fields:
            return
        values.append(job_id)
        with self._lock, self._conn:
            self._conn.execute(f"UPDATE jobs SET {', '.join(fields)} WHERE id = ?", values)

    def append_log(self, job_id: str, line: str) -> None:
        with self._lock, self._conn:
            row = self._conn.execute(
                "SELECT COALESCE(MAX(line_no), 0) AS max_line_no FROM job_logs WHERE job_id = ?",
                (job_id,),
            ).fetchone()
            next_line_no = int(row["max_line_no"]) + 1 if row is not None else 1
            self._conn.execute(
                "INSERT INTO job_logs (job_id, line_no, content) VALUES (?, ?, ?)",
                (job_id, next_line_no, line.rstrip("\n")),
            )

    def _row_to_job(self, row: sqlite3.Row, *, with_logs: bool, log_limit: int) -> dict[str, Any]:
        payload = {
            "id": row["id"],
            "action": row["action"],
            "command": json.loads(row["command_json"]),
            "status": row["status"],
            "created_at_utc": row["created_at_utc"],
            "started_at_utc": row["started_at_utc"],
            "finished_at_utc": row["finished_at_utc"],
            "return_code": row["return_code"],
            "error": row["error"],
            "retried_from_job_id": row["retried_from_job_id"],
            "logs": [],
        }
        if with_logs:
            log_rows = self._conn.execute(
                """
                SELECT content
                FROM job_logs
                WHERE job_id = ?
                ORDER BY line_no DESC
                LIMIT ?
                """,
                (row["id"], max(1, log_limit)),
            ).fetchall()
            payload["logs"] = [item["content"] for item in reversed(log_rows)]
        return payload

    def list_jobs(self, *, limit: int = 200, with_logs: bool = False, log_limit: int = 50) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT *
                FROM jobs
                ORDER BY created_at_utc DESC
                LIMIT ?
                """,
                (max(1, limit),),
            ).fetchall()
            return [self._row_to_job(row, with_logs=with_logs, log_limit=log_limit) for row in rows]

    def get_job(self, job_id: str, *, with_logs: bool = True, log_limit: int = 500) -> dict[str, Any] | None:
        with self._lock:
            row = self._conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            if row is None:
                return None
            return self._row_to_job(row, with_logs=with_logs, log_limit=log_limit)

    def get_job_command(self, job_id: str) -> tuple[str, list[str]] | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT action, command_json FROM jobs WHERE id = ?",
                (job_id,),
            ).fetchone()
            if row is None:
                return None
            return row["action"], json.loads(row["command_json"])

    def list_failed_jobs(self, *, limit: int = 20) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._conn.execute(
                """
                SELECT *
                FROM jobs
                WHERE status = 'error'
                ORDER BY created_at_utc DESC
                LIMIT ?
                """,
                (max(1, limit),),
            ).fetchall()
            return [self._row_to_job(row, with_logs=False, log_limit=0) for row in rows]
