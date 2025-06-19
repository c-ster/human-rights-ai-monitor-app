import motor.motor_asyncio
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

client = motor.motor_asyncio.AsyncIOMotorClient(DATABASE_URL)
database = client.human_rights_ai_monitor
content_collection = database.get_collection("content")
