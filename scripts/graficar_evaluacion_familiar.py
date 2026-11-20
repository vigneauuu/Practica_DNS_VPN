"""Grafica la evaluación de perfiles familiares de DNS4EU, Cloudflare y AdGuard."""
from argparse import ArgumentParser
from pathlib import Path
import json

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from graficar_ampliacion import GRID, INK, configure_matplotlib


COLOR_SENAL = "#7B4A83"
COLOR_ORDINARIA = "#007F86"
COLOR_OMISION = "#D99100"
COLOR_SIN_REF = "#C9D2D6"


def build_rows(dns4eu_data, fam_base_data, fam_ofcom_data):
    """Construye filas verificadas por operador, categoría y tipo (A / AAAA)."""
    rows = []

    dns4eu_res = dns4eu_data["resultados_por_dominio"]
    for cat, label, expected_n in (
        ("apuestas", "DNS4EU infantil · Apuestas", 42),
        ("adultos", "DNS4EU infantil · Adulto", 4),
        ("armas", "DNS4EU infantil · Armas", 3),
        ("educativo", "DNS4EU infantil · Educativo", 39),
    ):
        entry = {"label": f"{label} (n={expected_n})", "n": expected_n, "group": "dns4eu"}
        for qtype in ("A", "AAAA"):
            c = dns4eu_res[cat][qtype]
            senal = c.get("restriccion_observada", 0)
            ordinaria = c.get("resolucion_observada", 0)
            omision = c.get("sin_senal", 0)
            sin_ref = c.get("sin_referencia", 0)
            if senal + ordinaria + omision + sin_ref != expected_n:
                raise ValueError(f"Suma inesperada en DNS4EU {cat} {qtype}: {c}")
            entry[qtype] = (senal, omision, ordinaria, sin_ref)
        rows.append(entry)

    for op_key, op_label in (("cloudflare", "Cloudflare familiar"), ("adguard", "AdGuard familiar")):
        b = fam_base_data["por_dominio"][op_key]
        o = fam_ofcom_data["por_dominio"][op_key]

        entry_ad = {"label": f"{op_label} · Adulto (n=22)", "n": 22, "group": op_key}
        for qtype in ("A", "AAAA"):
            cb = b[qtype]["adultos"]
            co = o[qtype]["adultos"]
            senal = cb.get("restriccion_observada", 0) + co.get("restriccion_observada", 0)
            omision = cb.get("sin_senal", 0) + co.get("sin_senal", 0)
            ordinaria = cb.get("resolucion_observada", 0) + co.get("resolucion_observada", 0)
            sin_ref = cb.get("sin_referencia", 0) + co.get("sin_referencia", 0)
            if senal + ordinaria + omision + sin_ref != 22:
                raise ValueError(f"Suma inesperada en {op_key} adultos {qtype}")
            entry_ad[qtype] = (senal, omision, ordinaria, sin_ref)
        rows.append(entry_ad)

        entry_ed = {"label": f"{op_label} · Educativo (n=39)", "n": 39, "group": op_key}
        for qtype in ("A", "AAAA"):
            ce = b[qtype]["educativo"]
            senal = ce.get("restriccion_observada", 0) + ce.get("bloqueo_indebido", 0)
            omision = 0
            ordinaria = ce.get("resolucion_observada", 0)
            sin_ref = ce.get("sin_referencia", 0)
            if senal + ordinaria + omision + sin_ref != 39:
                raise ValueError(f"Suma inesperada en {op_key} educativo {qtype}")
            entry_ed[qtype] = (senal, omision, ordinaria, sin_ref)
        rows.append(entry_ed)

    return rows


def render(dns4eu_path, fam_base_path, fam_ofcom_path, output_path):
    dns4eu_data = json.loads(dns4eu_path.read_text(encoding="utf-8"))
    fam_base_data = json.loads(fam_base_path.read_text(encoding="utf-8"))
    fam_ofcom_data = json.loads(fam_ofcom_path.read_text(encoding="utf-8"))
    rows = build_rows(dns4eu_data, fam_base_data, fam_ofcom_data)

    positions = [0.0, 0.9, 1.8, 2.7, 4.05, 4.95, 6.3, 7.2]
    dividers = [3.375, 5.625]

    configure_matplotlib()
    plt.rcParams.update({"font.size": 8.5})
    fig, axes = plt.subplots(1, 2, figsize=(7.45, 3.85), sharey=True)

    segments_spec = (
        (COLOR_SENAL, "white", "Señal de restricción"),
        (COLOR_OMISION, "white", "Sin señal (categoría declarada)"),
        (COLOR_ORDINARIA, "white", "Resolución sin señal (educativo)"),
        (COLOR_SIN_REF, INK, "Sin referencia comparable"),
    )

    for ax, qtype in zip(axes, ("A", "AAAA")):
        ax.text(50.0, -1.05, f"Registros {qtype}", ha="center", va="bottom",
                fontsize=9.5, fontweight="bold", color=INK)
        for y, row in zip(positions, rows):
            n = row["n"]
            vals = row[qtype]
            left = 0.0
            for val, (color, tcolor, _) in zip(vals, segments_spec):
                if not val:
                    continue
                pct = 100.0 * val / n
                ax.barh(y, pct, left=left, height=0.66, color=color,
                        edgecolor="white", linewidth=0.7, zorder=3)
                if pct >= 13.0:
                    ax.text(left + pct / 2.0, y, f"{val}",
                            ha="center", va="center", color=tcolor,
                            fontsize=8, fontweight="bold", zorder=4)
                left += pct
            senal, omision, ordinaria, sin_ref = vals
            small_notes = []
            if senal and (100.0 * senal / n) < 13.0:
                small_notes.append(f"{senal} señal")
            if omision and (100.0 * omision / n) < 13.0:
                small_notes.append(f"{omision} sin señal")
            if sin_ref and (100.0 * sin_ref / n) < 13.0:
                small_notes.append(f"{sin_ref} s/ref.")
            if small_notes:
                ax.text(102.2, y, "\n".join(small_notes), ha="left", va="center",
                        fontsize=6.8, linespacing=1.08, color=INK)

        for div in dividers:
            ax.plot([0, 100], [div, div], color=GRID, linewidth=0.8, linestyle="--", zorder=1)

        ax.set_xlim(0, 134)
        ax.set_xticks([0, 25, 50, 75, 100], ["0%", "25%", "50%", "75%", "100%"])
        ax.text(50.0, 8.85, "Proporción de dominios evaluados", ha="center", va="top",
                fontsize=8.2, color=INK)
        ax.xaxis.grid(True, color=GRID, linewidth=0.5, zorder=0)
        ax.set_axisbelow(True)
        ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
        ax.plot([0, 100], [7.82, 7.82], color=GRID, linewidth=0.8, zorder=2)
        ax.tick_params(axis="both", length=0, labelsize=8)

    axes[0].set_yticks(positions, [r["label"] for r in rows])
    axes[0].set_ylim(7.85, -0.65)

    legend_handles = [
        Patch(facecolor=color, edgecolor="white", label=label)
        for color, _, label in segments_spec
    ]
    fig.legend(handles=legend_handles, loc="lower center", ncol=2,
               frameon=False, fontsize=8, bbox_to_anchor=(0.54, 0.005))
    fig.subplots_adjust(left=0.33, right=0.985, top=0.89, bottom=0.23, wspace=0.08)
    fig.savefig(output_path, format="pdf", metadata={"CreationDate": None, "ModDate": None})
    plt.close(fig)


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("dns4eu", type=Path)
    parser.add_argument("fam_base", type=Path)
    parser.add_argument("fam_ofcom", type=Path)
    parser.add_argument("salida", type=Path)
    args = parser.parse_args()
    render(args.dns4eu, args.fam_base, args.fam_ofcom, args.salida)


if __name__ == "__main__":
    main()
