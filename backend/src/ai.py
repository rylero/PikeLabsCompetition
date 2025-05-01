from search import get_search_result_schema, get_search_result
import os, json
from dotenv import load_dotenv
from openai import OpenAI
import time

load_dotenv()

tools_definition = [
    {
        "type": "function",
        "function": {
            "name": "get_search_result",
            "description": "Gets search results of only news articles from the tavily search api.",
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

def getArticleAnalysis(url, text):
    last_time = time.time()
    messages = [{
                "role": "system",
                "content": "You are a news fact checker. You get given a url and article and you return a json containing a factuality score out of 5, plus a description of why you chose that score. Factuality should be evaluated thoroughly. Include if other articles came to the same conclusion, even if they were from media sources that typically reported from the opposite side. Also evaluate if the article's sources are correct, just because the article includes external sources doesn't mean that it is more factual. Then you get a bias score between -2, to +2 with -2 being very left leaning and +2 being very right leaning, along with another description of why. If the article is not political and shouldn't have a bias score please set show-bias equal to false, otherwise set it to true. In your descriptions please use key sentences or phrases that leads you to your answer. answer in a json format with fields: factuality, factuality-description, bias, bias-description, show-bias. Also find news articles that oppose the current article using the \"search\" tool and gather a list of news article links and store them in the json called opposing_links. Try to group your searches together to speed up response time. You should start your search with the phase: \"News articles for ___\" or \"News articles against ___\". Then do the same with agreement_links with articles that agree with the current argument. Each link should be an object with two properties: title for the title of the article, and link for the link to the article."
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
    print(f"First Response: {time.time() - last_time}s")
    last_time = time.time()

    while response.choices[0].message.tool_calls:
        i = 1
        for tool_call in response.choices[0].message.tool_calls:

            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            result = tools_map[function_name](**function_args)
            with open(f"{len(result)}.txt", "w") as f:
                f.write(result)

            messages.append(
                {
                    "role": "tool",
                    "content": result,
                    "tool_call_id": tool_call.id  # tool_call.id supplied in Grok's response
                }
            )

            print(f"Tool Call #{i}: {time.time() - last_time}s")
            last_time = time.time()
            i+=1

        response = grokClient.chat.completions.create(
            model="grok-3-latest",
            messages=messages,
            tools=tools_definition,
            tool_choice="auto"
        )
        print(f"Last Response: {time.time() - last_time}s")
        print(response.choices[0].message.content)
        last_time = time.time()

    data = json.loads(response.choices[0].message.content)

    return data;
