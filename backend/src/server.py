from typing import Annotated
import fastapi
from fastapi.middleware.cors import CORSMiddleware
import json, time
from fastapi.params import Form

from transcription import get_transcription
from cache import AnalysisCache
from ai import grokClient, tools_definition, tools_map, getArticleAnalysis
from chat import ChatMessageHistoryDB

app = fastapi.FastAPI()
analysis_cache = AnalysisCache()
message_history = ChatMessageHistoryDB()

origins = [
    "chrome-extension://hokdliajopfilpnmimlhennnnbjgmane",  # Your Chrome extension's origin
    "http://localhost",  # For local development
    "http://localhost:8000",  # If your server runs locally
    # Add other origins as needed
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # List of allowed origins
    allow_credentials=True,  # Allow cookies and credentials
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

from pydantic import BaseModel
class Article(BaseModel):
    body: str

@app.get("/")
def read_root():
    return {"message": "Root api endpoint"}

@app.post("/generate_report")
async def generate_report(url: Annotated[str, Form()], text: Annotated[str, Form()]):
    if cached_analysis := analysis_cache.find_article_by_url(url):
        cached_analysis.pop("id")
        cached_analysis.pop("url")
        return cached_analysis

    data = getArticleAnalysis(url, text)

    if not data:
        raise fastapi.HTTPException(status_code=500, detail="Internal Server Error.")

    analysis_cache.add_article(
        url,
        data["factuality"],
        data["factuality_description"],
        data["bias"],
        data["bias_description"],
        data["opposing_links"],
        data["agreement_links"],
    )

    return data

@app.post("/generate_report_from_youtube")
async def get_captions(url: Annotated[str, Form()]):
    text = get_transcription(url)

    if cached_analysis := analysis_cache.find_article_by_url(url):
        cached_analysis.pop("id")
        cached_analysis.pop("url")
        return cached_analysis

    data = getArticleAnalysis(url, text)

    if not data:
        raise fastapi.HTTPException(status_code=500, detail="Internal Server Error.")

    analysis_cache.add_article(
        url,
        data["factuality"],
        data["factuality_description"],
        data["bias"],
        data["bias_description"],
        data["opposing_links"],
        data["agreement_links"],
    )

    return data