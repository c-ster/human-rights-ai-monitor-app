import os
from fastapi import FastAPI, HTTPException
from typing import List
from . import pipeline
from .db import content_collection, client
from .models import Content

app = FastAPI(
    title="Human Rights & AI Monitor",
    description="A service to discover, summarize, and prioritize content on AI and human rights.",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_db_client():
    # This is where you might want to add a check to ensure db connection is alive
    pass

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

@app.get("/")
async def root():
    return {"message": "Welcome to the Human Rights & AI Monitor API"}

@app.post("/pipeline/run")
async def run_pipeline_endpoint():
    """
    Triggers the content discovery pipeline to fetch new content from all sources.
    """
    try:
        result = await pipeline.fetch_and_store_feeds()
        return result
    except Exception as e:
        print(f"Error running pipeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/content", response_model=List[Content])
async def list_content():
    """
    A test endpoint to retrieve the 10 most recent content entries from the database.
    """
    try:
        contents = await content_collection.find().sort("created_at", -1).limit(10).to_list(10)
        return contents
    except Exception as e:
        print(f"Error fetching content: {e}")
        raise HTTPException(status_code=500, detail=str(e))
