#!/usr/bin/env python3
"""
Export DB rows -> chunk -> embed via OpenAI-compatible /embeddings (ADP or OpenAI) -> save JSONL vectors
Also writes a Markdown snapshot that you can upload to ADP Knowledge Base for source-grounding.
"""
import os, json, sqlite3, requests
from pathlib import Path

DB_URL = os.getenv('DB_URL', 'sqlite:///sample.db')  # placeholder; demo uses local sqlite file "sample.db"
TABLE  = os.getenv('DB_TABLE', 'products')
OUTDIR = Path(os.getenv('OUTDIR', 'artifacts/embeddings'))
OUTDIR.mkdir(parents=True, exist_ok=True)

BASE_URL = os.getenv('ADP_BASE_URL') or os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
API_KEY  = os.getenv('ADP_API_KEY')  or os.getenv('OPENAI_API_KEY')
EMBED_MODEL = os.getenv('ADP_EMBEDDINGS_MODEL') or os.getenv('OPENAI_EMBEDDINGS_MODEL', 'text-embedding-3-large')

headers = { 'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json' }

def to_chunks(text: str, max_chars: int = 3000):
    return [text[i:i+max_chars] for i in range(0, len(text), max_chars)]

def main():
    # Demo: local sqlite db file "sample.db"
    conn = sqlite3.connect('sample.db')
    c = conn.cursor()
    c.execute(f"CREATE TABLE IF NOT EXISTS {TABLE} (id INTEGER PRIMARY KEY, name TEXT, description TEXT)")
    conn.commit()

    rows = list(c.execute(f"SELECT id, name, description FROM {TABLE}"))
    if not rows:
        demo = [
            (1, 'Hydro Flask 21oz', 'Insulated stainless bottle; keeps cold 24h; BPA-free.'),
            (2, 'Trail Running Shoes', 'Lightweight cushion; rock plate; suitable for 10-30km.'),
            (3, 'Noise-Canceling Headphones', 'ANC, transparency, 30h battery; BT 5.3; AAC/LDAC.'),
        ]
        c.executemany(f"INSERT INTO {TABLE} (id,name,description) VALUES (?,?,?)", demo)
        conn.commit()
        rows = demo

    # Convert to simple Markdown records and chunk
    records = []
    for rid, name, desc in rows:
        md = f"## {name} (#{rid})\n\n{desc}\n\n"
        for i, ch in enumerate(to_chunks(md)):
            rec_id = f"{rid}-{i}"
            records.append({"id": rec_id, "rid": rid, "name": name, "text": ch})

    # Embed in a single batch
    texts = [r['text'] for r in records]
    payload = {"model": EMBED_MODEL, "input": texts}
    resp = requests.post(f"{BASE_URL}/embeddings", headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json().get('data', [])

    vectors = []
    for r, d in zip(records, data):
        vectors.append({
            "id": r["id"],
            "name": r["name"],
            "vector": d.get("embedding"),
            "text": r["text"],
        })

    out_jsonl = OUTDIR / "products_embeddings.jsonl"
    out_md    = OUTDIR / "products_snapshot.md"
    OUTDIR.mkdir(parents=True, exist_ok=True)

    with out_jsonl.open("w", encoding="utf-8") as f:
        for v in vectors:
            f.write(json.dumps(v) + "\n")

    with out_md.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(r["text"] + "\n")

    print(f"Wrote {out_jsonl}")
    print(f"Wrote {out_md} (upload this to ADP KB for reference sources)")

if __name__ == "__main__":
    main()
