"""Grafica las consultas A con Riseup y los controles HTTPS de WARP y Tor."""

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.ticker import MaxNLocator

from graficar_ampliacion import configure_matplotlib
from graficar_warp import CONTROL_LABELS


RUTAS_DNS = (
    ("directa", "dns4eu_sin_filtro", "Directa · DNS4EU sin filtro"),
    ("directa", "dns4eu_infantil", "Directa · DNS4EU infantil"),
    ("riseup", "dns4eu_sin_filtro", "Riseup · DNS4EU sin filtro"),
    ("riseup", "dns4eu_infantil", "Riseup · DNS4EU infantil"),
    ("riseup", "dns_riseup", "Riseup · DNS del túnel"),
)
RESTRINGIDOS = ("adultos", "apuestas", "apuestas_subtel", "armas")
COLOR_AVISO = "#284751"
COLOR_DIRECCION = "#DFE8E9"


def panel_dns(ax, evidencia):
    for posicion, (ruta, perfil, _) in enumerate(RUTAS_DNS):
        grupos = evidencia["routes"][ruta]["profiles"][perfil]["groups"]
        muestra = [grupos[categoria]["A"] for categoria in RESTRINGIDOS]
        aviso = sum(grupo["states"].get("direccion_aviso", 0) for grupo in muestra)
        ordinaria = sum(grupo["states"].get("direccion", 0) for grupo in muestra)
        if aviso + ordinaria != sum(grupo["observations"] for grupo in muestra):
            raise ValueError(f"Hay respuestas adicionales para {ruta}/{perfil}")
        for total, inicio, color, tinta in ((aviso, 0, COLOR_AVISO, "white"),
                                            (ordinaria, aviso, COLOR_DIRECCION, "#15292F")):
            if total:
                ax.barh(posicion, total, left=inicio, color=color, edgecolor=COLOR_AVISO,
                        linewidth=0.6, zorder=3)
                ax.text(inicio + total / 2, posicion, str(total),
                        ha="center", va="center", color=tinta, fontsize=9)
    ax.set_yticks(range(len(RUTAS_DNS)), [label for _, _, label in RUTAS_DNS])
    ax.invert_yaxis()
    ax.xaxis.set_major_locator(MaxNLocator(nbins=8, integer=True))
    ax.set_title("A. Consultas A a 17 dominios de adulto, apuestas o armas", loc="left", fontsize=10)
    ax.set_xlabel("Consultas DNS (dos rondas por dominio)", fontsize=9)
    ax.xaxis.grid(True, linewidth=0.5)
    ax.legend(handles=[Patch(facecolor=COLOR_AVISO, label="Dirección de aviso de DNS4EU"),
                       Patch(facecolor=COLOR_DIRECCION, edgecolor=COLOR_AVISO,
                             label="Dirección ordinaria")],
              frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.29), ncol=2, fontsize=8)


def panel_https(ax, warp, tor):
    salidas_warp = warp["proxy"]["phases"]["proxy_full"]["outcomes"]
    salidas_tor = {ruta: datos["controls"] for ruta, datos in tor["routes"].items()}
    condiciones = ("WARP · directa", "WARP · proxy", "Tor · directa", "Tor · proxy")
    matriz = []
    for dominio, _ in CONTROL_LABELS:
        matriz.append([
            salidas_warp[dominio]["direct"].get("HTTP_200", 0),
            salidas_warp[dominio]["socks5h"].get("HTTP_200", 0),
            salidas_tor["directa"][dominio].get("http_200", 0),
            salidas_tor["tor"][dominio].get("http_200", 0),
        ])
    mapa = matplotlib.colors.ListedColormap(["#FFFFFF", COLOR_DIRECCION, COLOR_AVISO])
    ax.imshow(matriz, cmap=mapa, vmin=0, vmax=2, aspect="auto")
    for fila, valores in enumerate(matriz):
        for columna, valor in enumerate(valores):
            ax.text(columna, fila, f"{valor}/2", va="center", ha="center",
                    color="white" if valor == 2 else "#15292F", fontsize=9)
    ax.set_xticks(range(len(condiciones)), condiciones)
    ax.set_yticks(range(len(CONTROL_LABELS)), [label for _, label in CONTROL_LABELS])
    ax.set_title("B. Respuestas HTTP 200 a solicitudes HTTPS (HEAD)", loc="left", fontsize=10)
    ax.set_xticks([0.5, 1.5, 2.5], minor=True)
    ax.set_yticks([0.5, 1.5, 2.5], minor=True)
    ax.grid(which="minor", color="#88979A", linewidth=0.6)
    ax.tick_params(which="minor", length=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for argumento in ("riseup", "warp", "tor", "salida"):
        parser.add_argument(argumento, type=Path)
    args = parser.parse_args()
    riseup, warp, tor = (json.loads(ruta.read_text(encoding="utf-8"))
                         for ruta in (args.riseup, args.warp, args.tor))
    configure_matplotlib()
    fig, (dns, https) = plt.subplots(2, 1, figsize=(7.25, 4.35), height_ratios=(1.12, 1.0))
    panel_dns(dns, riseup)
    panel_https(https, warp, tor)
    for ax in (dns, https):
        ax.tick_params(axis="both", length=0, labelsize=8)
        ax.spines[["top", "right", "left"]].set_visible(False)
    fig.subplots_adjust(left=0.31, right=0.982, top=0.93, bottom=0.095, hspace=1.00)
    fig.savefig(args.salida, format="pdf", metadata={"CreationDate": None, "ModDate": None})
    plt.close(fig)


if __name__ == "__main__":
    main()
