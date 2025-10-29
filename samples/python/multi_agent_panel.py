#!/usr/bin/env python3
"""
Query OpenAI and Claude, then ask an ADP (OpenAI-compatible) judge model (e.g., DeepSeek R1) to synthesize a final answer.
"""
import os, requests

OPENAI_BASE = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
OPENAI_KEY  = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL= os.getenv('OPENAI_MODEL', 'gpt-4.1-mini')

ANTH_BASE   = os.getenv('ANTHROPIC_BASE_URL', 'https://api.anthropic.com/v1')
ANTH_KEY    = os.getenv('ANTHROPIC_API_KEY')
ANTH_MODEL  = os.getenv('ANTHROPIC_MODEL', 'claude-3.7-sonnet')

ADP_BASE    = os.getenv('ADP_BASE_URL')  # judge
ADP_KEY     = os.getenv('ADP_API_KEY')
ADP_MODEL   = os.getenv('ADP_MODEL', 'deepseek-r1')

QUESTION = os.getenv('QUESTION', 'Give me a 5-step plan to add guardrails to a RAG agent.')

def ask_openai(q: str) -> str:
    r = requests.post(f"{OPENAI_BASE}/chat/completions",
                      headers={'Authorization': f'Bearer {OPENAI_KEY}', 'Content-Type': 'application/json'},
                      json={'model': OPENAI_MODEL, 'messages':[{'role':'user','content':q}]},
                      timeout=60)
    r.raise_for_status()
    return r.json()['choices'][0]['message']['content']

def ask_claude(q: str) -> str:
    r = requests.post(f"{ANTH_BASE}/messages",
                      headers={'x-api-key': ANTH_KEY, 'anthropic-version':'2023-06-01', 'content-type':'application/json'},
                      json={'model': ANTH_MODEL, 'max_tokens': 800, 'messages':[{'role':'user','content':q}]},
                      timeout=60)
    r.raise_for_status()
    data = r.json()
    return ''.join([b.get('text','') for b in data.get('content', [])])

def judge(a1: str, a2: str, q: str) -> str:
    prompt = f"""
You are an impartial judge. Compare Answer A and Answer B to the same question.
- Identify agreement and conflict.
- Produce one concise, actionable final answer.
Question:
{q}

Answer A (OpenAI):
{a1}

Answer B (Claude):
{a2}
""".strip()
    r = requests.post(f"{ADP_BASE}/chat/completions",
                      headers={'Authorization': f'Bearer {ADP_KEY}', 'Content-Type': 'application/json'},
                      json={'model': ADP_MODEL,
                            'messages':[
                                {'role':'system','content':'You are a careful, concise arbiter.'},
                                {'role':'user','content': prompt}
                            ]},
                      timeout=60)
    r.raise_for_status()
    return r.json()['choices'][0]['message']['content']

def main():
    a1 = ask_openai(QUESTION)
    a2 = ask_claude(QUESTION)
    final = judge(a1, a2, QUESTION)
    print("=== OpenAI ===\n", a1)
    print("\n=== Claude ===\n", a2)
    print("\n=== Final (Arbiter) ===\n", final)

if __name__ == "__main__":
    main()
