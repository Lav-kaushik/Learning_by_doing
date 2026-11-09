from starlette.routing import Route
from starlette.applications import Starlette
import threading
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

_lock = threading.Lock()

app = Starlette()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000"]
)

_START = 100000001
_END = 56000000000
_DIFF = 1000000

def ping(request):
    return JSONResponse({
        "message": "pong"
    })

def get_range(request):
    global _START
    with _lock:
        if _START > _END:
            return JSONResponse(
                {
                    "success": -1,
                    "status_code": 400
                }
            )
        start = _START
        end = min(start+_DIFF-1, _END)
        _START = end + 1
    return JSONResponse(
        {
            "success": 1,
            "start": start,
            "end": end
        }
    )

app = Starlette(routes=[
    Route("/get/range", get_range),
    Route("/ping", ping),
])