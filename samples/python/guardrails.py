"""
Guardrails: input moderation/PII check, tool-call allowlist, simple output filter.
"""
import os, re, requests
from urllib.parse import urlparse

OPENAI_BASE = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
OPENAI_KEY  = os.getenv('OPENAI_API_KEY')

PII_RE = re.compile(r"(\b\d{3}-\d{2}-\d{4}\b|\b\d{6}-\d{7}\b|\b\d{16}\b)")  # SSN / KR-RRN / naive CC

class Block(Exception):
    pass

def guard_input(text: str):
    if PII_RE.search(text or ""):
        raise Block('PII detected. Please redact sensitive numbers before proceeding.')
    if OPENAI_KEY:
        r = requests.post(f"{OPENAI_BASE}/moderations",
                          headers={'Authorization': f'Bearer {OPENAI_KEY}', 'Content-Type':'application/json'},
                          json={'model':'omni-moderation-latest','input': text},
                          timeout=30)
        r.raise_for_status()
        out = r.json()
        flagged = out.get('results', [{}])[0].get('flagged', False)
        if flagged:
            raise Block('Content flagged by moderation policy.')
    return True

ALLOWED_HOSTS = {'api.example.com', 'api.github.com'}

def guard_tool(url: str):
    host = urlparse(url).hostname or ''
    if host not in ALLOWED_HOSTS:
        raise Block(f'Tool call blocked: host {host} not in allowlist')
    return True

def guard_output(text: str) -> str:
    banned = ['how to build a bomb', 'bypass copyright']
    if any(b in (text or '').lower() for b in banned):
        return 'Response redacted due to policy. Please rephrase your request.'
    return text or ''
