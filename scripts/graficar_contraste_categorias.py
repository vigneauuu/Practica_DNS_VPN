"""Compara las respuestas A en las mediciones DoH de Mullvad y DNS4EU."""
from argparse import ArgumentParser
from pathlib import Path
import json

from graficar_ampliacion import configure_matplotlib, INK
import matplotlib.pyplot as plt
from matplotlib.patches import Patch


PROFILES = {
    "mullvad_open": "Mullvad sin filtro",
    "mullvad_family": "Mullvad familiar",
    "dns4eu_unfiltered": "DNS4EU sin filtro",
    "dns4eu_protective": "DNS4EU protector",
    "dns4eu_child": "DNS4EU infantil",
}
GROUPS = {"apuestas": "Apuestas", "educativo": "Educativo", "armas": "Armas"}
STYLES = {
    "NOERROR_con_direccion_del_tipo": ("Otras direcciones A", "#BDD5D7", "", INK),
    "NXDOMAIN": ("NXDOMAIN", "#334C59", "", "white"),
    "NOERROR_direccion_comun": ("51.15.69.11 (DNS4EU)", "#E4CFB1", "///", INK),
    "NOERROR_sin_direccion_del_tipo": ("NOERROR sin A", "white", "////", INK),
}


def read_counts(path):
    evidence = json.loads(path.read_text(encoding="utf-8"))
    names = {
        category: {name for name, row in evidence["recuentos_por_nombre"].items()
                   if row["categoria_documental"] == category}
        for category in GROUPS
    }
    counts = {}
    for row in evidence["recuentos_por_grupo"]:
        category = row["categoria"]
        if category not in GROUPS or row["tipo"] != "A":
            continue
        key = (row["perfil"], category)
        outcomes = row["respuestas"]
        if key in counts or row["perfil"] not in PROFILES:
            raise ValueError(f"Fila duplicada o perfil desconocido: {key}")
        if set(outcomes) - STYLES.keys() or sum(outcomes.values()) != 2 * len(names[category]):
            raise ValueError(f"Formas de respuesta o total inesperados para {key}: {outcomes}")
        counts[key] = outcomes
    return names, counts


def render(mullvad_path, dns4eu_path, output):
    mullvad_names, counts = read_counts(mullvad_path)
    dns4eu_names, dns4eu_counts = read_counts(dns4eu_path)
    for category in ("apuestas", "educativo"):
        if mullvad_names[category] != dns4eu_names[category]:
            raise ValueError(f"Los nombres de {category} difieren entre las mediciones.")
    if mullvad_names["armas"] or not dns4eu_names["armas"]:
        raise ValueError("La figura espera el grupo de armas únicamente en el contraste de DNS4EU.")
    counts.update(dns4eu_counts)
    positions = [0, 1, 2.5, 3.5, 4.5]
    configure_matplotlib()
    figure, axes = plt.subplots(1, len(GROUPS), figsize=(7.2, 2.85), sharex=True, sharey=True)
    maximum = max(2 * len(names) for names in dns4eu_names.values())
    for axis, (category, heading) in zip(axes, GROUPS.items()):
        size = len(dns4eu_names[category])
        axis.set_title(f"{heading}\n{size} nombres", fontsize=9.5)
        for profile, y in zip(PROFILES, positions):
            if profile.startswith("mullvad_") and category == "armas":
                axis.text(0.15, y, "Sin medición", ha="left", va="center", fontsize=7.5)
                continue
            outcomes = counts[profile, category]
            left = 0
            for state, (_, color, hatch, text_color) in STYLES.items():
                value = outcomes.get(state, 0)
                if value:
                    axis.barh(y, value, left=left, height=0.68, color=color, hatch=hatch,
                              edgecolor=INK, linewidth=0.6, zorder=3)
                    axis.text(left + value / 2, y, str(value), ha="center", va="center",
                              color=text_color, fontsize=8, zorder=4,
                              bbox=dict(facecolor=color, edgecolor="none", pad=0.5) if hatch else None)
                    left += value
        axis.axhline(1.75, color="#D0D9DC", linewidth=0.6)
        axis.set_xlim(0, maximum)
        axis.set_xticks(range(0, maximum + 1, 4))
        axis.set_yticks(positions, list(PROFILES.values()))
        axis.tick_params(axis="both", length=0, labelsize=8.5)
        axis.spines[["top", "left", "right"]].set_visible(False)
        axis.grid(axis="x", linewidth=0.5)
    axes[0].set_ylim(5.0, -0.6)
    figure.supxlabel("Consultas A en dos rondas", y=0.13, fontsize=9)
    used = {state for cell in counts.values() for state, n in cell.items() if n}
    legend = [
        Patch(facecolor=color, hatch=hatch, edgecolor=INK, label=label, linewidth=0.6)
        for state, (label, color, hatch, _) in STYLES.items() if state in used
    ]
    figure.legend(handles=legend, loc="lower center", ncols=len(legend), fontsize=8,
                  frameon=False, bbox_to_anchor=(0.55, -0.005))
    figure.subplots_adjust(left=0.19, right=0.985, bottom=0.27, top=0.82, wspace=0.15)
    figure.savefig(output, format="pdf", metadata={"CreationDate": None, "ModDate": None})
    plt.close(figure)


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("mullvad", type=Path)
    parser.add_argument("dns4eu", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    render(args.mullvad, args.dns4eu, args.output)
