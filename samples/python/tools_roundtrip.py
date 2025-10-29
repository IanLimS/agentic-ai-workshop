import os, json, requests
base, key, model = os.getenv("ADP_BASE_URL"), os.getenv("ADP_API_KEY"), os.getenv("ADP_MODEL","deepseek-r1")
HEAD = {"Authorization": f"Bearer {key}", "Content-Type":"application/json"}

tools = [{
  "type":"function",
  "function":{
    "name":"get_order_status",
    "description":"Lookup order status by order_number",
    "parameters":{
      "type":"object",
      "properties":{"order_number":{"type":"string"}},
      "required":["order_number"]
    }
  }
}]

# 1) Model proposes tool call(s)
resp = requests.post(f"{base}/chat/completions", headers=HEAD, json={
  "model": model,
  "messages":[{"role":"user","content":"ORD-20251025-001 주문 상태 알려줘"}],
  "tools": tools,
  "tool_choice": "auto"
}).json()

choice = resp["choices"][0]
msg = choice["message"]
calls = msg.get("tool_calls", [])

# 2) Execute the tool(s) (fake response)
tool_results = []
for call in calls:
  if call["type"] == "function" and call["function"]["name"] == "get_order_status":
    args = json.loads(call["function"]["arguments"])
    tool_results.append({
      "role":"tool",
      "tool_call_id": call["id"],
      "content": json.dumps({"order_number": args["order_number"], "status":"delivered"})
    })

# 3) Send tool results back -> final answer
final = requests.post(f"{base}/chat/completions", headers=HEAD, json={
  "model": model,
  "messages":[msg] + tool_results
}).json()
print(final["choices"][0]["message"]["content"])