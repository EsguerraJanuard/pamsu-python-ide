"""Judge0 dispatch reuses one SSL context per worker process (2026-10-28).

Alpha tester: "slight delays when running Python code". Building a new
httpx client loads the CA bundle into a new SSL context, about 0.4 s of CPU
on every run (more on Render's shared CPU). The worker now makes the
context once per process and still opens a fresh connection per call.
"""

import httpx
import pytest

from app.tasks import celery_worker


@pytest.fixture
def counted_contexts(monkeypatch):
    made = []
    real = httpx.create_ssl_context

    def create_ssl_context(*args, **kwargs):
        context = real(*args, **kwargs)
        made.append(context)
        return context

    monkeypatch.setattr(httpx, "create_ssl_context", create_ssl_context)
    monkeypatch.setattr(celery_worker, "_judge0_ssl_context", None)
    monkeypatch.setattr(celery_worker, "_judge0_ssl_context_pid", None)
    return made


def test_clients_share_one_ssl_context(counted_contexts):
    with celery_worker.judge0_http_client() as first, celery_worker.judge0_http_client() as second:
        assert first is not second  # a new client (and connection) per call
        assert first.timeout == httpx.Timeout(10.0)

    assert len(counted_contexts) == 1


def test_a_forked_worker_process_makes_its_own_context(counted_contexts, monkeypatch):
    celery_worker.judge0_http_client().close()
    monkeypatch.setattr(celery_worker.os, "getpid", lambda: -12345)
    celery_worker.judge0_http_client().close()

    assert len(counted_contexts) == 2


def test_the_context_is_ready_when_the_worker_process_starts(counted_contexts):
    celery_worker._prepare_judge0_ssl_context()
    celery_worker.judge0_http_client().close()

    assert len(counted_contexts) == 1


def test_a_failing_warm_up_does_not_stop_the_worker(counted_contexts, monkeypatch):
    def broken(*args, **kwargs):
        raise OSError("no CA bundle")

    monkeypatch.setattr(httpx, "create_ssl_context", broken)

    celery_worker._prepare_judge0_ssl_context()  # logged, not raised
