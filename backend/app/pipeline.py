import feedparser
import asyncio
import aiohttp
import json
from .db import content_collection
from .models import Content, ContentType, Category
from .ai import get_summary, get_category, transcribe_audio
import re
from datetime import datetime
import os
from urllib.parse import quote
import xml.etree.ElementTree as ET

# A sample list of RSS feeds to start with
RSS_FEEDS = [
    "https://www.wired.com/feed/category/security/rss",
    "https://www.technologyreview.com/feed/",
    "https://feeds.feedburner.com/eff/updates",
    "https://www.amnesty.org/en/rss/",
    "https://www.hrw.org/rss",
    "https://www.accessnow.org/feed/"
]

# Academic search terms for Google Scholar alerts
ACADEMIC_SEARCH_TERMS = [
    "artificial intelligence human rights",
    "AI bias discrimination",
    "algorithmic fairness",
    "AI ethics human rights",
    "machine learning privacy rights",
    "AI surveillance human rights"
]

# Podcast RSS feeds focused on AI and human rights
PODCAST_FEEDS = [
    "https://feeds.simplecast.com/54nAGcIl",  # AI Ethics podcast
    "https://feeds.megaphone.fm/techpolicy",  # Tech Policy podcast
    "https://feeds.feedburner.com/futureofwork"  # Future of Work podcast
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

            # Insert the content into the database
            result = await content_collection.insert_one(content_dict)
            print(f"Inserted content with ID: {result.inserted_id}")

    return {"status": "success", "message": "Feeds processed successfully"}

async def fetch_academic_content():
    """Fetches academic content using Google Scholar-like search."""
    print("Fetching academic content...")
    
    for search_term in ACADEMIC_SEARCH_TERMS:
        try:
            # Use Semantic Scholar API as an alternative to Google Scholar
            encoded_term = quote(search_term)
            url = f"https://api.semanticscholar.org/graph/v1/paper/search?query={encoded_term}&limit=5&fields=title,abstract,url,authors,year,venue"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for paper in data.get('data', []):
                            # Check if paper already exists
                            existing_content = await content_collection.find_one({"url": paper.get('url', '')})
                            if existing_content:
                                continue
                            
                            # Process academic paper
                            abstract = paper.get('abstract', '')
                            if abstract:
                                ai_summary = await get_summary(abstract)
                                ai_category = await get_category(abstract)
                                
                                authors = [author.get('name', '') for author in paper.get('authors', [])]
                                
                                content_item = Content(
                                    url=paper.get('url', f"https://semanticscholar.org/paper/{paper.get('paperId', '')}"),
                                    title=paper.get('title', 'Untitled Academic Paper'),
                                    summary=[ai_summary],
                                    source=f"Academic - {paper.get('venue', 'Unknown Venue')}",
                                    content_type=ContentType.ARTICLE,
                                    category=ai_category,
                                    published_at=datetime(paper.get('year', datetime.now().year), 1, 1) if paper.get('year') else datetime.now(),
                                    metadata={"authors": authors, "venue": paper.get('venue', '')}
                                )
                                
                                content_dict = content_item.dict(by_alias=True, exclude_none=True)
                                content_dict['url'] = str(content_item.url)
                                
                                result = await content_collection.insert_one(content_dict)
                                print(f"Inserted academic content: {paper.get('title', 'Untitled')}")
                    
                    # Rate limiting for API
                    await asyncio.sleep(1)
                    
        except Exception as e:
            print(f"Error fetching academic content for '{search_term}': {e}")
            continue
    
    return {"status": "success", "message": "Academic content processed"}

async def fetch_podcast_content():
    """Fetches and processes podcast content with speech-to-text."""
    print("Fetching podcast content...")
    
    for podcast_url in PODCAST_FEEDS:
        try:
            feed = feedparser.parse(podcast_url)
            
            for entry in feed.entries[:3]:  # Limit to 3 most recent episodes
                # Check if episode already exists
                existing_content = await content_collection.find_one({"url": entry.link})
                if existing_content:
                    continue
                
                # Look for audio enclosure
                audio_url = None
                for enclosure in getattr(entry, 'enclosures', []):
                    if enclosure.type and 'audio' in enclosure.type:
                        audio_url = enclosure.href
                        break
                
                if audio_url:
                    # Get transcript using speech-to-text
                    transcript = await transcribe_audio(audio_url)
                    
                    if transcript:
                        ai_summary = await get_summary(transcript[:2000])  # Limit text for API
                        ai_category = await get_category(transcript[:2000])
                        
                        content_item = Content(
                            url=entry.link,
                            title=entry.title,
                            summary=[ai_summary],
                            source=f"Podcast - {feed.feed.title}",
                            content_type=ContentType.PODCAST,
                            category=ai_category,
                            published_at=datetime(*entry.published_parsed[:6]) if hasattr(entry, 'published_parsed') else datetime.now(),
                            metadata={"audio_url": audio_url, "transcript_preview": transcript[:500]}
                        )
                        
                        content_dict = content_item.dict(by_alias=True, exclude_none=True)
                        content_dict['url'] = str(content_item.url)
                        
                        result = await content_collection.insert_one(content_dict)
                        print(f"Inserted podcast content: {entry.title}")
                
                # Rate limiting
                await asyncio.sleep(2)
                
        except Exception as e:
            print(f"Error processing podcast feed {podcast_url}: {e}")
            continue
    
    return {"status": "success", "message": "Podcast content processed"}

async def run_complete_pipeline():
    """Runs the complete content pipeline including RSS, academic, and podcast sources."""
    print("Starting complete content pipeline...")
    
    results = []
    
    # Run all pipeline components
    rss_result = await fetch_and_store_feeds()
    results.append(rss_result)
    
    academic_result = await fetch_academic_content()
    results.append(academic_result)
    
    podcast_result = await fetch_podcast_content()
    results.append(podcast_result)
    
    return {
        "status": "success",
        "message": "Complete pipeline executed",
        "results": results
    }
