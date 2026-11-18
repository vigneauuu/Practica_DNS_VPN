"""Repite el contraste DNS por perfil y guarda una base independiente por cada uno."""
from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import subprocess
import sys

from pdns_lab.dnsprobe import probe


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--profiles", type=Path, default=Path("config/ampliacion-dns-2026-11-18.json"))
    parser.add_argument("--corpus", type=Path, default=Path("dataset/piloto-50-2026-10-30.csv"))
    args = parser.parse_args()
    args.output.mkdir()
    profiles = json.loads(args.profiles.read_text(encoding="utf-8"))["profiles"]
    cases = ("example.com", "no-existe-pdns-lab.invalid", "nudity.testcategory.com", "malware.testcategory.com")

    def calibrate(profile, names=cases):
        rows = {}
        for name in names:
            for qtype in ("A", "AAAA"):
                rows[f"{name}|{qtype}"] = probe(name, qtype, profile["endpoint"], transport="tcp",
                                               retries=0, interval=.08, timeout=2.5)["final"]
        return profile["id"], rows

    def run(ident):
        command = [
            sys.executable, "-m", "pdns_lab.cli", "run", "--profiles", str(args.profiles),
            "--corpus", str(args.corpus), "--include-unreviewed", "--select", ident,
            "--db", str(args.output / f"{ident}.sqlite3"), "--rounds", "3", "--qtypes", "A,AAAA",
            "--timeout", "2.5", "--retries", "0", "--interval", "0.09", "--seed", "20261118",
        ]
        with (args.output / f"{ident}.log").open("w", encoding="utf-8") as log:
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True)
        print(f"{ident} terminado", flush=True)

    with ThreadPoolExecutor(max_workers=7) as pool:
        calibration = dict(pool.map(calibrate, profiles))
        (args.output / "calibracion.json").write_text(json.dumps(calibration, indent=2) + "\n")
        list(pool.map(run, [profile["id"] for profile in profiles]))
        cisco = dict(calibrate(p, ("example.com", "exampleadultsite.com")) for p in profiles
                     if p["id"] in {"opendns_standard", "opendns_family"})
        (args.output / "calibracion-cisco.json").write_text(json.dumps(cisco, indent=2) + "\n")


if __name__ == "__main__":
    main()
