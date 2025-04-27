from typing import Annotated
import fastapi
from fastapi.middleware.cors import CORSMiddleware
import json
from fastapi.params import Form

from db import Database
from ai import grokClient, tools_definition, tools_map, getArticleAnalysis

app = fastapi.FastAPI()
db = Database()

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
    if cached_analysis := db.find_article_by_url(url):
        cached_analysis.pop("id")
        cached_analysis.pop("url")
        return cached_analysis

    data = getArticleAnalysis(url, text)

    if not data:
        raise fastapi.HTTPException(status_code=500, detail="Internal Server Error.")

    db.add_article(
        url,
        data["factuality"],
        data["factuality-description"],
        data["bias"],
        data["bias-description"],
        data["opposing_links"],
        data["agreement_links"],
    )

    return data;
