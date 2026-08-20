"""MongoDB connection configuration."""

import os

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.database import Database

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "")
DB_NAME = os.getenv("DB_NAME", "")

client = MongoClient(MONGO_URI) if MONGO_URI else None
db: Database | None = client[DB_NAME] if client and DB_NAME else None


def get_database() -> Database | None:
    # TODO: Provide the configured MongoDB database to application dependencies.
    pass
