import tempfile
import unittest
from pathlib import Path

from backend.job_store import JobStore


class JobStoreTests(unittest.TestCase):
    def test_job_and_logs_are_persisted(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "jobs.sqlite3"
            store = JobStore(db_path)
            try:
                store.create_job(
                    job_id="job-1",
                    action="build_site_bundle",
                    command=["python3", "-m", "dataGenerator.build_site_bundle"],
                    status="queued",
                    created_at_utc="2026-03-11T00:00:00+00:00",
                )
                store.append_log("job-1", "line-1\n")
                store.update_job("job-1", status="success", finished_at_utc="2026-03-11T00:00:05+00:00")

                payload = store.get_job("job-1")
                assert payload is not None
                self.assertEqual(payload["status"], "success")
                self.assertEqual(payload["logs"], ["line-1"])
            finally:
                store.close()

            reopened = JobStore(db_path)
            try:
                payload = reopened.get_job("job-1")
                assert payload is not None
                self.assertEqual(payload["action"], "build_site_bundle")
                self.assertEqual(payload["logs"], ["line-1"])
            finally:
                reopened.close()

    def test_incomplete_jobs_become_error_after_restart(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "jobs.sqlite3"
            store = JobStore(db_path)
            try:
                store.create_job(
                    job_id="job-2",
                    action="fetch_info",
                    command=["python3", "-m", "dataFetcher.fetch_uma_info"],
                    status="running",
                    created_at_utc="2026-03-11T00:00:00+00:00",
                )
            finally:
                store.close()

            reopened = JobStore(db_path)
            try:
                payload = reopened.get_job("job-2")
                assert payload is not None
                self.assertEqual(payload["status"], "error")
                self.assertIn("server restarted", payload["error"])
            finally:
                reopened.close()


if __name__ == "__main__":
    unittest.main()
