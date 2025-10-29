import os
from openai import OpenAI

client = OpenAI(base_url=os.getenv("ADP_BASE_URL"), api_key=os.getenv("ADP_API_KEY"))
model = os.getenv("ADP_EMBEDDINGS_MODEL","text-embedding-3-large")

emb = client.embeddings.create(model=model, input=["hello world", "agentic ai"])
print(len(emb.data[0].embedding), len(emb.data[1].embedding))