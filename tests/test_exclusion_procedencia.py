"""La procedencia incompatible solo retira la etiqueta afectada para medir."""
import json

from pdns_lab.corpus import UT1_AGRESSIF_SHA256, build_legacy, experimental_rows, read_corpus


def test_inventario_y_piloto_conservan_sus_fuentes(tmp_path):
    corpus = tmp_path / "historico.csv"
    build_legacy("dataset", corpus)
    historical = read_corpus(corpus)
    projected = list(experimental_rows(historical))
    assert len(projected) == len(historical) - 266
    assert sum(r["categories"] == "armas" for r in historical) == 266
    assert all("armas" not in r["categories"].split("|") for r in projected)
    pilot = list(experimental_rows(read_corpus("dataset/piloto-50-2026-10-30.csv")))
    assert sum(r["categories"] == "armas" for r in pilot) == 3


def test_etiqueta_adicional_y_revision_individual():
    row = {"categories": "armas|popular", "validation_status": "pending",
           "sources": json.dumps([{"sha256": UT1_AGRESSIF_SHA256}])}
    assert list(experimental_rows([row])) == [{**row, "categories": "popular"}]
    assert row["categories"] == "armas|popular"
    reviewed = {**row, "validation_status": "validated", "validation_evidence": "fuente individual",
                "reviewer": "responsable", "reviewed_at": "2026-11-19"}
    assert list(experimental_rows([reviewed])) == [reviewed]
    assert not list(experimental_rows([{**row, "validation_status": "excluded"}]))
