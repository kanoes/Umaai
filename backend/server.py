#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import threading
import uuid
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.job_store import JobStore
from backend.site_data import INDEX_PATH, ROOT, STORE, filter_summaries

BODY_METRICS_PATH = ROOT / "data" / "body_metrics.json"
FRONTEND_INDEX_PATH = ROOT / "static" / "index.html"
JOB_DB_PATH = ROOT / "data" / "umaai_jobs.sqlite3"


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
        "build_site_bundle": [
            py,
            "-m",
            "dataGenerator.build_site_bundle",
            "--output-dir",
            "data",
        ],
    }


class JobManager:
    def __init__(self, store: JobStore) -> None:
        self._store = store
        self._lock = threading.Lock()

    def list_jobs(self) -> list[dict[str, Any]]:
        return self._store.list_jobs(limit=300, with_logs=False)

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        return self._store.get_job(job_id, with_logs=True, log_limit=500)

    def list_failed_jobs(self, *, limit: int = 20) -> list[dict[str, Any]]:
        return self._store.list_failed_jobs(limit=limit)

    def _append_log(self, job_id: str, line: str) -> None:
        self._store.append_log(job_id, line)

    def _set_fields(self, job_id: str, **kwargs: Any) -> None:
        self._store.update_job(job_id, **kwargs)

    def start(self, action: str, command: list[str], *, retried_from_job_id: str | None = None) -> dict[str, Any]:
        job_id = uuid.uuid4().hex[:12]
        created_at_utc = now_iso()
        self._store.create_job(
            job_id=job_id,
            action=action,
            command=command,
            status="queued",
            created_at_utc=created_at_utc,
            retried_from_job_id=retried_from_job_id,
        )

        thread = threading.Thread(target=self._run, args=(job_id,), daemon=True)
        thread.start()
        job = self._store.get_job(job_id, with_logs=True, log_limit=20)
        assert job is not None
        return job

    def retry(self, job_id: str) -> dict[str, Any] | None:
        retry_source = self._store.get_job_command(job_id)
        if retry_source is None:
            return None
        action, command = retry_source
        return self.start(action, command, retried_from_job_id=job_id)

    def _run(self, job_id: str) -> None:
        job = self._store.get_job(job_id, with_logs=False, log_limit=0)
        if job is None:
            return
        command = job["command"]

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
        STORE.invalidate()


JOB_STORE = JobStore(JOB_DB_PATH)
JOB_MANAGER = JobManager(JOB_STORE)
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

    def _send_html(self, status: int, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
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

    def _dataset(self) -> dict[str, Any]:
        return STORE.get()

    def _handle_health(self) -> None:
        self._send_json(
            HTTPStatus.OK,
            {
                "ok": True,
                "time_utc": now_iso(),
                "index_exists": INDEX_PATH.exists(),
                "body_metrics_exists": BODY_METRICS_PATH.exists(),
                "frontend_build_exists": FRONTEND_INDEX_PATH.exists(),
                "actions": sorted(ACTION_COMMANDS.keys()),
            },
        )

    def _handle_site_get(self, path: str, query: dict[str, list[str]]) -> bool:
        dataset = self._dataset()
        if path == "/api/site/overview":
            self._send_json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "overview": dataset["overview"],
                    "stats": dataset["stats"],
                    "filters": dataset.get("manifest", {}).get("filter_meta", {}),
                    "manifest": dataset.get("manifest"),
                    "updated_at_utc": dataset["updated_at_utc"],
                },
            )
            return True

        if path == "/api/site/filter-meta":
            self._send_json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "filters": dataset.get("manifest", {}).get("filter_meta", {}),
                    "manifest": dataset.get("manifest"),
                },
            )
            return True

        if path == "/api/site/characters":
            limit_raw = (query.get("limit") or ["200"])[0]
            offset_raw = (query.get("offset") or ["0"])[0]
            try:
                limit = max(1, min(500, int(limit_raw)))
            except ValueError:
                limit = 200
            try:
                offset = max(0, int(offset_raw))
            except ValueError:
                offset = 0

            query_payload = {key: values[0] for key, values in query.items() if values}
            characters = filter_summaries(dataset, query_payload)
            total = len(characters)
            paged = characters[offset : offset + limit]
            self._send_json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "items": [strip_internal(item) for item in paged],
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                    "query": query_payload.get("query", ""),
                    "applied_filters": query_payload,
                },
            )
            return True

        if path.startswith("/api/site/characters/"):
            slug = path.rsplit("/", 1)[-1]
            detail = dataset["character_lookup"].get(slug)
            if detail is None:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": f"character not found: {slug}"})
                return True
            self._send_json(HTTPStatus.OK, {"ok": True, "item": strip_internal(detail)})
            return True

        if path == "/api/site/rankings":
            self._send_json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "meta": dataset["ranking_meta"],
                    "rankings": dataset["rankings"],
                    "manifest": dataset.get("manifest"),
                },
            )
            return True

        if path == "/api/site/relations":
            self._send_json(HTTPStatus.OK, {"ok": True, "graph": dataset.get("relations", {})})
            return True

        if path == "/api/site/compare":
            raw = (query.get("slugs") or [""])[0]
            slugs = [slug.strip() for slug in raw.split(",") if slug.strip()]
            items = []
            for slug in slugs:
                detail = dataset["character_lookup"].get(slug)
                if detail is not None:
                    items.append(strip_internal(detail))
            self._send_json(HTTPStatus.OK, {"ok": True, "items": items})
            return True

        return False

    def _handle_admin_get(self, path: str) -> bool:
        if path == "/api/admin/overview":
            dataset = self._dataset()
            self._send_json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "stats": dataset["stats"],
                    "updated_at_utc": dataset["updated_at_utc"],
                    "manifest": dataset.get("manifest"),
                    "quality_summary": dataset.get("quality_report", {}).get("summary", {}),
                    "diff_prompt": dataset.get("quality_report", {}).get("stale_prompt"),
                    "actions": sorted(ACTION_COMMANDS.keys()),
                    "jobs": JOB_MANAGER.list_jobs()[:10],
                    "failed_jobs": JOB_MANAGER.list_failed_jobs(limit=8),
                },
            )
            return True

        if path == "/api/admin/quality":
            dataset = self._dataset()
            self._send_json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "report": dataset.get("quality_report", {}),
                    "failed_jobs": JOB_MANAGER.list_failed_jobs(limit=20),
                    "manifest": dataset.get("manifest"),
                },
            )
            return True

        if path == "/api/admin/jobs":
            self._send_json(HTTPStatus.OK, {"ok": True, "jobs": JOB_MANAGER.list_jobs()})
            return True

        if path.startswith("/api/admin/jobs/"):
            job_id = path.rsplit("/", 1)[-1]
            job = JOB_MANAGER.get_job(job_id)
            if job is None:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": f"job not found: {job_id}"})
                return True
            self._send_json(HTTPStatus.OK, {"ok": True, "job": job})
            return True

        return False

    def _handle_legacy_get(self, path: str) -> bool:
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

    def _handle_api_get(self, path: str, query: dict[str, list[str]]) -> bool:
        if path == "/api/health":
            self._handle_health()
            return True
        if self._handle_site_get(path, query):
            return True
        if self._handle_admin_get(path):
            return True
        if self._handle_legacy_get(path):
            return True
        return False

    def _handle_api_post(self, path: str) -> bool:
        if path.startswith("/api/admin/jobs/") and path.endswith("/retry"):
            job_id = path.split("/")[-2]
            retried_job = JOB_MANAGER.retry(job_id)
            if retried_job is None:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": f"job not found: {job_id}"})
                return True
            self._send_json(HTTPStatus.OK, {"ok": True, "job": retried_job})
            return True

        if path.startswith("/api/actions/"):
            action = path.rsplit("/", 1)[-1]
        elif path.startswith("/api/admin/actions/"):
            action = path.rsplit("/", 1)[-1]
        else:
            return False

        if action not in ACTION_COMMANDS:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": f"unknown action: {action}"})
            return True

        _ = self._read_json_body()
        job = JOB_MANAGER.start(action, ACTION_COMMANDS[action])
        self._send_json(HTTPStatus.OK, {"ok": True, "job": job})
        return True

    def _serve_frontend(self, path: str) -> None:
        if path.startswith("/static/") or path.startswith("/uma/"):
            super().do_GET()
            return

        if not FRONTEND_INDEX_PATH.exists():
            self._send_html(
                HTTPStatus.SERVICE_UNAVAILABLE,
                (
                    "<!doctype html><html><body style='font-family:sans-serif;padding:24px'>"
                    "<h1>Frontend build not found</h1>"
                    "<p>Run <code>cd frontend && npm install && npm run build</code> first.</p>"
                    "</body></html>"
                ),
            )
            return

        requested = ROOT / path.lstrip("/")
        if requested.exists() and requested.is_file():
            super().do_GET()
            return

        self.path = "/static/index.html"
        super().do_GET()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/"):
            if self._handle_api_get(path, parse_qs(parsed.query)):
                return
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "api route not found"})
            return
        self._serve_frontend(path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/"):
            if self._handle_api_post(path):
                return
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "api route not found"})
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"error": "route not found"})

    def do_HEAD(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/"):
            self.send_response(HTTPStatus.METHOD_NOT_ALLOWED)
            self.end_headers()
            return

        if path.startswith("/static/") or path.startswith("/uma/"):
            super().do_HEAD()
            return

        if not FRONTEND_INDEX_PATH.exists():
            self.send_response(HTTPStatus.SERVICE_UNAVAILABLE)
            self.end_headers()
            return

        requested = ROOT / path.lstrip("/")
        if requested.exists() and requested.is_file():
            super().do_HEAD()
            return

        self.path = "/static/index.html"
        super().do_HEAD()


def strip_internal(item: dict[str, Any]) -> dict[str, Any]:
    payload = dict(item)
    payload.pop("search_blob", None)
    payload.pop("latest_outfit_at_ts", None)
    return payload


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Umaai local server for public site, admin, and data jobs")
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
        JOB_STORE.close()


if __name__ == "__main__":
    main()
