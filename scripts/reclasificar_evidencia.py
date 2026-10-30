"""Reinterpreta una ejecución conservando la base original y sus mensajes."""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import uuid
from pdns_lab.dnsprobe import classify, utcnow
from pdns_lab.storage import Store
import pdns_lab.dnsprobe as classifier


def reclassify(source, run_id, output):
    source, output = Path(source), Path(output)
    if source.resolve() == output.resolve() or output.exists():
        raise ValueError("La salida debe ser una base nueva distinta de la original")
    con = sqlite3.connect(f"file:{source.resolve()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        run = con.execute("SELECT * FROM runs WHERE run_id=?", (run_id,)).fetchone()
        if run is None:
            raise ValueError("Ejecución no encontrada")
        meta = json.loads(run["metadata_json"])
        samples = list(con.execute("SELECT * FROM samples WHERE run_id=?", (run_id,)))
    finally:
        con.close()
    if len(samples) != meta.get("expected_samples"):
        raise ValueError("Se requiere una ejecución original completa")
    profiles = {p["id"]: p for p in meta["profiles"]}
    domains = {r["domain"]: r for r in meta["corpus_rows"]}
    meta["reclassification"] = {
        "source_run_id": run_id,
        "source_db_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "classifier_sha256": hashlib.sha256(Path(classifier.__file__).read_bytes()).hexdigest(),
        "reason": "EDE 18 no acredita por sí solo filtrado de contenido; RFC 8914, 4.19",
        "network_repeated": False,
    }
    derived_id = str(uuid.uuid4())
    changes = []
    store = Store(output)
    try:
        store.start(derived_id, utcnow(), meta)
        for row in samples:
            evidence = json.loads(row["evidence_json"])
            before, after = evidence.get("control_before"), evidence.get("control_after")
            status, reason = classify(evidence["target"]["final"],
                before["final"] if before else None, after["final"] if after else None,
                profiles[row["profile"]])
            if (status, reason) != (row["status"], row["reason"]):
                changes.append({"domain": row["domain"], "profile": row["profile"],
                    "qtype": row["qtype"], "round": row["round"],
                    "previous_status": row["status"], "status": status,
                    "previous_reason": row["reason"], "reason": reason})
            store.save(derived_id, domains[row["domain"]], row["profile"], row["qtype"],
                       row["round"], status, reason, evidence)
    finally:
        store.close()
    return {"run_id": derived_id, "source_run_id": run_id,
            "samples": len(samples), "changed": len(changes), "changes": changes,
            "provenance": meta["reclassification"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(json.dumps(reclassify(args.source, args.run_id, args.output), ensure_ascii=False, indent=2))
