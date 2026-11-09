import base62
import threading 
import requests
from requests.exceptions import RequestException
from settings import settings
import logging
import json

logger = logging.getLogger(__name__)

class IDGenerator:
    def __init__(self, start: int | None = None, end: int | None = None):
        self.start = start 
        self.end = end 
        self._lock = threading.Lock()
        self._renew_range_url = settings.RANGE_ALLOCATOR_URL
    
    def generate(self):
        with self._lock:
            if self.start is None or self.end is None or self.start > self.end:
                self._renew_range()
            start = self.start
            assert start is not None
            encoded = base62.encode(start)
            self.start = start + 1

        return encoded 
    
    def _renew_range(self):
        try:
            response = requests.get(self._renew_range_url, timeout=5)
            response.raise_for_status()
            payload = response.json()
        except (RequestException, json.JSONDecodeError) as e:
            logger.error("Call to range allocator failed: %s", e)
            raise RuntimeError("Unable to retrieve an ID range") from e

        if not isinstance(payload, dict) or payload.get("success") != 1:
            raise RuntimeError("Range allocator returned no available range")

        start = payload.get("start")
        end = payload.get("end")
        if not isinstance(start, int) or not isinstance(end, int) or start > end:
            raise RuntimeError("Range allocator returned an invalid range")

        self.start = start
        self.end = end
        
genertor = IDGenerator()