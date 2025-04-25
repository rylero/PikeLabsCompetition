from search import get_search_result, get_search_result_schema

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