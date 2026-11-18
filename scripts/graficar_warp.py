"""Compara las respuestas DNS de WARP al cambiar la política familiar."""
from argparse import ArgumentParser
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import MaxNLocator

from graficar_ampliacion import configure_matplotlib


CATEGORIES = (
    ("adultos", "Adulto"),
    ("apuestas", "Apuestas"),
    ("armas", "Armas"),
    ("educativo", "Educativo"),
)
POLICIES = (
    ("warp_off", "Filtro familiar desactivado"),
    ("warp_full", "Filtro familiar activado"),
)
STYLES = {
    "address": ("Dirección no nula", "#DDE6E8", ""),
    "sink": ("Dirección nula", "#284751", ""),
    "no_address": ("NOERROR sin dirección", "#FFFFFF", "////"),
    "NXDOMAIN": ("NXDOMAIN", "#B0B7B8", "xx"),
}


def render(phases, output):
    figure, panels = plt.subplots(2, 2, figsize=(7.1, 3.45), sharex=True, sharey=True)
    used_states = set()
    max_observations = 0
    sample_sizes = {}
    for column, (policy, heading) in enumerate(POLICIES):
        for row, qtype in enumerate(("A", "AAAA")):
            axis = panels[row, column]
            for position, (category, _) in enumerate(CATEGORIES):
                cell = phases[policy]["categories"][category][qtype]
                states = cell["states"]
                if set(states) - STYLES.keys():
                    raise ValueError(f"Forma de respuesta sin representar en {policy}/{category}/{qtype}: {states}")
                if sum(states.values()) != cell["observations"]:
                    raise ValueError(f"Recuentos incompletos en {policy}/{category}/{qtype}")
                size = (cell["domains"], cell["observations"])
                if sample_sizes.setdefault(category, size) != size:
                    raise ValueError(f"Denominadores distintos para {category}")
                max_observations = max(max_observations, cell["observations"])
                left = 0
                for state, (_, color, hatch) in STYLES.items():
                    value = states.get(state, 0)
                    if value:
                        used_states.add(state)
                        axis.barh(position, value, left=left, height=0.72, color=color,
                                  edgecolor="#40565B", linewidth=0.6, hatch=hatch, zorder=3)
                        axis.text(left + value / 2, position, str(value), ha="center",
                                  va="center", fontsize=8, color="white" if state == "sink" else "#15292F",
                                  bbox=dict(facecolor="white", edgecolor="none", pad=0.4) if hatch else None)
                        left += value
            axis.set_yticks(range(len(CATEGORIES)), [label for _, label in CATEGORIES])
            axis.tick_params(axis="both", length=0, labelsize=9)
            axis.xaxis.grid(True, linewidth=0.5)
            axis.spines[["left", "right", "top"]].set_visible(False)
            if row == 0:
                axis.set_title(heading, fontsize=10)
            if column == 0:
                axis.set_ylabel(qtype, fontsize=10, fontweight="bold")

    first = panels[0, 0]
    first.invert_yaxis()
    first.set_xlim(0, max_observations)
    first.xaxis.set_major_locator(MaxNLocator(nbins=5, integer=True))
    figure.supxlabel("Consultas DNS", y=0.13, fontsize=10)
    legend = [
        Patch(facecolor=color, edgecolor="#40565B", hatch=hatch, label=label, linewidth=0.6)
        for state, (label, color, hatch) in STYLES.items() if state in used_states
    ]
    figure.legend(handles=legend, loc="lower center", bbox_to_anchor=(0.5, 0.005),
                  ncols=len(legend), fontsize=9, frameon=False)
    figure.subplots_adjust(left=0.15, right=0.985, bottom=0.25, top=0.91, hspace=0.23, wspace=0.09)
    figure.savefig(output, format="pdf", metadata={"CreationDate": None, "ModDate": None})
    plt.close(figure)


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("output", type=Path, help="Archivo PDF de salida")
    args = parser.parse_args()
    evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
    configure_matplotlib()
    render(evidence["dns"]["phases"], args.output)


if __name__ == "__main__":
    main()
