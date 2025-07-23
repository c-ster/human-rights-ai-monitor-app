from motor.motor_asyncio import AsyncIOMotorClient
from .models import DATABASE_URL

class DB:
    client: AsyncIOMotorClient = None

db = DB()

async def get_database_client() -> AsyncIOMotorClient:
    return db.client

async def connect_to_mongo():
    print("Connecting to MongoDB...")
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL not set, cannot connect to MongoDB.")
    db.client = AsyncIOMotorClient(DATABASE_URL)
    print("Successfully connected to MongoDB.")

async def close_mongo_connection():
    print("Closing MongoDB connection...")
    db.client.close()
    print("MongoDB connection closed.")
