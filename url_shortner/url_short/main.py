from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from model import URL
from db import get_db
from id_generator import genertor
from schema import URLMapping, URLAnalytics
from sqlalchemy.exc import IntegrityError
from sqlalchemy import update, func
from redis_fastapi import AsyncRedisDep, FastAPIRedis
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
FastAPIRedis(app).lifespan()

@app.post("/ping")
def ping():
    return {
        "message": "pong"
    }

@app.post("/api/urls/shorten")
async def generate_short_url(data : URL, cache: AsyncRedisDep, db = Depends(get_db)):
    try:
        shortened_url= genertor.generate()
        original_url = str(data.url)
        mapping = URLMapping(original_url=original_url, shortened_url=shortened_url)
        analytics = URLAnalytics(short_url=shortened_url)
        await cache.set(shortened_url, original_url, ex=300)
        logger.info("Successfully cached: %s", shortened_url)
        db.add(mapping)
        db.add(analytics)
        db.commit()
    except IntegrityError:
        db.rollback()
        return {
            "error": "The url mapping already exists.",
            "status_code": status.HTTP_400_BAD_REQUEST
        }

    return {"shorten_url": shortened_url}

async def update_analytics(key: str, cache: AsyncRedisDep, db):
    click_count = await cache.incr(f"clicks-{key}", 1)
    if click_count >= 10000:
        update_stmt = (
            update(URLAnalytics)
            .where(URLAnalytics.short_url==key)
            .values(
                click_count = URLAnalytics.click_count + click_count,
                last_accessed = func.now()
            )
        )
        result = db.execute(update_stmt)
        if result.rowcount == 0:
            db.rollback()
            logger.error("No analytics row found for short URL %s", key)
            return
        db.commit()
        await cache.delete(f"clicks-{key}")

    return 

@app.get("/api/urls/{short_url}")
async def redirect_to_url(short_url: str, cache: AsyncRedisDep, db = Depends(get_db)):
    result = await cache.get(short_url)
    if result is not None:
        logger.info("Cache hit for %s", short_url)
        await update_analytics(short_url, cache, db)
        if isinstance(result, bytes):
            result = result.decode("utf-8")
        return RedirectResponse(url=result)
    logger.info("Cache miss for: %s fetching data from db.", short_url)
    mapping = db.get(URLMapping, short_url)
    if mapping is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown URL.")
    await cache.set(mapping.shortened_url, mapping.original_url, ex=300)
    await update_analytics(short_url, cache, db)
    return RedirectResponse(url=mapping.original_url)
