
import os
from unittest.mock import MagicMock

import pytest
from arq import Retry
from redis.asyncio import Redis

from app import worker


@pytest.fixture
async def redis_client():
    client = Redis.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        decode_responses=True,
    )
    await client.ping()
    yield client
    await client.aclose()


class FakeSession:
    """Minimal database-session substitute for worker tests."""

    def __init__(self, engine):
        self.engine = engine

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def query(self, model):
        query = MagicMock()
        query.filter.return_value = query

        if model is worker.Connection:
            query.first.return_value = MagicMock(
                id=1,
                user_id=7,
            )
        else:
            query.first.return_value = None

        return query


@pytest.mark.asyncio
async def test_redis_connectivity(redis_client):
    assert await redis_client.ping() is True


@pytest.mark.asyncio
async def test_worker_executes_sync_and_releases_own_lock(
    redis_client, monkeypatch
):
    lock_key = "datasync:sync-lock:1"
    lock_token = "test-lock-token"

    await redis_client.set(lock_key, lock_token)

    monkeypatch.setattr(worker, "Session", FakeSession)
    monkeypatch.setattr(
        worker,
        "get_connection_engines",
        lambda connection_id: (MagicMock(), MagicMock()),
    )

    expected_result = {
        "status": "success",
        "connection_id": 1,
        "inserted_count": 3,
        "updated_count": 0,
        "failed_count": 0,
    }

    monkeypatch.setattr(
        worker,
        "run_sync",
        lambda **kwargs: expected_result,
    )

    result = await worker.sync_connection_job(
        {
            "redis": redis_client,
            "job_try": 1,
            "job_id": "test-job-1",
        },
        connection_id=1,
        user_id=7,
        lock_token=lock_token,
    )

    assert result == expected_result
    assert await redis_client.get(lock_key) is None


@pytest.mark.asyncio
async def test_worker_does_not_delete_another_workers_lock(
    redis_client, monkeypatch
):
    lock_key = "datasync:sync-lock:1"

    await redis_client.set(lock_key, "original-owner")

    monkeypatch.setattr(worker, "Session", FakeSession)
    monkeypatch.setattr(
        worker,
        "get_connection_engines",
        lambda connection_id: (MagicMock(), MagicMock()),
    )
    monkeypatch.setattr(
        worker,
        "run_sync",
        lambda **kwargs: {"status": "success"},
    )

    await worker.sync_connection_job(
        {
            "redis": redis_client,
            "job_try": 1,
            "job_id": "test-job-2",
        },
        connection_id=1,
        user_id=7,
        lock_token="different-owner",
    )

    assert await redis_client.get(lock_key) == "original-owner"


@pytest.mark.asyncio
async def test_worker_requests_retry_after_sync_error(
    redis_client, monkeypatch
):
    lock_key = "datasync:sync-lock:1"
    lock_token = "retry-lock-token"

    await redis_client.set(lock_key, lock_token)

    monkeypatch.setattr(worker, "Session", FakeSession)
    monkeypatch.setattr(
        worker,
        "get_connection_engines",
        lambda connection_id: (MagicMock(), MagicMock()),
    )

    def fail_sync(**kwargs):
        raise RuntimeError("Temporary sync failure")

    monkeypatch.setattr(worker, "run_sync", fail_sync)

    with pytest.raises(Retry):
        await worker.sync_connection_job(
            {
                "redis": redis_client,
                "job_try": 1,
                "job_id": "retry-job",
            },
            connection_id=1,
            user_id=7,
            lock_token=lock_token,
        )

    # The lock should remain while another attempt is expected.
    assert await redis_client.get(lock_key) == lock_token


@pytest.mark.asyncio
async def test_final_failed_attempt_releases_lock(
    redis_client, monkeypatch
):
    lock_key = "datasync:sync-lock:1"
    lock_token = "final-lock-token"

    await redis_client.set(lock_key, lock_token)

    monkeypatch.setattr(worker, "Session", FakeSession)
    monkeypatch.setattr(
        worker,
        "get_connection_engines",
        lambda connection_id: (MagicMock(), MagicMock()),
    )

    def fail_sync(**kwargs):
        raise RuntimeError("Permanent sync failure")

    monkeypatch.setattr(worker, "run_sync", fail_sync)

    with pytest.raises(RuntimeError, match="Permanent sync failure"):
        await worker.sync_connection_job(
            {
                "redis": redis_client,
                "job_try": worker.MAX_TRIES,
                "job_id": "final-failure-job",
            },
            connection_id=1,
            user_id=7,
            lock_token=lock_token,
        )

    assert await redis_client.get(lock_key) is None
