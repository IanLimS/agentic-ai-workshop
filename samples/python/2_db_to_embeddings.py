"""
Turn a SQLite DB into a text snapshot for KB upload (plus optional embeddings).
Assumes a local SQLite file 'sample.db'. Tries best-effort to extract a 'products' table.
Outputs:
  - artifacts/embeddings/products_snapshot.md
  - artifacts/embeddings/products_embeddings.jsonl (placeholder vectors for demo)
"""
import os, sqlite3, json, math, hashlib
from pathlib import Path

DB_PATH = Path("sample.db")
ART = Path("artifacts/embeddings")
ART.mkdir(parents=True, exist_ok=True)

SNAP = ART / "products_snapshot.md"
EMB  = ART / "products_embeddings.jsonl"

def simple_embed(text: str, dim: int = 32):
    # Dummy embedding to keep the example self-contained (not calling external APIs here).
    # Hash -> deterministic pseudo-vector (for illustration only).
    h = hashlib.sha256(text.encode("utf-8")).digest()
    nums = [b for b in h[:dim]]
    norm = (sum(n*n for n in nums) or 1.0) ** 0.5
    return [round(n/norm, 6) for n in nums]

if not DB_PATH.exists():
    raise SystemExit("sample.db not found. Copy your SQLite file to ./sample.db then re-run.")

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Probe schema
tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")]
target = None
for name in tables:
    cols = [r[1] for r in c.execute(f"PRAGMA table_info({name})")]
    if any("name" in col.lower() for col in cols) and any("sku" in col.lower() for col in cols):
        target = name
        break
if target is None and tables:
    target = tables[0]

rows = list(c.execute(f"SELECT * FROM {target}"))
cols = [r[1] for r in c.execute(f"PRAGMA table_info({target})")]

with SNAP.open("w", encoding="utf-8") as f:
    f.write(f"# Product Snapshot from table `{target}`\n\n")
    f.write("| " + " | ".join(cols) + " |\n")
    f.write("|" + "|".join(["---"]*len(cols)) + "|\n")
    for row in rows[:200]:
        f.write("| " + " | ".join(str(v) if v is not None else "" for v in row) + " |\n")

with EMB.open("w", encoding="utf-8") as f:
    for row in rows[:200]:
        text = " ".join(str(v) for v in row if v is not None)
        vec = simple_embed(text)
        f.write(json.dumps({"text": text, "embedding": vec}) + "\n")

conn.close()
print(f"Wrote: {SNAP}")
print(f"Wrote: {EMB}")
