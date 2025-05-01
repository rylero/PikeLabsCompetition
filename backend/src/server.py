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
    start = time.time()
    if cached_analysis := analysis_cache.find_article_by_url(url):
        cached_analysis.pop("id")
        cached_analysis.pop("url")
        return cached_analysis
    print(f"Cache Check: {time.time() - start}s")

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

@app.post("/get_captions")
async def get_captions(url: Annotated[str, Form()]):
    return get_transcription(url)

@app.websocket("/chat")
async def chat_endpoint(websocket: fastapi.WebSocket):
    await websocket.accept()

    inital_message = json.loads(await websocket.receive_text())
    current_chat = None
    
    current_chat = message_history.get_message_history(inital_message.email, inital_message.url)
    if not current_chat:
        current_chat = [{
                "role": "system",
                "content": "You are an ai chat bot that helps users understand articles. Users will chat with you about an article and ask questions. You will be given an article and url and the user will ask questions."
            }, {
                "role": "user",
                "content": f"Link: {inital_message.url} + \n + {inital_message.text}"
            }]
        message_history.create_messsage_history(inital_message.email, inital_message.url, current_chat)

    while True:
        chat_message = json.loads(websocket.receive_text())
        
        msg = chat_message.user_message
        current_chat.append({
            "role": "user",
            "content": msg
        })

        response = grokClient.chat.completions.create(
            model="grok-3-fast",
            messages=current_chat,
            stream=True,
        )

        for chunk in response:
            websocket.send_text(chunk.choices[0].delta.content)
        
        current_chat.append(response.choices[0].message)
        
        message_history.update_message_history(inital_message.email, inital_message.url, current_chat)