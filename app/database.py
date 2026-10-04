import os

from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

SOURCE_DATABASE_URL = os.getenv("SOURCE_DATABASE_URL")
DESTINATION_DATABASE_URL = os.getenv("DESTINATION_DATABASE_URL")
DATASYNC_DATABASE_URL = os.getenv("DATASYNC_DATABASE_URL")

source_engine = create_engine(SOURCE_DATABASE_URL)
destination_engine = create_engine(DESTINATION_DATABASE_URL)
datasync_engine = create_engine(DATASYNC_DATABASE_URL)