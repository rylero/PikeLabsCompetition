from typing import Annotated
import fastapi
from fastapi.middleware.cors import CORSMiddleware
import json, time
from fastapi.params import Form
import asyncio

from transcription import get_transcription
from cache import AnalysisCache
from ai import grokClient, tools_definition, tools_map, getArticleAnalysis
from chat import ChatMessageHistoryDB
from search import get_article_text

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

    if text == "":
        try:
            article_data = get_article_text(url)
            if not article_data or not article_data.get('results'):
                raise fastapi.HTTPException(status_code=422, detail="Could not extract article text")
            text = article_data['results'][0]['raw_content']
        except Exception as e:
            raise fastapi.HTTPException(status_code=422, detail=f"Failed to extract article text: {str(e)}")

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

    # Wait for initial message
    initialData = await websocket.receive_json()
    print("InitialData : " + str(initialData))
    
    # Handle initial connection
    url = ""
    text = ""
    email = initialData.get("email", "anonymous")  # Get email or use anonymous as default
    
    if email == "anonymous":
        print("AUTH FAILURE")

    if initialData.get("type") == "new_article":
        print("New Article")
        url = initialData["data"]
    else:
        # Legacy format handling
        url = initialData.get("url", "")
        text = initialData.get("text", "")

    # Get article text if not provided
    if not text:
        try:
            article_data = get_article_text(url)
            if article_data and article_data.get('results'):
                text = article_data['results'][0]['raw_content']
            else:
                text = "Could not extract article text"
        except Exception as e:
            text = f"Error extracting article text: {str(e)}"

    chat_id = str(time.time())  # Unique chat ID for this session
    current_sequence = 0  # Track the current sequence number
    current_generation = None  # Track the current generation task

    # Try to get existing messages from database
    existing_messages = message_history.get_message_history(email, url)
    if existing_messages:
        messages = existing_messages
    else:
        # Initialize messages with system and initial user message
        messages = [{
            "role": "system",
            "content": "Your are an ai chat bot that helps users better understand the news. Users will first give you a url and text and you will then need to respond to queries. You also have acess to a search tool but try to avoid using it as much as possible as its very slow. If the user asks you to research something then use the tool."
        },
        {
            "role": "user",
            "content": f"Link: {url}\n\nArticle Text:\n{text}",
        }]
        # Store initial messages in database
        message_history.create_message_history(email, url, messages)

    # Send initial chat history
    await websocket.send_text(json.dumps({
        "type": "history",
        "chat_id": chat_id,
        "sequence": current_sequence,
        "data": {"messages": messages}
    }))

    async def generate_response(message_sequence: int, current_messages: list):
        print(message_sequence, current_messages)
        """Async function to generate response from Grok"""
        try:
            response = grokClient.chat.completions.create(
                model="grok-3-mini-fast",
                tools=tools_definition,
                tool_choice="auto",
                messages=current_messages
            )

            # Convert ChatCompletionMessage to dict
            message_dict = {
                "role": response.choices[0].message.role,
                "content": response.choices[0].message.content,
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": tool_call.type,
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    } for tool_call in (response.choices[0].message.tool_calls or [])
                ] if response.choices[0].message.tool_calls else None
            }
            current_messages.append(message_dict)

            while message_dict.get("tool_calls"):
                for tool_call in message_dict["tool_calls"]:
                    function_name = tool_call["function"]["name"]
                    function_args = json.loads(tool_call["function"]["arguments"])

                    result = tools_map[function_name](**function_args)

                    current_messages.append({
                        "role": "tool",
                        "content": result,
                        "tool_call_id": tool_call["id"]
                    })

                response = grokClient.chat.completions.create(
                    model="grok-3-mini-fast",
                    messages=current_messages,
                    tools=tools_definition,
                    tool_choice="auto"
                )

                # Convert final response to dict
                message_dict = {
                    "role": response.choices[0].message.role,
                    "content": response.choices[0].message.content,
                    "tool_calls": [
                        {
                            "id": tool_call.id,
                            "type": tool_call.type,
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments
                            }
                        } for tool_call in (response.choices[0].message.tool_calls or [])
                    ] if response.choices[0].message.tool_calls else None
                }
                current_messages.append(message_dict)

            # Only send if this is still the current sequence
            if message_sequence == current_sequence:
                # Update messages in database
                message_history.update_message_history(email, url, current_messages)
                
                await websocket.send_text(json.dumps({
                    "type": "message",
                    "chat_id": chat_id,
                    "sequence": message_sequence,
                    "data": {
                        "message": message_dict["content"],
                        "role": message_dict["role"]
                    }
                }))
        except Exception as e:
            print(f"Error in generate_response: {e}")
            # Only send error if this is still the current sequence
            if message_sequence == current_sequence:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "chat_id": chat_id,
                    "sequence": message_sequence,
                    "data": {"error": str(e)}
                }))

    while True:
        try:
            data = await websocket.receive_text()

            if data == "keepalive":
                continue

            # Parse the incoming message
            try:
                message_data = json.loads(data)
                message_type = message_data.get("type", "message")
                message_content = message_data.get("data", "")
                message_sequence = message_data.get("sequence", 0)
            except json.JSONDecodeError:
                # Handle legacy format
                message_type = "message"
                message_content = data
                message_sequence = current_sequence + 1

            # If this is an old sequence, ignore it
            if message_sequence < current_sequence:
                continue

            # Update current sequence
            current_sequence = message_sequence

            if message_type == "new_article":
                print("New Article")
                # Cancel any ongoing generation
                if current_generation:
                    current_generation = None
                
                # Reset sequence for new article
                current_sequence = 0
                url = message_content
                
                # Try to get existing messages for new article
                existing_messages = message_history.get_message_history(email, url)
                if existing_messages:
                    messages = existing_messages
                else:
                    messages = [{
                        "role": "system",
                        "content": "Your are an ai chat bot that helps users better understand the news. Users will first give you a url and text and you will then need to respond to queries. You also have acess to a search tool but try to avoid using it as much as possible as its very slow. If the user asks you to research something then use the tool."
                    },
                    {
                        "role": "user",
                        "content": f"Link: {url}\n\nArticle Text:\n{text}",
                    }]
                    # Store initial messages in database
                    message_history.create_message_history(email, url, messages)
                
                await websocket.send_text(json.dumps({
                    "type": "history",
                    "chat_id": chat_id,
                    "sequence": current_sequence,
                    "data": {"messages": messages}
                }))
                continue

            # Add user message to history
            messages.append({
                "role": "user",
                "content": message_content
            })
            
            # Update messages in database
            message_history.update_message_history(email, url, messages)

            # Start new generation task
            current_generation = asyncio.create_task(
                generate_response(current_sequence, messages.copy())
            )

        except Exception as e:
            print(f"Error in websocket loop: {e}")
            await websocket.send_text(json.dumps({
                "type": "error",
                "chat_id": chat_id,
                "sequence": current_sequence,
                "data": {"error": str(e)}
            }))