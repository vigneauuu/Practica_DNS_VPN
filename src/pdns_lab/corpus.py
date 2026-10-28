"""Corpus con procedencia, etiquetas múltiples y revisión explícita."""
import csv
import hashlib
import ipaddress
import json
import re
from pathlib import Path

FIELDS = ["domain", "categories", "sources", "validation_status", "validation_evidence", "reviewer", "reviewed_at"]
CATEGORIES = {"adultos", "armas", "apuestas", "phishing", "popular", "educativo", "referencia_biblioteca", "control_tecnico"}
LEGACY = {
    "adultos_top400.csv": ("adultos", "UT1; snapshot heredado, fecha de extracción desconocida"),
    "armas_top400.csv": ("armas", "UT1; snapshot heredado, fecha de extracción desconocida"),
    "casinos_top400.csv": ("apuestas", "StevenBlack y selección manual; snapshot heredado"),
    "recientes_top400.csv": ("phishing", "Phishing.Database; no acredita antigüedad ni actividad actual"),
    "tranco_top400.csv": ("popular", "Tranco; ID y fecha originales no conservados"),
}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalize_domain(value):
    value = value.strip().lower().rstrip(".")
    try:
        ipaddress.ip_address(value)
    except ValueError:
        pass
    else:
        raise ValueError("Una IP no es un nombre de dominio")
    try:
        name = value.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise ValueError("IDNA inválido") from exc
    if len(name) > 253 or "." not in name:
        raise ValueError("Se requiere un nombre de dominio completo")
    for label in name.split("."):
        if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label):
            raise ValueError("Etiqueta DNS inválida o URL en lugar de dominio")
    return name


def write_corpus(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_corpus(path):
    with Path(path).open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if not set(FIELDS).issubset(reader.fieldnames or []):
            raise ValueError("El corpus no tiene las columnas requeridas")
        rows = list(reader)
    seen = set()
    for row in rows:
        row["domain"] = normalize_domain(row["domain"])
        if row["domain"] in seen:
            raise ValueError("El corpus debe tener una fila por dominio")
        seen.add(row["domain"])
        cats = set(row["categories"].split("|"))
        if not cats or not cats <= CATEGORIES:
            raise ValueError(f"Categoría desconocida: {cats}")
        if row["validation_status"] not in {"pending", "validated", "excluded"}:
            raise ValueError("Estado de validación desconocido")
        if row["validation_status"] == "validated" and not all(row[k].strip() for k in ("validation_evidence", "reviewer", "reviewed_at")):
            raise ValueError("Una etiqueta validada requiere evidencia, responsable y fecha")
    return rows


def build_legacy(source, output):
    """Conserva las etiquetas de origen sin convertirlas en verdad de referencia."""
    source, output = Path(source), Path(output)
    if output.exists():
        raise ValueError("El corpus ya existe; elija otra salida para conservar las revisiones")
    domains, invalid, inputs, count = {}, [], [], 0
    for filename, (category, description) in LEGACY.items():
        path = source / filename
        digest = sha256(path)
        file_rows = list(csv.reader(path.open(encoding="utf-8")))
        inputs.append({"file": filename, "sha256": digest, "rows": len(file_rows)})
        for line, row in enumerate(file_rows, 1):
            if not row:
                continue
            count += 1
            try:
                domain = normalize_domain(row[0])
            except ValueError as exc:
                invalid.append({"file": filename, "line": line, "value": row[0], "reason": str(exc)})
                continue
            item = domains.setdefault(domain, {"categories": set(), "sources": []})
            item["categories"].add(category)
            item["sources"].append({"file": filename, "line": line, "sha256": digest, "description": description})
    rows = [{"domain": domain, "categories": "|".join(sorted(item["categories"])),
             "sources": json.dumps(item["sources"], ensure_ascii=False, sort_keys=True),
             "validation_status": "pending", "validation_evidence": "", "reviewer": "", "reviewed_at": ""}
            for domain, item in sorted(domains.items())]
    write_corpus(output, rows)
    audit = {"input_rows": count, "unique_valid_domains": len(rows), "invalid_rows": invalid,
             "multilabel_domains": sum("|" in r["categories"] for r in rows),
             "category_memberships": {c: sum(c in r["categories"].split("|") for r in rows) for c in sorted(CATEGORIES)},
             "inputs": inputs, "corpus_sha256": sha256(output), "validation": "pending; no revisión semántica automática"}
    output.with_suffix(".audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    return audit
