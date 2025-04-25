from typing import Annotated
import fastapi
from dotenv import load_dotenv
import os
import json
from fastapi.params import Form
from openai import OpenAI
from tools import tools_definition, tools_map

load_dotenv()

GROK_API_KEY = os.getenv("GROK_API")
client = OpenAI(
  api_key=GROK_API_KEY,
  base_url="https://api.x.ai/v1",
)

app = fastapi.FastAPI()

from pydantic import BaseModel
class Article(BaseModel):
     body: str

@app.get("/")
def read_root():
    return {"message": "Root api endpoint"}

@app.post("/generate_report")
async def generate_report(url: Annotated[str, Form()], text: Annotated[str, Form()]):
    messages = [{
                "role": "system",
                "content": "You are a news fact checker. You get given a url and article and you return a json containing a factuality score out of 5, plus a description of why you chose that score. Factuality should be evaulated thrououghly. Include if other articles came to the same conclusion, even if there were from media sources that tipically reported from the opposite side. Also evaluate if the articles sources are correct, just because the article includes external sources doesnt mean that it is more factual.Then you get a bias score between -2, to +2 with -2 being very left leaning and +2 being very right leaning, along with another description of why. In your descriptions please use key sentences or phrases that leads you to your answer. answer in a json format with 4 fields: factuality, factuality-description, bias, bias-description. Also find news articles that oppose the current article using the \"search\" tool and gather a list of news article links and store them in the json called opposing_links. Then do the same with agreement_links with articles that agree with the current argument."
            },
            {
                "role": "user",
                "content": f"Link: {url} + \n + {text}",
            }]
    
    response = client.chat.completions.create(
        model="grok-3",
        tools=tools_definition,
        tool_choice="auto",
        messages=messages
    )

    messages.append(response.choices[0].message)

    if response.choices[0].message.tool_calls:
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

        response = client.chat.completions.create(
            model="grok-3-latest",
            messages=messages,
            tools=tools_definition,
            tool_choice="auto"
        )

    return json.loads(response.choices[0].message.content)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
