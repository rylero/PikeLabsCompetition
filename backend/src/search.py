from pydantic import BaseModel, Field
import requests
import os
from dotenv import load_dotenv

load_dotenv()

BRAVE_API_KEY = os.getenv("BRAVE_API")

class SearchRequest(BaseModel):
    query: str = Field(description="string to search brave search api with for search results")

def get_search_result(**kwargs):
    request = SearchRequest(**kwargs)

    url = "https://api.search.brave.com/res/v1/web/search"
    params = { "q": request.query, "summary": True }
    headers = {
        "X-Subscription-Token": BRAVE_API_KEY
    }
    response = requests.get(url, params=params, headers=headers)

    return response.json()

get_search_result_schema = SearchRequest.model_json_schema()