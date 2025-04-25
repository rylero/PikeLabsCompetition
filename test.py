from openai import OpenAI
    
client = OpenAI(
  api_key="xai-QEmLDTSrW3ZXhFH6yGpNtNxE6dn0Ada1da9Wqv0vjwxLDAJmPu3XPxfhThPrpSoLbYemXKwjnk3aRA0P",
  base_url="https://api.x.ai/v1",
)

completion = client.chat.completions.create(
  model="grok-3-mini-fast",
  messages=[
    {
        "role": "system",
        "content": "You are a news fact checker. You get given a url and article and you return a json containing a factuality score out of 5, plus a description of why you chose that score. Factuality should be evaulated thrououghly. Include if other articles came to the same conclusion, even if there were from media sources that tipically reported from the opossite side. Also evaluate if the articles sources are correct, just because the article includes external sources doesnt mean that it is more factual. Stick to cold hard facts. Then you get a bias score between -2, to +2 with -2 being very left leaning and +2 being very right leaning, along with another description of why. In your descriptions please use key sentences or phrases that leads you to your answer. answer in a json format with 4 fields: factuality, factuality-description, bias, bias-description. Also generate a list of links stored in a list in the json called opposing_links to other articles from the opposing side of the argument. Then do the same with agreement_links with articles that agree with the current argument."
    },
    {
        "role": "user",
        "content": """Link: https://www.npr.org/2025/04/22/nx-s1-5372588/trump-tariffs-imf-trade-world-economy
The global economy will be hit hard by Trump's tariffs, IMF warns
April 22, 20253:06 PM ET
By 

Rafael Nam

President Trump announced his latest tariffs at a Rose Garden event at the White House on April 2. The International Monetary Fund on Tuesday cut its forecasts for the global economy this year, citing the risks from an all-out trade war.
President Trump announced his latest tariffs at a Rose Garden event at the White House in Washington, D.C., on April 2. The International Monetary Fund cut its forecasts for the global economy this year, citing the risks from an all-out trade war.

Chip Somodevilla/Getty Images
The International Monetary Fund warned on Tuesday that the global economy could be hit hard as President Trump's sweeping tariffs threaten to spark an all-out trade war.

US President Donald Trump holds a chart as he delivers remarks on reciprocal tariffs during an event in the Rose Garden entitled "Make America Wealthy Again" at the White House in Washington, DC, on April 2, 2025.
Newsletter
Are Trump's tariffs a bargaining chip for a new global economic order?
People walk past a screen showing the CSI 300 Index at a shopping mall in Guangzhou, in southern China's Guangdong province.
U.S. vs. China: Inside a great power rivalry
China warns of 'countermeasures' against any deals that harm its interests
The IMF predicted the global economy would grow 2.8% this year, down from 3.3% in 2024. Back in January, the multilateral organization had predicted global growth would expand at the same rate as last year.

At the same time, the IMF slashed its forecast for U.S. growth to 1.8% this year, down from the 2.8% it had predicted in January.

But the IMF also recognized just how unpredictable things had become for the global economy since Trump unveiled a number of tariffs this year including on steel and aluminum imports. Although he has paused many of them, the U.S. has still imposed a 10% tariff on all imports. Meanwhile, he has slapped an additional 145% tariff on China so far on his second term.

"We're entering a new era as the global economic system that has operated for the last 80 years is being reset," said Pierre-Olivier Gourinchas, IMF's chief economist, in a news conference.

"Beyond the abrupt increase in tariffs, the surge in policy uncertainty is a major driver of the economic outlook," he added. "If sustained, the increase in trade tensions and uncertainty will slow global growth significantly."

Global markets have tumbled in the wake of Trump's latest tariffs earlier this month, while fears are rising that foreign investors may be cutting their exposure to the U.S. and no longer considering the world's biggest economy the safe haven it has been for decades.

President Trump answers a reporters question during a meeting with Israeli Prime Minister Benjamin in the Oval Office of the White House on April 7. 
Politics
Mixed messages on tariffs raise scrutiny on Trump aides
One of the biggest fears by investors is that countries targeted by Trump will retaliate, leading to more widespread tensions. Trump has temporarily paused most of the reciprocal tariffs he had imposed on countries, except for China, as his administration seeks to negotiate deals.

So far, China and Canada have hit back at the U.S. with their own tariffs, while the European Union has said it's prepared to retaliate but is willing to give negotiations a try.

Scott Horsley contributed to this report."""
    }
  ]
)

with open("res.json", "w") as f:
    f.write(completion.choices[0].message.content)