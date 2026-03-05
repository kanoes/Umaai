#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT / "uma" / "index.json"
BODY_METRICS_PATH = ROOT / "data" / "body_metrics.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json_file(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def action_commands() -> dict[str, list[str]]:
    py = sys.executable
    return {
        "fetch_info": [
            py,
            "-m",
            "dataFetcher.fetch_uma_info",
            "--name-map",
            "ref/name_map.json",
            "--out-root",
            "uma",
        ],
        "fetch_chara": [
            py,
            "-m",
            "dataFetcher.fetch_uma_chara",
            "--index",
            "uma/index.json",
            "--out-root",
            "uma",
        ],
        "build_body_metrics": [
            py,
            "-m",
            "dataGenerator.build_body_metrics",
            "--uma-root",
            "uma",
            "--index",
            "uma/index.json",
            "--output",
            "data/body_metrics.json",
        ],
    }


@dataclass
class Job:
    id: str
    action: str
    command: list[str]
    status: str = "queued"
    created_at_utc: str = field(default_factory=now_iso)
    started_at_utc: str | None = None
    finished_at_utc: str | None = None
    return_code: int | None = None
    error: str | None = None
    logs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "action": self.action,
            "command": self.command,
            "status": self.status,
            "created_at_utc": self.created_at_utc,
            "started_at_utc": self.started_at_utc,
            "finished_at_utc": self.finished_at_utc,
            "return_code": self.return_code,
            "error": self.error,
            "logs": self.logs[-500:],
        }


class JobManager:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def list_jobs(self) -> list[dict[str, Any]]:
        with self._lock:
            jobs = list(self._jobs.values())
        jobs.sort(key=lambda x: x.created_at_utc, reverse=True)
        return [job.to_dict() for job in jobs]

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        with self._lock:
            job = self._jobs.get(job_id)
            return None if job is None else job.to_dict()

    def _append_log(self, job_id: str, line: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            job.logs.append(line.rstrip("\n"))
            if len(job.logs) > 5000:
                job.logs = job.logs[-2000:]

    def _set_fields(self, job_id: str, **kwargs: Any) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            for key, value in kwargs.items():
                setattr(job, key, value)

    def start(self, action: str, command: list[str]) -> dict[str, Any]:
        job_id = uuid.uuid4().hex[:12]
        job = Job(id=job_id, action=action, command=command)
        with self._lock:
            self._jobs[job_id] = job

        thread = threading.Thread(target=self._run, args=(job_id,), daemon=True)
        thread.start()
        return job.to_dict()

    def _run(self, job_id: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            command = job.command
        self._set_fields(job_id, status="running", started_at_utc=now_iso())

        try:
            proc = subprocess.Popen(
                command,
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        except Exception as exc:
            self._set_fields(
                job_id,
                status="error",
                error=f"failed to start process: {exc}",
                finished_at_utc=now_iso(),
            )
            return

        assert proc.stdout is not None
        for line in proc.stdout:
            self._append_log(job_id, line)
        proc.wait()

        if proc.returncode == 0:
            self._set_fields(
                job_id,
                status="success",
                return_code=proc.returncode,
                finished_at_utc=now_iso(),
            )
        else:
            self._set_fields(
                job_id,
                status="error",
                return_code=proc.returncode,
                error=f"process exited with code {proc.returncode}",
                finished_at_utc=now_iso(),
            )


JOB_MANAGER = JobManager()
ACTION_COMMANDS = action_commands()


class UmaAIHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        if not raw:
            return {}
        return json.loads(raw.decode("utf-8"))

    def _handle_api_get(self, path: str) -> bool:
        if path == "/api/health":
            payload = {
                "ok": True,
                "time_utc": now_iso(),
                "index_exists": INDEX_PATH.exists(),
                "body_metrics_exists": BODY_METRICS_PATH.exists(),
                "actions": sorted(ACTION_COMMANDS.keys()),
            }
            self._send_json(HTTPStatus.OK, payload)
            return True

        if path == "/api/data/index":
            if not INDEX_PATH.exists():
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "uma/index.json not found"})
                return True
            self._send_json(HTTPStatus.OK, {"ok": True, "data": load_json_file(INDEX_PATH)})
            return True

        if path == "/api/data/body-metrics":
            if not BODY_METRICS_PATH.exists():
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "data/body_metrics.json not found"})
                return True
            self._send_json(HTTPStatus.OK, {"ok": True, "data": load_json_file(BODY_METRICS_PATH)})
            return True

        if path == "/api/jobs":
            self._send_json(HTTPStatus.OK, {"ok": True, "jobs": JOB_MANAGER.list_jobs()})
            return True

        if path.startswith("/api/jobs/"):
            job_id = path.rsplit("/", 1)[-1]
            job = JOB_MANAGER.get_job(job_id)
            if job is None:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": f"job not found: {job_id}"})
                return True
            self._send_json(HTTPStatus.OK, {"ok": True, "job": job})
            return True

        return False

    def _handle_api_post(self, path: str) -> bool:
        if not path.startswith("/api/actions/"):
            return False
        action = path.rsplit("/", 1)[-1]
        if action not in ACTION_COMMANDS:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": f"unknown action: {action}"})
            return True
        _ = self._read_json_body()
        job = JOB_MANAGER.start(action, ACTION_COMMANDS[action])
        self._send_json(HTTPStatus.OK, {"ok": True, "job": job})
        return True

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/"):
            if self._handle_api_get(path):
                return
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "api route not found"})
            return

        if path == "/":
            self.path = "/web/index.html"
        super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/"):
            if self._handle_api_post(path):
                return
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "api route not found"})
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"error": "route not found"})


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="UmaAI local server for frontend + data jobs")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host")
    parser.add_argument("--port", type=int, default=8787, help="Bind port")
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), UmaAIHandler)
    print(f"Serving on http://{args.host}:{args.port}")
    print("Actions:", ", ".join(sorted(ACTION_COMMANDS.keys())))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
