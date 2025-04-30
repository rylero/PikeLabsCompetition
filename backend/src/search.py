from pydantic import BaseModel, Field
import requests
import os, json
from dotenv import load_dotenv
from readabilipy import simple_json_from_html_string

load_dotenv()

BRAVE_API_KEY = os.getenv("BRAVE_API")

class SearchRequest(BaseModel):
    query: str = Field(description="string to search brave search api with for search results")

def article_text(url):
    res = requests.get(url)
    article = simple_json_from_html_string(res.text, use_readability=True)
    selected_features = {}
    selected_features["byline"] = article["byline"]
    selected_features["content"] = article["content"]
    return selected_features

def get_search_result(**kwargs):
    request = SearchRequest(**kwargs)

    url = "https://api.search.brave.com/res/v1/web/search"
    params = { "q": request.query, "summary": True, "count": 10 }
    headers = {
        "X-Subscription-Token": BRAVE_API_KEY
    }
    response = requests.get(url, params=params, headers=headers)

    json = response.json()

    data = []
    for result in json["web"]["results"]:
        article = {}
        if "title" in result:
            article["title"] = result["title"]
        if "description" in result:
            article["description"] = result["description"]
        if "url" in result:
            article["url"] = result["url"]
        if "age" in result:
            article["page_age"] = result["age"]
        # article["text_processor_out"] = article_text(result["url"])
        data.append(article)
        print("Article len: " + str(len(str(article))))
    return data


get_search_result_schema = SearchRequest.model_json_schema()