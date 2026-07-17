import os
import time
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Configure logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("web-app")

app = FastAPI(title="SRE Demo")

# Read Database connection details from Environment Variables

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.middleware("http")
async def log_request_execution_latency(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    logger.info(f"HTTP {request.method} {request.url.path} processed in {time.time() - start_time:.4f}s")
    return response

@app.get("/")
def read_root():
    return {
        "status": "Web App Online",
        "description": "lorem Ipsum"
    }

@app.get("/health")
def health_check():
    return  {"status": "healthy"}
