from search import get_search_result, get_search_result_schema
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

tools_definition = [
    {
        "type": "function",
        "function": {
            "name": "get_search_result",
            "description": "Gets search results of only news articles from the brave search api.",
            "parameters": get_search_result_schema,
        },
    },
]

tools_map = {
    "get_search_result": get_search_result
}

GROK_API_KEY = os.getenv("GROK_API")
grokClient = OpenAI(
  api_key=GROK_API_KEY,
  base_url="https://api.x.ai/v1",
)