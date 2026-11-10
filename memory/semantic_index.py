"""Small local semantic-style memory index using SQLite FTS5 with safe fallback scoring.

This is lexical retrieval, not an embedding model. It works offline and stays lightweight.
"""
from __future__ import annotations
import re
import sqlite3
from pathlib import Path
import os

DB_PATH = Path(os.environ.get("JARVIS_DATA_DIR", Path.home() / ".jarvis")) / "memory_index.sqlite3"

class SemanticMemoryIndex:
    def __init__(self, db_path: str | Path | None = None):
        self.path = Path(db_path or DB_PATH)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS memories (id INTEGER PRIMARY KEY, category TEXT NOT NULL, key TEXT NOT NULL, content TEXT NOT NULL, updated_at TEXT DEFAULT CURRENT_TIMESTAMP, UNIQUE(category,key))")
            try:
                db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(category, key, content, content='memories', content_rowid='id')")
                db.execute("CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN INSERT INTO memories_fts(rowid,category,key,content) VALUES(new.id,new.category,new.key,new.content); END")
                db.execute("CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN INSERT INTO memories_fts(memories_fts,rowid,category,key,content) VALUES('delete',old.id,old.category,old.key,old.content); END")
                db.execute("CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN INSERT INTO memories_fts(memories_fts,rowid,category,key,content) VALUES('delete',old.id,old.category,old.key,old.content); INSERT INTO memories_fts(rowid,category,key,content) VALUES(new.id,new.category,new.key,new.content); END")
                self.fts_available = True
            except sqlite3.OperationalError:
                self.fts_available = False

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.execute("PRAGMA journal_mode=WAL")
        return db

    def upsert(self, category: str, key: str, content: str) -> None:
        text = str(content or "").strip()
        if not text: return
        with self._connect() as db:
            db.execute("INSERT INTO memories(category,key,content) VALUES(?,?,?) ON CONFLICT(category,key) DO UPDATE SET content=excluded.content, updated_at=CURRENT_TIMESTAMP", (str(category)[:60], str(key)[:120], text[:4000]))

    def search(self, query: str, limit: int = 8) -> list[dict]:
        query = str(query or "").strip()
        if not query: return []
        limit = max(1, min(int(limit), 25))
        with self._connect() as db:
            if self.fts_available:
                terms = [t for t in re.findall(r"[\w-]+", query) if len(t) > 1][:12]
                if terms:
                    match = " OR ".join('"' + t.replace('"','') + '"' for t in terms)
                    try:
                        rows = db.execute("SELECT m.category,m.key,m.content,bm25(memories_fts) AS score FROM memories_fts f JOIN memories m ON m.id=f.rowid WHERE memories_fts MATCH ? ORDER BY score LIMIT ?", (match, limit)).fetchall()
                        return [{"category":r[0],"key":r[1],"content":r[2],"score":float(r[3])} for r in rows]
                    except sqlite3.OperationalError:
                        pass
            rows = db.execute("SELECT category,key,content FROM memories").fetchall()
        terms = {t.lower() for t in re.findall(r"[\w-]+", query) if len(t) > 1}
        ranked = []
        for category, key, content in rows:
            hay = f"{category} {key} {content}".lower()
            score = sum(hay.count(term) for term in terms)
            if score: ranked.append((score, category, key, content))
        ranked.sort(reverse=True)
        return [{"category":c,"key":k,"content":v,"score":s} for s,c,k,v in ranked[:limit]]

    def delete(self, category: str, key: str) -> bool:
        with self._connect() as db:
            cur = db.execute("DELETE FROM memories WHERE category=? AND key=?", (category, key))
            return cur.rowcount > 0
