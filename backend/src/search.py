from pydantic import BaseModel, Field
from dotenv import load_dotenv
from tavily import TavilyClient
import os

load_dotenv()

class SearchRequest(BaseModel):
    query: str = Field(description="string to search brave search api with for search results")

client = TavilyClient(api_key=os.getenv("TAVILY_API"))

def get_article_text(urls):
    return client.extract(urls=urls, extract_depth="advanced")

def compress(data):
    s = ""
    for row in data:
        s += "Article\n"
        s += f"Url: {row['url']}\n"
        s += f"Title: {row['title']}\n"
        s += f"Date: {row['published_date']}\n"
        s += f"Content: {row['content']}\n\n"
    return s

def get_search_result(**kwargs):
    request = SearchRequest(**kwargs)

    query = request.query
    return compress(client.search(query, topic="news", max_results=5, search_depth="advanced")["results"])

get_search_result_schema = SearchRequest.model_json_schema()