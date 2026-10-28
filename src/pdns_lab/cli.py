"""Interfaz reproducible: preparar, revisar, medir, analizar e intercambiar con OONI."""
import argparse
from datetime import datetime, timezone
import ipaddress
import json
import os
from pathlib import Path
import platform
import random
import subprocess
import sys
import uuid

from . import __version__
from .corpus import build_legacy, read_corpus, write_corpus, sha256, normalize_domain, CATEGORIES
from .dnsprobe import probe, classify, utcnow
from .analysis import analyze
from .storage import Store
from .study import plan_study, select_study, build_parental_candidates
from .ooni import export_urls, import_measurements
from .http_probe import probe_http


def dump(value, output=None):
    text = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+"\n"
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def load_profiles(path, selected):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    profiles = data["profiles"]
    identifiers = [p["id"] for p in profiles]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("IDs de perfil repetidos")
    chosen = set(selected.split(",")) if selected else {p["id"] for p in profiles if p.get("enabled", False)}
    if not chosen or not chosen <= set(identifiers):
        raise ValueError("Seleccione perfiles existentes")
    result = [p for p in profiles if p["id"] in chosen]
    for p in result:
        ipaddress.ip_address(p["endpoint"])
        if p.get("reference"):
            ipaddress.ip_address(p["reference"])
        if p.get("transport", "udp") not in {"udp", "tcp"}:
            raise ValueError("Transporte DNS no implementado")
        if p.get("kind") not in {"dns", "vpn"}:
            raise ValueError("Use http-probe para proxies HTTP/SOCKS")
        if p.get("fingerprint_ips") and not p.get("fingerprint_source"):
            raise ValueError("Las huellas de bloqueo requieren una fuente")
    return result


def context_snapshot(context_path, profiles, *, check=False):
    context = json.loads(Path(context_path).read_text()) if context_path else {"kind": "direct", "note": "No se acredita la ruta mediante túnel"}
    if not isinstance(context, dict):
        raise ValueError("El contexto debe ser un objeto JSON")
    if any(p["kind"] == "vpn" for p in profiles):
        if not context_path or context.get("kind") != "vpn" or not context.get("interface") or not context.get("filter_setting"):
            raise ValueError("Una VPN requiere contexto con interface y filter_setting")
        if any("REEMPLAZAR" in str(context[k]) for k in ("interface", "filter_setting")):
            raise ValueError("Complete la plantilla con la configuración real antes de medir")
        if check:
            interface = context["interface"]
            link = subprocess.run(["ip", "-j", "link", "show", "dev", interface], capture_output=True, text=True, check=True)
            states = json.loads(link.stdout)
            if not states or "UP" not in states[0].get("flags", []):
                raise ValueError("La interfaz VPN no está activa")
            routes = {}
            for p in profiles:
                if p["kind"] != "vpn":
                    continue
                route = json.loads(subprocess.check_output(["ip", "-j", "route", "get", p["endpoint"]], text=True))
                if not route or route[0].get("dev") != interface:
                    raise ValueError("El resolutor VPN no se enruta por la interfaz declarada")
                routes[p["id"]] = route
            context["observed_routes"] = routes
    context["platform"] = platform.platform()
    context["python"] = platform.python_version()
    return context


def run(args):
    if args.rounds < 1 or args.retries < 0 or args.timeout <= 0 or args.interval < 0 or (args.limit is not None and args.limit < 1):
        raise ValueError("Parámetros de ejecución fuera de rango")
    profiles = load_profiles(args.profiles, args.select)
    rows = [r for r in read_corpus(args.corpus) if r["validation_status"] != "excluded" and (args.include_unreviewed or r["validation_status"] == "validated")]
    if not rows:
        raise ValueError("No hay dominios validados. Revise etiquetas o use --include-unreviewed para una ejecución exploratoria explícita")
    rng = random.Random(args.seed)
    rng.shuffle(rows)
    rows = rows[:args.limit] if args.limit else rows
    qtypes = args.qtypes.split(",")
    if not set(qtypes) <= {"A", "AAAA"}:
        raise ValueError("Se soportan A y AAAA, especificados sin espacios")
    if len(qtypes) != len(set(qtypes)):
        raise ValueError("Tipos DNS repetidos")
    context = context_snapshot(args.context, profiles, check=not args.dry_run)
    expected = len(rows)*len(profiles)*len(qtypes)*args.rounds
    probes_per_cell = sum(3 if p.get("reference") else 1 for p in profiles)
    metadata = {"version": __version__, "corpus_sha256": sha256(args.corpus), "profiles_sha256": sha256(args.profiles),
                "profiles": profiles, "corpus_rows": rows, "context": context, "seed": args.seed,
                "qtypes": qtypes, "rounds": args.rounds, "timeout": args.timeout, "retries": args.retries,
                "interval": args.interval, "exploratory": any(r["validation_status"] != "validated" for r in rows),
                "expected_samples": expected, "dns_probe_groups": len(rows)*len(qtypes)*args.rounds*probes_per_cell,
                "max_dns_attempts": len(rows)*len(qtypes)*args.rounds*probes_per_cell*(args.retries+1),
                "note": "Los controles son referencias observacionales, no verdad absoluta de existencia o benignidad"}
    if args.dry_run:
        dump(metadata)
        return
    store = Store(args.db)
    run_id = str(uuid.uuid4())
    store.start(run_id, utcnow(), metadata)
    print(f"run_id={run_id}", flush=True)
    done = 0
    try:
        for round_number in range(1, args.rounds+1):
            for row in rows:
                for qtype in qtypes:
                    order = profiles.copy()
                    rng.shuffle(order)
                    for p in order:
                        reference = p.get("reference")
                        kwargs = {"timeout": args.timeout, "retries": args.retries, "interval": args.interval,
                                  "transport": p.get("transport", "udp")}
                        before = probe(row["domain"], qtype, reference, **kwargs) if reference else None
                        target = probe(row["domain"], qtype, p["endpoint"], source=p.get("source_ip"), **kwargs)
                        after = probe(row["domain"], qtype, reference, **kwargs) if reference else None
                        status, reason = classify(target["final"], before["final"] if before else None, after["final"] if after else None, p)
                        evidence = {"target": target, "control_before": before, "control_after": after}
                        store.save(run_id, row, p["id"], qtype, round_number, status, reason, evidence)
                        done += 1
                        print(f"{done}/{expected} {row['domain']} {p['id']} {qtype}: {status}", flush=True)
    finally:
        store.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("corpus-build")
    build.add_argument("--source", default="dataset")
    build.add_argument("--output", default="dataset/corpus.csv")
    audit = sub.add_parser("corpus-audit")
    audit.add_argument("--corpus", default="dataset/corpus.csv")
    parent = sub.add_parser("corpus-parental-build")
    parent.add_argument("--corpus", default="dataset/corpus.csv")
    parent.add_argument("--study", default="config/estudio.json")
    parent.add_argument("--reference-source", default="dataset/fuentes/ut1_liste_bu_dominios_2026-10-27.txt")
    parent.add_argument("--output", default="dataset/corpus-parental-candidatos.csv")
    plan = sub.add_parser("study-plan")
    plan.add_argument("--corpus", default="dataset/corpus-parental-candidatos.csv")
    plan.add_argument("--study", default="config/estudio.json")
    plan.add_argument("--output")
    select = sub.add_parser("corpus-select")
    select.add_argument("--corpus", default="dataset/corpus-parental-candidatos.csv")
    select.add_argument("--study", default="config/estudio.json")
    select.add_argument("--output", required=True)
    review = sub.add_parser("corpus-review")
    review.add_argument("--corpus", default="dataset/corpus.csv")
    review.add_argument("--domain", required=True)
    review.add_argument("--categories", required=True, help="Etiquetas separadas por |")
    review.add_argument("--evidence", required=True)
    review.add_argument("--reviewer", required=True)
    review.add_argument("--exclude", action="store_true")
    measure = sub.add_parser("run")
    measure.add_argument("--corpus", default="dataset/corpus.csv")
    measure.add_argument("--profiles", default="config/profiles.json")
    measure.add_argument("--select", help="IDs separados por coma")
    measure.add_argument("--db", default="results/mediciones.sqlite3")
    measure.add_argument("--rounds", type=int, default=3)
    measure.add_argument("--qtypes", default="A,AAAA")
    measure.add_argument("--timeout", type=float, default=3)
    measure.add_argument("--retries", type=int, default=1)
    measure.add_argument("--interval", type=float, default=0.2)
    measure.add_argument("--seed", type=int, default=20261027)
    measure.add_argument("--limit", type=int)
    measure.add_argument("--include-unreviewed", action="store_true")
    measure.add_argument("--context")
    measure.add_argument("--dry-run", action="store_true")
    analysis = sub.add_parser("analyze")
    analysis.add_argument("--db", default="results/mediciones.sqlite3")
    analysis.add_argument("--run-id", required=True)
    analysis.add_argument("--output")
    export = sub.add_parser("ooni-export")
    export.add_argument("--corpus", default="dataset/corpus.csv")
    export.add_argument("--output", default="results/ooni-urls.txt")
    importer = sub.add_parser("ooni-import")
    importer.add_argument("path")
    importer.add_argument("--output", default="results/ooni-resumen.json")
    http = sub.add_parser("http-probe")
    http.add_argument("--url", required=True)
    http.add_argument("--proxy-env", help="Nombre de variable con URL del proxy; nunca se guarda el valor")
    http.add_argument("--fingerprints", help="JSON local con lista de textos de bloqueo ya verificados")
    http.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "corpus-build":
            dump(build_legacy(args.source, args.output))
        elif args.command == "corpus-audit":
            rows = read_corpus(args.corpus)
            dump({"domains": len(rows), "sha256": sha256(args.corpus),
                  "states": {s: sum(r["validation_status"] == s for r in rows) for s in ("pending","validated","excluded")},
                  "multilabel_domains": sum("|" in r["categories"] for r in rows)})
        elif args.command == "corpus-parental-build":
            dump(build_parental_candidates(args.corpus, args.study, args.reference_source, args.output))
        elif args.command == "study-plan":
            dump(plan_study(args.corpus, args.study), args.output)
        elif args.command == "corpus-select":
            dump(select_study(args.corpus, args.study, args.output))
        elif args.command == "corpus-review":
            rows = read_corpus(args.corpus)
            categories = set(args.categories.split("|"))
            if not categories <= CATEGORIES or not categories or not args.evidence.strip() or not args.reviewer.strip():
                raise ValueError("Categorías, evidencia o responsable inválidos")
            domain = normalize_domain(args.domain)
            found = False
            for row in rows:
                if row["domain"] == domain:
                    row.update(categories="|".join(sorted(categories)), validation_status="excluded" if args.exclude else "validated",
                               validation_evidence=args.evidence, reviewer=args.reviewer,
                               reviewed_at=datetime.now(timezone.utc).isoformat())
                    found = True
            if not found:
                raise ValueError("El dominio no está en el corpus")
            write_corpus(args.corpus, rows)
        elif args.command == "run":
            run(args)
        elif args.command == "analyze":
            dump(analyze(Path(args.db).resolve(), args.run_id), args.output)
        elif args.command == "ooni-export":
            print(export_urls(read_corpus(args.corpus), args.output))
        elif args.command == "ooni-import":
            dump({"source_sha256": sha256(args.path), "measurements": import_measurements(args.path)}, args.output)
        elif args.command == "http-probe":
            proxy = os.environ.get(args.proxy_env) if args.proxy_env else None
            if args.proxy_env and not proxy:
                raise ValueError("La variable de proxy no está definida")
            fingerprints = json.loads(Path(args.fingerprints).read_text()) if args.fingerprints else []
            if not isinstance(fingerprints, list) or not all(isinstance(s,dict) and isinstance(s.get("text"),str) and s["text"].strip() and isinstance(s.get("source"),str) and s["source"].strip() for s in fingerprints):
                raise ValueError("Cada huella requiere text y source con evidencia de verificación")
            dump(probe_http(args.url, proxy=proxy, fingerprints=fingerprints), args.output)
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        parser.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
