import feedparser
import asyncio
from .db import content_collection
from .models import Content, ContentType, Category
from .ai import get_summary, get_category
import re
from datetime import datetime

# A sample list of RSS feeds to start with
RSS_FEEDS = [
    "https://www.wired.com/feed/category/security/rss",
    "https://www.technologyreview.com/feed/",
    "https://feeds.feedburner.com/eff/updates"
]

async def fetch_and_store_feeds():
    """Fetches content from RSS feeds and stores new entries in the database."""
    for url in RSS_FEEDS:
        print(f"Fetching feed: {url}")
        feed = feedparser.parse(url)
        
        for entry in feed.entries:
            # Check if the article already exists in the DB
            existing_content = await content_collection.find_one({"url": entry.link})
            if existing_content:
                continue # Skip if it already exists

            # Clean up the summary text from HTML tags
            summary_text = re.sub('<[^<]+?>', '', entry.summary)

            # Get AI-powered summary and category
            ai_summary = await get_summary(summary_text)
            ai_category = await get_category(summary_text)

            # Create a Content object
            content_item = Content(
                url=entry.link,
                title=entry.title,
                summary=[ai_summary], # Use the AI-generated summary
                source=feed.feed.title,
                content_type=ContentType.ARTICLE, # Default to article
                category=ai_category, # Use the AI-determined category
                published_at=datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else datetime.now(),
            )

            # Convert the Pydantic model to a dictionary for DB insertion, excluding None values
            content_dict = content_item.dict(by_alias=True, exclude_none=True)

            # Manually convert types that are not BSON-encodable
            content_dict['url'] = str(content_item.url)

            # Insert into the database
            await content_collection.insert_one(content_dict)
            print(f"Stored new article: {entry.title}")

    return {"status": "success", "message": "Feeds processed."}
