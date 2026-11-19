"""Compara el DNS del túnel WARP y las solicitudes HTTPS directas y por SOCKS5h."""
from argparse import ArgumentParser
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle
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


def draw_dns(figure, phases):
    panels = figure.subplots(2, 2, sharex=True, sharey=True)
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
    figure.subplots_adjust(left=0.15, right=0.985, bottom=0.25, top=0.82, hspace=0.23, wspace=0.09)


CONTROL_LABELS = (
    ("example.com", "example.com"),
    ("nudity.testcategory.com", "Prueba de adulto"),
    ("malware.testcategory.com", "Prueba de malware"),
    ("no-existe-pdns-lab.invalid", "Nombre .invalid"),
)
OUTCOMES = {
    "HTTP_200": ("HTTP 200", "#DDE6E8"),
    "curl_6": ("curl 6", "#FFFFFF"),
    "curl_97": ("curl 97", "#FFFFFF"),
}


def draw_proxy(figure, proxy, rounds):
    axis = figure.subplots()
    axis.set_xlim(0, 4)
    axis.set_ylim(4, 0)
    axis.set_aspect("auto")
    axis.set_xticks([0.5, 1.5, 2.5, 3.5], ["Directa", "SOCKS5h", "Directa", "SOCKS5h"])
    axis.set_yticks([i + 0.5 for i in range(4)], [label for _, label in CONTROL_LABELS])
    axis.tick_params(axis="both", length=0, labelsize=9)
    axis.xaxis.tick_top()
    axis.spines[:].set_visible(False)
    total = 0
    for group, (phase, label) in enumerate((("proxy_off", "Desactivado"), ("proxy_full", "Activado"))):
        axis.text(group * 2 + 1, -0.93, label, ha="center", fontsize=9, fontweight="bold")
        outcomes = proxy["phases"][phase]["outcomes"]
        for offset, path in enumerate(("direct", "socks5h")):
            column = group * 2 + offset
            for row, (domain, _) in enumerate(CONTROL_LABELS):
                counts = outcomes[domain][path]
                if sum(counts.values()) != rounds or counts.keys() - OUTCOMES.keys():
                    raise ValueError(f"Resultados HTTPS incompletos o desconocidos en {phase}/{domain}/{path}")
                total += sum(counts.values())
                left = column
                for outcome, count in counts.items():
                    width = count / rounds
                    text, color = OUTCOMES[outcome]
                    axis.add_patch(Rectangle((left, row), width, 1, facecolor=color,
                                             edgecolor="#88979A", linewidth=0.6))
                    axis.text(left + width / 2, row + 0.5, text, ha="center",
                              va="center", fontsize=8.5)
                    left += width
    if total != proxy["requests"]:
        raise ValueError("El panel no incluye todas las solicitudes HEAD")
    axis.axvline(2, color="#40565B", linewidth=1.5)
    figure.subplots_adjust(left=0.235, right=0.985, top=0.62, bottom=0.02)


def render(evidence, output):
    figure = plt.figure(figsize=(7.1, 5.3))
    dns, proxy = figure.subfigures(2, 1, height_ratios=(3.4, 1.9))
    dns.suptitle("Túnel WARP · consultas DNS", x=0.03, y=0.99, ha="left",
                 fontsize=10, fontweight="bold")
    draw_dns(dns, evidence["dns"]["phases"])
    proxy.suptitle("Modo proxy · solicitudes HTTPS (HEAD)", x=0.03, y=0.98, ha="left",
                   fontsize=10, fontweight="bold")
    draw_proxy(proxy, evidence["proxy"], evidence["rounds_per_condition"])
    figure.savefig(output, format="pdf", metadata={"CreationDate": None, "ModDate": None})
    plt.close(figure)


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("output", type=Path, help="Archivo PDF de salida")
    args = parser.parse_args()
    evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
    configure_matplotlib()
    render(evidence, args.output)


if __name__ == "__main__":
    main()
