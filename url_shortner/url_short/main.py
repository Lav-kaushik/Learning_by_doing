from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from model import URL
from db import get_db
from id_generator import genertor
from schema import URLMapping
from sqlalchemy.exc import IntegrityError
from redis_fastapi import CacheBackendDep, FastAPIRedis
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
async def generate_short_url(data : URL, cache: CacheBackendDep, db = Depends(get_db)):
    try:
        shortened_url= genertor.generate()
        original_url = str(data.url)
        mapping = URLMapping(original_url=original_url, shortened_url=shortened_url)
        await cache.set(shortened_url, original_url, ttl=300, eviction_group="urls")
        logger.info("Successfully cached: %s", shortened_url)
        db.add(mapping)
        db.commit()
    except IntegrityError:
        db.rollback()
        return {
            "error": "The url mapping already exists.",
            "status_code": status.HTTP_400_BAD_REQUEST
        }

    return {"shorten_url": shortened_url}

@app.get("/api/urls/{short_url}")
async def redirect_to_url(short_url: str, cache: CacheBackendDep, db = Depends(get_db)):
    result = await cache.get(short_url, default=None, eviction_group="urls")
    if result is not None:
        logger.info("Cache hit for %s", short_url)
        return RedirectResponse(url=str(result))
    logger.info("Cache miss for: %s fetching data from db.", short_url)
    mapping = db.get(URLMapping, short_url)
    if mapping is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown URL.")
    await cache.set(mapping.shortened_url, mapping.original_url, ttl=300, eviction_group="urls")
    return RedirectResponse(url=mapping.original_url)
