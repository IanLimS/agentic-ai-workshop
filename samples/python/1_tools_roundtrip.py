import os, json
from openai import OpenAI

# 1. initialize
base = os.getenv("ADP_BASE_URL"); key = os.getenv("ADP_API_KEY"); model = os.getenv("ADP_MODEL","deepseek-r1")
HEAD = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

client = OpenAI(
    api_key=key,
    base_url=base,
)

# 2. define function 
def get_weather(city):
    return {"temperature": 22, "conditions": "sunny"}  # 예시 데이터

# 3. main process
if __name__ == "__main__":
    # [Step1] model propose tools
    response = client.chat.completions.create(
        model=os.getenv("ADP_MODEL", "deepseek-r1"),
        messages=[{"role": "user", "content": "how is weather in seoul"}],
        tools=[{
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather by city name",
                "parameters": {"type": "object", "properties": {"city": {"type": "string"}}},
            }
        }]
    )
    
    # [Step 2] run tool_call
    tool_call = response.choices[0].message.tool_calls[0]
    weather = get_weather(json.loads(tool_call.function.arguments)["city"])
    
    # [Step 3] apply tool_call result and final response
    final_response = client.chat.completions.create(
        model=os.getenv("ADP_MODEL", "deepseek-r1"),
        messages=[
            {"role": "user", "content": "how is weather in seoul"},
            response.choices[0].message,
            {"role": "tool", "content": json.dumps(weather), "tool_call_id": tool_call.id}
        ]
    )
    print("final answer:", final_response.choices[0].message.content)