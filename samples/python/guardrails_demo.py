#!/usr/bin/env python3
from guardrails import guard_input, guard_tool, guard_output, Block

def run(query: str):
    try:
        guard_input(query)
        guard_tool('https://api.github.com/search/repositories?q=agent')
        # ... call LLM & tools ... (omitted in demo)
        raw = "Here is your safe answer."
        final = guard_output(raw)
        return final
    except Block as e:
        return f"Blocked: {e}"

if __name__ == '__main__':
    print(run('Find OSS repos about agentic ai. My SSN is 123-45-6789'))
