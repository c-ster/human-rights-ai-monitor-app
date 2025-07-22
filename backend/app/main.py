import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from . import pipeline
from .db import content_collection, client
from .models import Content, ContentStatus
from bson import ObjectId
from datetime import datetime

app = FastAPI(
    title="Human Rights & AI Monitor API"
)

# CORS Middleware
origins = [
    "http://localhost:5173", # Vite default port
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.description = "A service to discover, summarize, and prioritize content on AI and human rights."
app.version = "1.0.0"

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


@app.post("/content/approve-latest")
async def approve_latest_content():
    """
    A temporary endpoint to approve the 10 most recent pending articles.
    This helps in testing the main dashboard without manual curation.
    """
    try:
        # Find the 10 most recent pending articles
        pending_articles = await content_collection.find(
            {"status": "pending"}
        ).sort("created_at", -1).limit(10).to_list(10)

        if not pending_articles:
            return {"status": "noop", "message": "No pending articles to approve."}

        # Get the IDs of these articles
        article_ids = [article['_id'] for article in pending_articles]

        # Update their status to 'approved'
        result = await content_collection.update_many(
            {"_id": {"$in": article_ids}},
            {"$set": {"status": "approved", "updated_at": datetime.now()}}
        )

        return {"status": "success", "message": f"{result.modified_count} articles approved."}

    except Exception as e:
        print(f"Error approving latest content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

@app.post("/pipeline/run-complete")
async def run_complete_pipeline_endpoint():
    """
    Triggers the complete content pipeline including RSS, academic, and podcast sources.
    """
    try:
        result = await pipeline.run_complete_pipeline()
        return result
    except Exception as e:
        print(f"Error running complete pipeline: {e}")
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

# Human Curation Models
class CurationAction(BaseModel):
    content_id: str
    action: str  # "approve", "reject", "edit"
    editor_notes: Optional[str] = None
    edited_summary: Optional[str] = None
    edited_title: Optional[str] = None

class FeedbackSubmission(BaseModel):
    content_id: str
    is_helpful: bool
    comments: Optional[str] = None

# Human Curation Endpoints
@app.get("/content/pending", response_model=List[Content])
async def get_pending_content(limit: int = Query(20, ge=1, le=100)):
    """
    Retrieves content that is pending human curation review.
    """
    try:
        contents = await content_collection.find(
            {"status": "pending"}
        ).sort("created_at", -1).limit(limit).to_list(limit)
        return contents
    except Exception as e:
        print(f"Error fetching pending content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/content/curate")
async def curate_content(action: CurationAction):
    """
    Allows human curators to approve, reject, or edit content.
    """
    try:
        content_id = ObjectId(action.content_id)
        
        # Find the content
        content = await content_collection.find_one({"_id": content_id})
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        update_data = {
            "updated_at": datetime.now(),
            "editor_notes": action.editor_notes
        }
        
        if action.action == "approve":
            update_data["status"] = "approved"
        elif action.action == "reject":
            update_data["status"] = "rejected"
        elif action.action == "edit":
            update_data["status"] = "approved"
            if action.edited_summary:
                update_data["summary"] = [action.edited_summary]
            if action.edited_title:
                update_data["title"] = action.edited_title
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
        
        # Update the content
        result = await content_collection.update_one(
            {"_id": content_id},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=500, detail="Failed to update content")
        
        return {"status": "success", "message": f"Content {action.action}d successfully"}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid content ID")
    except Exception as e:
        print(f"Error curating content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/content/status-counts")
async def get_status_counts():
    """
    A diagnostic endpoint to get the count of content items by status.
    """
    try:
        pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        counts = await content_collection.aggregate(pipeline).to_list(None)
        return {item['_id']: item['count'] for item in counts}
    except Exception as e:
        print(f"Error getting status counts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/content/approved", response_model=List[Content])
async def get_approved_content(
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None)
):
    """
    Retrieves approved content for public display.
    """
    try:
        find_filter = {"status": "approved"}
        if category:
            find_filter["category"] = category

        contents = await content_collection.find(
            find_filter
        ).sort("published_at", -1).limit(limit).to_list(limit)
        return contents
    except Exception as e:
        print(f"Error fetching approved content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/content/feedback")
async def submit_feedback(feedback: FeedbackSubmission):
    """
    Allows users to submit feedback on content helpfulness.
    """
    try:
        content_id = ObjectId(feedback.content_id)
        
        # Verify content exists
        content = await content_collection.find_one({"_id": content_id})
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Store feedback (you might want a separate feedback collection)
        feedback_data = {
            "content_id": content_id,
            "is_helpful": feedback.is_helpful,
            "comments": feedback.comments,
            "timestamp": datetime.now()
        }
        
        # For now, we'll add feedback to the content document
        # In production, you might want a separate feedback collection
        await content_collection.update_one(
            {"_id": content_id},
            {"$push": {"feedback": feedback_data}}
        )
        
        return {"status": "success", "message": "Feedback submitted successfully"}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid content ID")
    except Exception as e:
        print(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/content/categories", response_model=List[str])
async def get_categories():
    """
    Retrieves a list of unique content categories.
    """
    try:
        # The distinct method returns a list of unique values for a given field
        categories = await content_collection.distinct("category")
        # Filter out any potential null or empty string values
        return [cat for cat in categories if cat]
    except Exception as e:
        print(f"Error fetching categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/content/search")
async def search_content(
    query: str = Query(..., min_length=1),
    category: Optional[str] = Query(None),
    content_type: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Search content by query, category, and content type.
    """
    try:
        # Build search filter
        search_filter = {
            "status": "approved",
            "$text": {"$search": query}
        }
        
        if category:
            search_filter["category"] = category
        if content_type:
            search_filter["content_type"] = content_type
        
        contents = await content_collection.find(
            search_filter
        ).sort("published_at", -1).limit(limit).to_list(limit)
        
        return contents
        
    except Exception as e:
        print(f"Error searching content: {e}")
        raise HTTPException(status_code=500, detail=str(e))
