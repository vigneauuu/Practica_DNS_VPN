"""Genera figuras comparativas a partir del resumen público de la medición."""
from argparse import ArgumentParser
from pathlib import Path
import json

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Patch


PROFILES = [
    ("cloudflare_standard", "Cloudflare estándar"),
    ("cloudflare_security", "Cloudflare seguridad"),
    ("cloudflare_family", "Cloudflare familiar"),
    ("google_public", "Google Public DNS"),
    ("quad9_reference", "Quad9 sin bloqueo"),
    ("quad9_secure", "Quad9 seguro"),
    ("adguard_open", "AdGuard sin filtro"),
    ("adguard_family", "AdGuard familiar"),
    ("cleanbrowsing_adult", "CleanBrowsing adulto"),
    ("cleanbrowsing_family", "CleanBrowsing familiar"),
    ("controld_open", "Control D sin filtro"),
    ("controld_family", "Control D familiar"),
    ("opendns_standard", "OpenDNS estándar"),
    ("opendns_family", "OpenDNS FamilyShield"),
]
FAMILY = {
    "cloudflare_family",
    "adguard_family",
    "cleanbrowsing_adult",
    "cleanbrowsing_family",
    "controld_family",
    "opendns_family",
}
STATES = [
    ("resolucion_observada", "Resolución observada", "#007F86"),
    ("bloqueo_senalizado", "Bloqueo señalizado", "#7B4A83"),
    ("anomalia", "Anomalía", "#D99100"),
    ("indeterminado", "Indeterminado", "#C9D2D6"),
    ("error_red", "Error de red", "#B64A4A"),
]
INK = "#18313D"
GRID = "#D8E0E3"


def configure_matplotlib():
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 16,
            "text.color": INK,
            "axes.labelcolor": INK,
            "axes.edgecolor": GRID,
            "xtick.color": INK,
            "ytick.color": INK,
            "axes.titlecolor": INK,
            "axes.titleweight": "bold",
            "axes.linewidth": 0.8,
            "axes.axisbelow": True,
            "grid.color": GRID,
            "grid.linewidth": 0.8,
            "grid.linestyle": "-",
            "pdf.fonttype": 42,
            "pdf.compression": 9,
            "savefig.facecolor": "white",
            "figure.facecolor": "white",
        }
    )


def draw_stacked_bars(ax, rows, sample_size, show_values=False):
    positions = list(range(len(rows)))
    cumulative = [0] * len(rows)
    used_states = []

    for key, label, color in STATES:
        values = [row.get("states", row).get(key, 0) for row in rows]
        if not any(values):
            continue
        ax.barh(
            positions,
            values,
            left=cumulative,
            height=0.68,
            color=color,
            edgecolor="white",
            linewidth=0.7,
            zorder=3,
        )
        used_states.append(Patch(facecolor=color, label=label))
        for y, start, value in zip(positions, cumulative, values):
            if show_values and value:
                text_color = "white" if key in {
                    "resolucion_observada",
                    "bloqueo_senalizado",
                    "error_red",
                } else INK
                ax.text(
                    start + value / 2,
                    y,
                    str(value),
                    ha="center",
                    va="center",
                    color=text_color,
                    fontsize=13,
                    fontweight="bold",
                    clip_on=True,
                )
        cumulative = [start + value for start, value in zip(cumulative, values)]

    if any(total != sample_size for total in cumulative):
        raise ValueError("Los segmentos del gráfico no suman el denominador esperado")

    ax.set_yticks(positions)
    ax.set_axisbelow(True)
    ax.xaxis.grid(True)
    ax.yaxis.grid(False)
    ax.tick_params(axis="y", length=0, pad=9)
    ax.tick_params(axis="x", length=0, pad=5)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    return used_states


def save_dns_plot(output, profiles, data, adult=False):
    is_adult = "adultos" if adult else "all"
    rows_by_type = {
        qtype: [data[profile, qtype, is_adult] for profile, _ in profiles]
        for qtype in ("A", "AAAA")
    }
    sample_size = 12 if adult else 150
    title = (
        "Respuestas de perfiles con filtro familiar o de adulto"
        if adult
        else "Estados de respuesta DNS por perfil"
    )
    subtitle = (
        "Cuatro dominios documentados como contenido adulto, tres rondas por tipo"
        if adult
        else "Mismos 50 dominios en todos los perfiles, tres rondas por tipo"
    )

    fig, axes = plt.subplots(1, 2, figsize=(12.6, 7.0), sharey=True)
    fig.suptitle(title, x=0.03, y=0.985, ha="left", fontsize=22, fontweight="bold")
    fig.text(0.03, 0.91, subtitle, ha="left", fontsize=14, color="#435A65")

    legend_by_label = {}
    for ax, qtype in zip(axes, ("A", "AAAA")):
        rows = rows_by_type[qtype]
        labels = [label for _, label in profiles]
        legend_handles = draw_stacked_bars(ax, rows, sample_size, show_values=adult)
        legend_by_label.update({handle.get_label(): handle for handle in legend_handles})
        ax.set_yticklabels(labels, fontsize=14)
        ax.set_xlim(0, sample_size)
        tick_count = 3 if sample_size > 24 else 4
        ax.set_xticks([sample_size * step // tick_count for step in range(tick_count + 1)])
        ax.set_xlabel("Observaciones", fontsize=14, labelpad=8)
        ax.set_title(qtype, fontsize=17, pad=12)

    axes[0].invert_yaxis()
    axes[1].tick_params(axis="y", left=False, labelleft=False)
    bottom = 0.19 if len(profiles) > 8 else 0.22
    fig.subplots_adjust(left=0.275, right=0.985, top=0.84, bottom=bottom, wspace=0.14)
    legend_handles = [
        legend_by_label[label]
        for _, label, _ in STATES
        if label in legend_by_label
    ]
    fig.legend(
        legend_handles,
        [handle.get_label() for handle in legend_handles],
        loc="lower center",
        bbox_to_anchor=(0.61, 0.025),
        ncol=5,
        frameon=False,
        fontsize=11,
        handlelength=1.3,
        columnspacing=1.6,
    )
    fig.savefig(output, format="pdf", bbox_inches="tight", metadata={"CreationDate": None, "ModDate": None})
    plt.close(fig)


def save_laboratory_plot(output, report):
    fig, axes = plt.subplots(1, 2, figsize=(12.6, 4.7))
    fig.suptitle(
        "Efecto de la regla en las configuraciones de laboratorio",
        x=0.03,
        y=0.99,
        ha="left",
        fontsize=21,
        fontweight="bold",
    )
    fig.text(
        0.03,
        0.90,
        "Acceso directo y dos configuraciones por mecanismo; casos de prueba sintéticos",
        ha="left",
        fontsize=14,
        color="#435A65",
    )

    panels = [
        (
            axes[0],
            report["vpn_local"],
            "vpn",
            "DNS por enlace o túnel OpenVPN",
            "consultas",
            24,
        ),
        (
            axes[1],
            report["proxy_local"],
            "proxy",
            "HTTP hacia un origen local",
            "solicitudes",
            12,
        ),
    ]
    conditions = [("directa", "Directa"), ("sin_filtro", "Regla desactivada"), ("con_filtro", "Regla activada")]
    shared_legend = []

    for ax, group, prefix, title, unit, sample_size in panels:
        rows = []
        for condition, _ in conditions:
            key = "directa" if condition == "directa" else f"{prefix}_{condition}"
            values = group[key]
            rows.append(
                {
                    "states": {
                        "resolucion_observada": values.get(
                            "resolucion_observada", values.get("respuesta_http_observada", 0)
                        ),
                        "bloqueo_senalizado": values.get("bloqueo_senalizado", 0),
                    }
                }
            )
        legend_handles = draw_stacked_bars(ax, rows, sample_size, show_values=True)
        ax.set_yticklabels([label for _, label in conditions], fontsize=14)
        if not shared_legend:
            shared_legend = legend_handles
        ax.set_xlim(0, sample_size)
        ax.set_xticks([sample_size * step // 4 for step in range(5)])
        ax.set_xlabel(f"Número de {unit}", fontsize=14, labelpad=8)
        ax.set_title(f"{title}\n(n = {sample_size} por condición)", fontsize=15, loc="left", pad=12)
        ax.invert_yaxis()

    shared_legend[0].set_label("Resolución DNS / HTTP 200")
    fig.subplots_adjust(left=0.205, right=0.985, top=0.71, bottom=0.29, wspace=0.5)
    fig.legend(
        shared_legend,
        [handle.get_label() for handle in shared_legend],
        loc="lower center",
        bbox_to_anchor=(0.6, 0.03),
        ncol=2,
        frameon=False,
        fontsize=11,
        handlelength=1.3,
        columnspacing=1.8,
    )
    fig.savefig(output, format="pdf", bbox_inches="tight", metadata={"CreationDate": None, "ModDate": None})
    plt.close(fig)


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    configure_matplotlib()
    report = json.loads(args.evidence.read_text(encoding="utf-8"))
    index = {
        (row["profile"], row["qtype"], row["category"]): row
        for row in report["counts"]
    }
    args.output.mkdir(parents=True, exist_ok=True)
    save_dns_plot(args.output / "dns-estados.pdf", PROFILES, index)
    save_dns_plot(
        args.output / "dns-adultos.pdf",
        [(profile, label) for profile, label in PROFILES if profile in FAMILY],
        index,
        adult=True,
    )
    save_laboratory_plot(args.output / "vpn-proxy-controles.pdf", report)


if __name__ == "__main__":
    main()
