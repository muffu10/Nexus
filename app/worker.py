
import asyncio
import os

from arq import Retry
from arq.connections import RedisSettings
from sqlalchemy.orm import Session

from app.database import datasync_engine
from app.models import Connection
from app.connection_service import get_connection_engines
from app.sync_runner import run_sync


MAX_TRIES = 3

RELEASE_LOCK_SCRIPT = """
if redis.call("GET", KEYS[1]) == ARGV[1] then
    return redis.call("DEL", KEYS[1])
end
return 0
"""


async def sync_connection_job(
    ctx,
    connection_id: int,
    user_id: int,
    lock_token: str,
):
    redis = ctx["redis"]
    lock_key = f"datasync:sync-lock:{connection_id}"
    job_try = ctx.get("job_try", 1)

    # ARQ provides the ID of the currently executing job.
    arq_job_id = ctx.get("job_id")

    source_engine = None
    destination_engine = None
    release_lock = False

    try:
        # Recheck ownership before accessing the connection.
        with Session(datasync_engine) as session:
            connection = (
                session.query(Connection)
                .filter(
                    Connection.id == connection_id,
                    Connection.user_id == user_id,
                )
                .first()
            )

            if connection is None:
                release_lock = True
                return {
                    "status": "cancelled",
                    "connection_id": connection_id,
                }

        # Create the source and destination database engines.
        source_engine, destination_engine = get_connection_engines(
            connection_id
        )

        # run_sync is synchronous, so execute it in a worker thread.
        result = await asyncio.to_thread(
            run_sync,
            datasync_engine=datasync_engine,
            source_engine=source_engine,
            destination_engine=destination_engine,
            connection_id=connection_id,
            arq_job_id=arq_job_id,
        )

        release_lock = True
        return result

    except Exception as exc:
        # Keep the lock while ARQ retries this job.
        if job_try < MAX_TRIES:
            raise Retry(defer=10) from exc

        # The final attempt failed, so release the lock.
        raise

    finally:
        if source_engine is not None:
            source_engine.dispose()

        if destination_engine is not None:
            destination_engine.dispose()

        # Release the lock after success, cancellation, or final failure.
        # The Lua script ensures we only delete our own lock.
        if release_lock or job_try >= MAX_TRIES:
            await redis.eval(
                RELEASE_LOCK_SCRIPT,
                1,
                lock_key,
                lock_token,
            )


class WorkerSettings:
    functions = [sync_connection_job]

    redis_settings = RedisSettings.from_dsn(
        os.getenv("REDIS_URL", "redis://localhost:6379/0")
    )

    max_jobs = 2
    job_timeout = 3600
    max_tries = MAX_TRIES
    keep_result = 3600
