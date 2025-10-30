import os, sys, json, requests
from openai import OpenAI
base = os.getenv("ADP_BASE_URL"); key = os.getenv("ADP_API_KEY"); model = os.getenv("ADP_MODEL","deepseek-r1")
HEAD = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}

print("Non-Streaming")
# 1) Non-streaming
client = OpenAI(
    api_key=key,
    base_url=base,
)

messages = [
    {'role': 'user', 'content': 'hello'},
    {'role': 'assistant', 'content': 'hi, how can I assist you?'},
    {'role': 'user', 'content': 'Which is greater, 9.9 or 9.11?'}
]

completion = client.chat.completions.create(
    model="deepseek-r1",  
    messages=messages
)

print("="*20+"first-round dialogue"+"="*20)
print("="*20+"reasoning_content"+"="*20)
print(completion.choices[0].message.reasoning_content)
print("="*20+"content"+"="*20)
print(completion.choices[0].message.content)

messages.append({'role': 'assistant', 'content': completion.choices[0].message.content})
messages.append({'role': 'user', 'content': 'who are you'})
print("="*20+"second-round dialogue"+"="*20)
completion = client.chat.completions.create(
    model="deepseek-r1",
    messages=messages
)
print("="*20+"reasoning_content"+"="*20)
print(completion.choices[0].message.reasoning_content)
print("="*20+"content"+"="*20)
print(completion.choices[0].message.content)


print("Streaming")
# 2) Streaming (SSE)

client = OpenAI(
    api_key=key,
    base_url=base,
)

def main():
    reasoning_content = ""
    answer_content = ""     
    is_answering = False
    
    # Create chat completion request
    stream = client.chat.completions.create(
        model="deepseek-r1",  
        messages=[
            {"role": "user", "content": "Which is greater, 9.9 or 9.11?"}
        ],
        stream=True
    )

    print("\n" + "=" * 20 + "reasoning processes" + "=" * 20 + "\n")

    for chunk in stream:
        # Process Usage Information
        if not getattr(chunk, 'choices', None):
            print("\n" + "=" * 20 + "Token usage" + "=" * 20 + "\n")
            print(chunk.usage)
            continue

        delta = chunk.choices[0].delta

        if not getattr(delta, 'reasoning_content', None) and not getattr(delta, 'content', None):
            continue

        if not getattr(delta, 'reasoning_content', None) and not is_answering:
            print("\n" + "=" * 20 + "reasoning_content" + "=" * 20 + "\n")
            is_answering = True

        if getattr(delta, 'reasoning_content', None):
            print(delta.reasoning_content, end='', flush=True)
            reasoning_content += delta.reasoning_content
        elif getattr(delta, 'content', None):
            print(delta.content, end='', flush=True)
            answer_content += delta.content

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"error：{e}")
