"""Cada ejecución conserva configuración y evidencia independiente del esquema histórico."""
import json
import sqlite3
from pathlib import Path


class Store:
    def __init__(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY, created_at TEXT NOT NULL, metadata_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS samples (
                run_id TEXT NOT NULL REFERENCES runs(run_id), domain TEXT NOT NULL,
                categories TEXT NOT NULL, validation_status TEXT NOT NULL,
                profile TEXT NOT NULL, qtype TEXT NOT NULL, round INTEGER NOT NULL,
                status TEXT NOT NULL, reason TEXT NOT NULL, evidence_json TEXT NOT NULL,
                PRIMARY KEY(run_id, domain, profile, qtype, round)
            );
        """)

    def start(self, run_id, created_at, metadata):
        self.connection.execute("INSERT INTO runs VALUES(?,?,?)", (run_id, created_at, json.dumps(metadata, ensure_ascii=False)))
        self.connection.commit()

    def save(self, run_id, row, profile, qtype, round_number, status, reason, evidence):
        self.connection.execute("INSERT INTO samples VALUES(?,?,?,?,?,?,?,?,?,?)", (
            run_id, row["domain"], row["categories"], row["validation_status"], profile,
            qtype, round_number, status, reason, json.dumps(evidence, ensure_ascii=False)))
        self.connection.commit()

    def close(self):
        self.connection.close()
