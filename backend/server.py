from typing import Annotated
import fastapi
from fastapi.middleware.cors import CORSMiddleware
import json
from fastapi.params import Form

from db import Database
from ai import grokClient, tools_definition, tools_map

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

    messages = [{
                "role": "system",
                "content": "You are a news fact checker. You get given a url and article and you return a json containing a factuality score out of 5, plus a description of why you chose that score. Factuality should be evaluated thoroughly. Include if other articles came to the same conclusion, even if they were from media sources that typically reported from the opposite side. Also evaluate if the article's sources are correct, just because the article includes external sources doesn't mean that it is more factual. Then you get a bias score between -2, to +2 with -2 being very left leaning and +2 being very right leaning, along with another description of why. If the article is not political and shouldn't have a bias score please set show-bias equal to false, otherwise set it to true. In your descriptions please use key sentences or phrases that leads you to your answer. answer in a json format with fields: factuality, factuality-description, bias, bias-description, show-bias. Also find news articles that oppose the current article using the \"search\" tool and gather a list of news article links and store them in the json called opposing_links. You should start your search with the phase: \"News articles for ___\" or \"News articles against ___\". Then do the same with agreement_links with articles that agree with the current argument. Each link should be an object with two properties: title for the title of the article, and link for the link to the article."
            },
            {
                "role": "user",
                "content": f"Link: {url} + \n + {text}",
            }]
    
    response = grokClient.chat.completions.create(
        model="grok-3-mini-fast",
        tools=tools_definition,
        tool_choice="auto",
        messages=messages
    )

    messages.append(response.choices[0].message)

    while response.choices[0].message.tool_calls:
        for tool_call in response.choices[0].message.tool_calls:

            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            result = tools_map[function_name](**function_args)

            messages.append(
                {
                    "role": "tool",
                    "content": json.dumps(result),
                    "tool_call_id": tool_call.id  # tool_call.id supplied in Grok's response
                }
            )

        response = grokClient.chat.completions.create(
            model="grok-3-latest",
            messages=messages,
            tools=tools_definition,
            tool_choice="auto"
        )

    data = json.loads(response.choices[0].message.content)

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
