from datetime import datetime, timezone
from arq.jobs import Job, JobStatus

import os
import uuid

from arq import create_pool
from arq.connections import RedisSettings



from sqlalchemy import text, create_engine, inspect

from app.sync_runner import run_sync

from fastapi.middleware.cors import CORSMiddleware

from fastapi import FastAPI, HTTPException

from pydantic import BaseModel

from sqlalchemy.orm import Session

from app.auth import hash_password

import json





from fastapi import Depends

from fastapi.security import (
    OAuth2PasswordBearer,
    OAuth2PasswordRequestForm,
)



from app.auth import (

    create_access_token,

    decode_access_token,

    hash_password,

    verify_password,

)

from app.models import User



from app.database import (

    source_engine,

    destination_engine,

    datasync_engine,

)



from app.models import (

    Base,

    User,

    Connection,

    ConnectionCredential,

    FieldMapping,

    MappingSuggestion,

    SyncRun,

    SyncError,

)



from app.schema_inspector import get_database_schema

from app.mapping_engine import suggest_mappings

from app.sync_service import sync_table



from app.connection_service import (

    test_database_connection,

    get_connection_engines,

)



from app.security import encrypt_value

from app.data_sampler import sample_table



from app.sync_status import (

    SYNC_RUNNING,

    SYNC_SUCCESS,

    SYNC_COMPLETED_WITH_ERRORS,

    SYNC_FAILED,

)





class RegisterRequest(BaseModel):

    username: str

    email: str

    password: str


class LoginRequest(BaseModel):
    email: str
    password: str





class ConnectionCreate(BaseModel):

    name: str

    source_type: str

    source_url: str

    destination_type: str

    destination_url: str

    source_table: str

    destination_table: str


class ConnectionTestRequest(BaseModel):
    source_type: str
    source_url: str
    destination_type: str
    destination_url: str



app = FastAPI(title="DataSync")

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/token"
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
):
    try:
        user_id = decode_access_token(token)
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token.",
        )

    with Session(datasync_engine) as session:
        user = session.get(User, user_id)

        if not user:
            raise HTTPException(
                status_code=401,
                detail="User not found.",
            )

        return user


def get_owned_connection(
    session,
    connection_id: int,
    user_id: int,
):
    connection = (
        session.query(Connection)
        .filter(
            Connection.id == connection_id,
            Connection.user_id == user_id,
        )
        .first()
    )

    if not connection:
        raise HTTPException(
            status_code=404,
            detail="Connection not found.",
        )

    return connection



app.add_middleware(

    CORSMiddleware,

    allow_origins=[

        "http://localhost:5173",

        "http://127.0.0.1:5173",

    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],

)





@app.get("/health")

def health_check():

    return {"status": "healthy"}




@app.get(

    "/connections/{connection_id}/mapping-suggestions"

)

def get_mapping_suggestions(
    connection_id: int,
    current_user: User = Depends(get_current_user),
):

    with Session(datasync_engine) as session:



        connection = get_owned_connection(
            session,
            connection_id,
            current_user.id,
        )



        if not connection:

            raise HTTPException(

                status_code=404,

                detail="Connection not found.",

            )



        source_table = connection.source_table

        destination_table = connection.destination_table



    source_engine_for_connection = None

    destination_engine_for_connection = None



    try:



        source_engine_for_connection, destination_engine_for_connection = (

            get_connection_engines(

                connection_id

            )

        )



        source_schema = get_database_schema(

            source_engine_for_connection

        )



        destination_schema = get_database_schema(

            destination_engine_for_connection

        )



        if source_table not in source_schema:

            raise HTTPException(

                status_code=404,

                detail=(

                    "Source table not found: "

                    f"{source_table}"

                ),

            )



        if destination_table not in destination_schema:

            raise HTTPException(

                status_code=404,

                detail=(

                    "Destination table not found: "

                    f"{destination_table}"

                ),

            )



        source_columns = source_schema[

            source_table

        ]



        destination_columns = destination_schema[

            destination_table

        ]



        source_samples = sample_table(

            source_engine_for_connection,

            source_table,

            source_columns,

        )



        destination_samples = sample_table(

            destination_engine_for_connection,

            destination_table,

            destination_columns,

        )



        mappings = suggest_mappings(

            source_columns,

            destination_columns,

            source_samples,

            destination_samples,

        )



        with Session(datasync_engine) as session:



            # Mark previous pending suggestions as

            # superseded instead of deleting them.

            session.query(

                MappingSuggestion

            ).filter(

                MappingSuggestion.connection_id

                == connection_id,

                MappingSuggestion.review_status

                == "pending",

            ).update(

                {

                    MappingSuggestion.review_status:

                        "superseded",

                    MappingSuggestion.reviewed_at:

                        datetime.now(timezone.utc),

                },

                synchronize_session=False,

            )



            # Get mappings that the user has already

            # approved.

            approved_mappings = (

                session.query(FieldMapping)

                .filter(

                    FieldMapping.connection_id

                    == connection_id

                )

                .all()

            )



            approved_pairs = {

                (

                    mapping.source_field,

                    mapping.destination_field,

                )

                for mapping in approved_mappings

            }



            saved_suggestions = []



            for mapping in mappings:



                pair = (

                    mapping["source"],

                    mapping["destination"],

                )



                # Do not suggest something that has

                # already been approved.

                if pair in approved_pairs:

                    continue



                suggestion = MappingSuggestion(

                    connection_id=connection_id,

                    source_field=mapping["source"],

                    destination_field=mapping[

                        "destination"

                    ],

                    confidence=mapping[

                        "confidence"

                    ],

                    margin=mapping[

                        "margin"

                    ],

                    match_status=mapping[

                        "match_status"

                    ],

                    signals=json.dumps(

                        mapping["signals"]

                    ),

                    review_status="pending",

                )



                session.add(suggestion)

                session.flush()



                saved_suggestions.append(

                    {

                        "id": suggestion.id,

                        "source": mapping[

                            "source"

                        ],

                        "destination": mapping[

                            "destination"

                        ],

                        "confidence": mapping[

                            "confidence"

                        ],

                        "margin": mapping[

                            "margin"

                        ],

                        "match_status": mapping[

                            "match_status"

                        ],

                        "review_status": (

                            suggestion.review_status

                        ),

                        "signals": mapping[

                            "signals"

                        ],

                    }

                )



            session.commit()



        return {

            "connection_id": connection_id,

            "source_table": source_table,

            "destination_table": destination_table,

            "source_samples": source_samples,

            "destination_samples": (

                destination_samples

            ),

            "mappings": saved_suggestions,

        }



    finally:



        if source_engine_for_connection:

            source_engine_for_connection.dispose()



        if destination_engine_for_connection:

            destination_engine_for_connection.dispose()





@app.post(

    "/mapping-suggestions/{suggestion_id}/approve"

)

def approve_mapping_suggestion(
    suggestion_id: int,
    current_user: User = Depends(get_current_user),
):

    with Session(datasync_engine) as session:



        suggestion = (

            session.query(

                MappingSuggestion

            )

            .filter(

                MappingSuggestion.id

                == suggestion_id

            )

            .first()

        )



        if not suggestion:

            raise HTTPException(

                status_code=404,

                detail=(

                    "Mapping suggestion not found."

                ),

            )



        if suggestion.review_status != "pending":

            raise HTTPException(

                status_code=400,

                detail=(

                    "This mapping suggestion has "

                    "already been reviewed."

                ),

            )



        connection = get_owned_connection(
            session,
            suggestion.connection_id,
            current_user.id,
        )



        if not connection:

            raise HTTPException(

                status_code=404,

                detail="Connection not found.",

            )



        existing_mapping = (

            session.query(FieldMapping)

            .filter(

                FieldMapping.connection_id

                == suggestion.connection_id,

                FieldMapping.source_field

                == suggestion.source_field,

                FieldMapping.destination_field

                == suggestion.destination_field,

            )

            .first()

        )



        if existing_mapping:



            suggestion.review_status = "approved"

            suggestion.reviewed_at = (

                datetime.now(timezone.utc)

            )



            session.commit()



            return {

                "message": (

                    "Mapping was already approved."

                ),

                "mapping": {

                    "id": existing_mapping.id,

                    "connection_id": (

                        existing_mapping.connection_id

                    ),

                    "source": (

                        existing_mapping.source_field

                    ),

                    "destination": (

                        existing_mapping.destination_field

                    ),

                },

            }



        mapping = FieldMapping(

            connection_id=(

                suggestion.connection_id

            ),

            source_field=(

                suggestion.source_field

            ),

            destination_field=(

                suggestion.destination_field

            ),

        )



        session.add(mapping)



        suggestion.review_status = "approved"

        suggestion.reviewed_at = (

            datetime.now(timezone.utc)

        )



        session.commit()

        session.refresh(mapping)



        return {

            "message": (

                "Mapping approved successfully."

            ),

            "mapping": {

                "id": mapping.id,

                "connection_id": (

                    mapping.connection_id

                ),

                "source": (

                    mapping.source_field

                ),

                "destination": (

                    mapping.destination_field

                ),

            },

        }



@app.post("/connections/test")
def test_connection(
    data: ConnectionTestRequest,
    current_user: User = Depends(get_current_user),
):
    if data.source_type.lower() != "postgresql":
        raise HTTPException(
            status_code=400,
            detail="Only PostgreSQL is currently supported.",
        )

    if data.destination_type.lower() != "postgresql":
        raise HTTPException(
            status_code=400,
            detail="Only PostgreSQL is currently supported.",
        )

    source_engine_for_test = None
    destination_engine_for_test = None

    try:
        # Test source
        source_engine_for_test = create_engine(
            data.source_url,
            pool_pre_ping=True,
        )

        with source_engine_for_test.connect() as connection:
            connection.execute(text("SELECT 1"))

        # Test destination
        destination_engine_for_test = create_engine(
            data.destination_url,
            pool_pre_ping=True,
        )

        with destination_engine_for_test.connect() as connection:
            connection.execute(text("SELECT 1"))

        # Get available tables
        source_tables = inspect(
            source_engine_for_test
        ).get_table_names()

        destination_tables = inspect(
            destination_engine_for_test
        ).get_table_names()

        return {
            "source_connection": "successful",
            "destination_connection": "successful",
            "source_tables": sorted(source_tables),
            "destination_tables": sorted(destination_tables),
        }

    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail=f"Database connection failed: {error}",
        )

    finally:
        if source_engine_for_test:
            source_engine_for_test.dispose()

        if destination_engine_for_test:
            destination_engine_for_test.dispose()



@app.post("/connections")
def create_connection(
    data: ConnectionCreate,
    current_user: User = Depends(get_current_user),
):

    # Test source database
    source_connected = test_database_connection(
        data.source_url
    )

    if not source_connected:
        raise HTTPException(
            status_code=400,
            detail=(
                "Could not connect to source "
                "database."
            ),
        )

    # Test destination database
    destination_connected = test_database_connection(
        data.destination_url
    )

    if not destination_connected:
        raise HTTPException(
            status_code=400,
            detail=(
                "Could not connect to destination "
                "database."
            ),
        )

    # Both databases are reachable.
    # Now encrypt the credentials.
    encrypted_source_url = encrypt_value(
        data.source_url
    )

    encrypted_destination_url = encrypt_value(
        data.destination_url
    )

    with Session(datasync_engine) as session:

        # Get the next connection number
        # for this user only.
        last_connection = (
            session.query(
                Connection.connection_number
            )
            .filter(
                Connection.user_id == current_user.id
            )
            .order_by(
                Connection.connection_number.desc()
            )
            .first()
        )

        next_connection_number = (
            last_connection[0] + 1
            if last_connection
            else 1
        )

        connection = Connection(
            user_id=current_user.id,
            connection_number=next_connection_number,
            name=data.name,
            source_type=data.source_type,
            destination_type=data.destination_type,
            source_table=data.source_table,
            destination_table=data.destination_table,
        )

        session.add(connection)
        session.flush()

        credentials = ConnectionCredential(
            connection_id=connection.id,
            encrypted_source_url=encrypted_source_url,
            encrypted_destination_url=(
                encrypted_destination_url
            ),
        )

        session.add(credentials)
        session.commit()
        session.refresh(connection)

        return {
            "id": connection.id,
            "connection_number": (
                connection.connection_number
            ),
            "name": connection.name,
            "source_type": connection.source_type,
            "destination_type": (
                connection.destination_type
            ),
            "source_table": (
                connection.source_table
            ),
            "destination_table": (
                connection.destination_table
            ),
            "source_connection": "successful",
            "destination_connection": "successful",
        }





@app.get("/connections/{connection_id}/samples")

def get_connection_samples(
    connection_id: int,
    current_user: User = Depends(get_current_user),
):

    with Session(datasync_engine) as session:

        connection = get_owned_connection(
            session,
            connection_id,
            current_user.id,
        )



        if not connection:

            raise HTTPException(

                status_code=404,

                detail="Connection not found",

            )



        source_table = connection.source_table

        destination_table = connection.destination_table



    try:

        source_engine, destination_engine = (

            get_connection_engines(connection_id)

        )



        def get_samples(engine, table_name):

            query = text(

                f'''

                SELECT *

                FROM "{table_name}"

                LIMIT 5

                '''

            )



            with engine.connect() as db_connection:

                result = db_connection.execute(query)



                rows = [

                    dict(row._mapping)

                    for row in result

                ]



            samples = {}



            for row in rows:

                for column, value in row.items():

                    samples.setdefault(column, [])



                    if value not in samples[column]:

                        samples[column].append(value)



            return samples



        source_samples = get_samples(

            source_engine,

            source_table,

        )



        destination_samples = get_samples(

            destination_engine,

            destination_table,

        )



        source_engine.dispose()

        destination_engine.dispose()



        return {

            "source": source_samples,

            "destination": destination_samples,

        }



    except Exception as error:

        raise HTTPException(

            status_code=500,

            detail=str(error),

        )





@app.get("/connections")

def get_connections(
    current_user: User = Depends(get_current_user),
):

    with Session(datasync_engine) as session:

        connections = (

            session.query(Connection)
            .filter(Connection.user_id == current_user.id)
            .order_by(Connection.id.desc())
            .all()

        )



        return [

            {

                "id": connection.id,

                "connection_number": connection.connection_number,

                "name": connection.name,

                "source_type": connection.source_type,

                "destination_type": connection.destination_type,

                "source_table": connection.source_table,

                "destination_table": connection.destination_table,

                "created_at": connection.created_at,

            }

            for connection in connections

        ]







@app.get(

    "/connections/{connection_id}/schema"

)

def get_connection_schema(
    connection_id: int,
    current_user: User = Depends(get_current_user),
):



    try:

        with Session(datasync_engine) as session:
            connection = get_owned_connection(
                session,
                connection_id,
                current_user.id,
            )


        source_engine_for_connection, destination_engine_for_connection = (

            get_connection_engines(

                connection_id

            )

        )



    except ValueError as error:



        raise HTTPException(

            status_code=404,

            detail=str(error),

        )



    try:



        source_schema = get_database_schema(

            source_engine_for_connection

        )



        destination_schema = get_database_schema(

            destination_engine_for_connection

        )



        return {
            "connection_id": connection_id,
            "source_table": connection.source_table,
            "destination_table": connection.destination_table,
            "source": source_schema,
            "destination": destination_schema,
        }



    finally:



        source_engine_for_connection.dispose()

        destination_engine_for_connection.dispose()







@app.post("/connections/{connection_id}/sync")
async def sync_connection(
    connection_id: int,
    current_user: User = Depends(get_current_user),
):
    # Check that this connection belongs to the logged-in user.
    with Session(datasync_engine) as session:
        get_owned_connection(
            session,
            connection_id,
            current_user.id,
        )

    redis = None
    lock_key = f"datasync:sync-lock:{connection_id}"
    lock_token = uuid.uuid4().hex

    try:
        redis = await create_pool(
            RedisSettings.from_dsn(
                os.getenv(
                    "REDIS_URL",
                    "redis://localhost:6379/0",
                )
            )
        )

        # Acquire the lock only if no sync already owns it.
        acquired = await redis.set(
            lock_key,
            lock_token,
            nx=True,
            ex=7200,
        )

        if not acquired:
            raise HTTPException(
                status_code=409,
                detail="A synchronization job is already queued or running for this connection.",
            )

        try:
            job = await redis.enqueue_job(
                "sync_connection_job",
                connection_id,
                current_user.id,
                lock_token,
                _job_id=f"sync-{uuid.uuid4().hex}",
            )

            if job is None:
                raise RuntimeError(
                    "ARQ did not enqueue the synchronization job."
                )

        except Exception:
            # Release only our own lock if enqueueing fails.
            await redis.eval(
                """
                if redis.call("GET", KEYS[1]) == ARGV[1] then
                    return redis.call("DEL", KEYS[1])
                end
                return 0
                """,
                1,
                lock_key,
                lock_token,
            )
            raise

        return {
            "status": "queued",
            "connection_id": connection_id,
            "job_id": job.job_id,
            "message": "Synchronization job queued successfully.",
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Unable to queue synchronization. Check that Redis is running.",
        )

    finally:
        if redis is not None:
            await redis.aclose()








@app.post(
    "/connections/{connection_id}/sync-runs/{sync_run_id}/retry"
)
async def retry_sync(
    connection_id: int,
    sync_run_id: int,
    current_user: User = Depends(get_current_user),
):
    # Verify ownership and ensure this run can be retried.
    with Session(datasync_engine) as session:
        get_owned_connection(
            session,
            connection_id,
            current_user.id,
        )

        sync_run = (
            session.query(SyncRun)
            .filter(
                SyncRun.id == sync_run_id,
                SyncRun.connection_id == connection_id,
            )
            .first()
        )

        if not sync_run:
            raise HTTPException(
                status_code=404,
                detail="Sync run not found for this connection.",
            )

        if sync_run.status not in {
            SYNC_FAILED,
            SYNC_COMPLETED_WITH_ERRORS,
        }:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Only failed or completed_with_errors "
                    "sync runs can be retried."
                ),
            )

    redis = None
    lock_key = f"datasync:sync-lock:{connection_id}"
    lock_token = uuid.uuid4().hex

    try:
        redis = await create_pool(
            RedisSettings.from_dsn(
                os.getenv(
                    "REDIS_URL",
                    "redis://localhost:6379/0",
                )
            )
        )

        acquired = await redis.set(
            lock_key,
            lock_token,
            nx=True,
            ex=7200,
        )

        if not acquired:
            raise HTTPException(
                status_code=409,
                detail=(
                    "A synchronization job is already "
                    "queued or running for this connection."
                ),
            )

        try:
            job = await redis.enqueue_job(
                "sync_connection_job",
                connection_id,
                current_user.id,
                lock_token,
                _job_id=f"sync-{uuid.uuid4().hex}",
            )

            if job is None:
                raise RuntimeError(
                    "ARQ did not enqueue the retry job."
                )

        except Exception:
            await redis.eval(
                """
                if redis.call("GET", KEYS[1]) == ARGV[1] then
                    return redis.call("DEL", KEYS[1])
                end
                return 0
                """,
                1,
                lock_key,
                lock_token,
            )
            raise

        return {
            "status": "queued",
            "connection_id": connection_id,
            "job_id": job.job_id,
            "retry_of_sync_run_id": sync_run_id,
            "message": "Retry job queued successfully.",
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=503,
            detail=(
                "Unable to queue retry. "
                "Check that Redis is running."
            ),
        )

    finally:
        if redis is not None:
            await redis.aclose()





@app.get(

    "/connections/{connection_id}/sync-runs"

)

def get_sync_runs(
    connection_id: int,
    current_user: User = Depends(get_current_user),
):



    with Session(datasync_engine) as session:



        connection = get_owned_connection(
            session,
            connection_id,
            current_user.id,
        )



        if not connection:

            raise HTTPException(

                status_code=404,

                detail="Connection not found.",

            )



        sync_runs = (

            session.query(SyncRun)

            .filter(

                SyncRun.connection_id

                == connection_id

            )

            .order_by(

                SyncRun.started_at.desc()

            )

            .all()

        )



        return {

            "connection_id": connection_id,

            "sync_runs": [

                {

                    "id": sync_run.id,

                    "status": sync_run.status,

                    "started_at": sync_run.started_at,

                    "finished_at": sync_run.finished_at,

                    "inserted_count": (

                        sync_run.inserted_count

                    ),

                    "updated_count": (

                        sync_run.updated_count

                    ),

                    "failed_count": (

                        sync_run.failed_count

                    ),

                    "error_message": (

                        sync_run.error_message

                    ),

                }

                for sync_run in sync_runs

            ],

        }



@app.get("/connections/{connection_id}/sync-jobs/{job_id}")
async def get_sync_job_status(
    connection_id: int,
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    # Ensure the connection belongs to the logged-in user.
    with Session(datasync_engine) as session:
        get_owned_connection(
            session,
            connection_id,
            current_user.id,
        )

    redis = None

    try:
        redis = await create_pool(
            RedisSettings.from_dsn(
                os.getenv(
                    "REDIS_URL",
                    "redis://localhost:6379/0",
                )
            )
        )

        job = Job(job_id, redis)

        # Retrieve the job definition to verify its ownership.
        job_info = await job.info()

        if job_info is None:
            return {
                "job_id": job_id,
                "connection_id": connection_id,
                "status": "not_found",
                "message": (
                    "The job was not found in ARQ's "
                    "available job records."
                ),
            }

        # ARQ stores the positional arguments used to enqueue
        # the job. Verify the connection and user IDs.
        job_args = job_info.args

        if (
            len(job_args) < 2
            or job_args[0] != connection_id
            or job_args[1] != current_user.id
        ):
            raise HTTPException(
                status_code=404,
                detail="Job not found for this connection.",
            )

        job_status = await job.status()

        status_map = {
            JobStatus.queued: "queued",
            JobStatus.in_progress: "running",
            JobStatus.complete: "complete",
            JobStatus.not_found: "not_found",
        }

        return {
            "job_id": job_id,
            "connection_id": connection_id,
            "status": status_map.get(
                job_status,
                str(job_status),
            ),
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Unable to retrieve job status from Redis.",
        )

    finally:
        if redis is not None:
            await redis.aclose()






@app.post("/auth/token")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    with Session(datasync_engine) as session:

        user = (
            session.query(User)
            .filter(
                User.email == form_data.username
            )
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password.",
            )

        if not verify_password(
            form_data.password,
            user.password_hash,
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password.",
            )

        access_token = create_access_token(
            user.id
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
        }

@app.post("/auth/register")

def register_user(request: RegisterRequest):

    with Session(datasync_engine) as session:

        existing_user = (

            session.query(User)

            .filter(

                (User.username == request.username)

                | (User.email == request.email)

            )

            .first()

        )



        if existing_user:

            raise HTTPException(

                status_code=400,

                detail="Username or email already exists.",

            )



        user = User(

            username=request.username,

            email=request.email,

            password_hash=hash_password(request.password),

        )



        session.add(user)

        session.commit()

        session.refresh(user)



        access_token = create_access_token(user.id)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            },
        }


@app.post("/auth/login")
def login_user(request: LoginRequest):
    with Session(datasync_engine) as session:
        user = (
            session.query(User)
            .filter(User.email == request.email)
            .first()
        )

        if user is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password.",
            )

        if not verify_password(
            request.password,
            user.password_hash,
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password.",
            )

        access_token = create_access_token(user.id)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            },
        }


@app.get("/auth/me")
def get_me(
    current_user: User = Depends(get_current_user),
):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
    }


@app.delete("/connections/{connection_id}")
def delete_connection(
    connection_id: int,
    current_user: User = Depends(get_current_user),
):
    with Session(datasync_engine) as session:
        connection = get_owned_connection(
            session,
            connection_id,
            current_user.id,
        )

        session.delete(connection)
        session.commit()

        return {
            "message": "Connection deleted successfully.",
            "connection_id": connection_id,
        }