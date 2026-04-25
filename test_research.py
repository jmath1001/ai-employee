from openai import OpenAI
from actions_web import deep_research
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
print(deep_research("diabetes recipes", client))
