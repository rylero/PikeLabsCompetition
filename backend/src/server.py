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

async def handle_analysis(url: str, text: str = None):
    """Shared function for handling article analysis"""
    if cached_analysis := analysis_cache.find_article_by_url(url):
        cached_analysis.pop("id")
        cached_analysis.pop("url")
        return cached_analysis

    data = getArticleAnalysis(url, text)
    if not data:
        raise fastapi.HTTPException(status_code=500, detail="Analysis failed")

    success = analysis_cache.add_article(
        url,
        data["factuality"],
        data["factuality_description"],
        data["bias"],
        data["bias_description"],
        data["opposing_links"],
        data["agreement_links"],
        data["show_bias"],
    )
    
    if not success:
        raise fastapi.HTTPException(status_code=500, detail="Failed to cache analysis")
    
    return data

@app.post("/generate_report")
async def generate_report(url: Annotated[str, Form()], text: Annotated[str, Form()]):
    return await handle_analysis(url, text)

@app.post("/generate_report_from_youtube")
async def get_captions(url: Annotated[str, Form()]):
    text = get_transcription(url)
    return await handle_analysis(url, text)

@app.websocket("/chat")
async def websocket_endpoint(websocket: fastapi.WebSocket):
    await websocket.accept()

    initialData = await websocket.receive_json()
    url = initialData["url"]
    text = initialData["text"]

    chatHistory = [{
                "role": "system",
                "content": "Your are an ai chat bot that helps users better understand the news. Users will first give you a url and text and you will then need to respond to queries"
            },
            {
                "role": "user",
                "content": f"Link: {url} + \n + {text}",
            }]

    while True:
        data = await websocket.receive_text()

        if (data == "keepalive"):
            continue
        
        chatHistory.append({
            "role": "user",
            "content": data
        })

        response = grokClient.chat.completions.create(
            model="grok-3-mini-fast",
            messages=chatHistory
        )
        chatHistory.append(response.choices[0].message)

        await websocket.send_text(response.choices[0].message.content)