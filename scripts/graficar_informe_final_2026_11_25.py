#!/usr/bin/env python3
"""Generador unificado y determinista de las 8 figuras estadísticas del informe final (25-11-2026).

Paleta única apta para impresión y daltonismo, vocabulario uniforme de estados DNS,
sin títulos incrustados redundantes (los títulos van en los pies de figura de LaTeX)
y con etiquetas legibles sobre fondo blanco cuando se superponen a barras.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
EV_DIR = ROOT / "docs" / "evidencia"
FIG_DIR = ROOT / "docs" / "informe" / "figuras"

# Paleta académica unificada
C_BLOCK = "#6A3D9A"    # Morado oscuro: Bloqueo señalizado
C_ALLOW = "#1F78B4"    # Azul acero: Resolución observada / Acceso normal
C_OMIT = "#E66101"     # Ámbar: Sin señal en categoría declarada / Anomalía
C_NODATA = "#BDBDBD"   # Gris neutro: Sin referencia / Indeterminado
C_ERR = "#CA0020"      # Rojo carmesí: Error de red / Fallo
C_OK = "#1B7837"       # Verde bosque: Verificado / Disponible


def fmt_es(val: float, dec: int = 1) -> str:
    """Formatea un número flotante con coma decimal en español."""
    return f"{val:.{dec}f}".replace(".", ",")

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 8.5,
    "axes.titlesize": 9.5,
    "axes.titleweight": "bold",
    "axes.labelsize": 8.5,
    "xtick.labelsize": 8.0,
    "ytick.labelsize": 8.0,
    "legend.fontsize": 7.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.edgecolor": "#444444",
    "axes.linewidth": 0.7,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

LABELS_PROFILE = {
    "cloudflare_standard": "Cloudflare Estándar",
    "cloudflare_security": "Cloudflare Seguridad",
    "cloudflare_family": "Cloudflare Familiar",
    "google_public": "Google Public DNS",
    "quad9_reference": "Quad9 Sin bloqueo",
    "quad9_unfiltered": "Quad9 Sin bloqueo",
    "quad9_secure": "Quad9 Seguro",
    "adguard_open": "AdGuard Sin filtro",
    "adguard_unfiltered": "AdGuard Sin filtro",
    "adguard_default": "AdGuard Predet.",
    "adguard_family": "AdGuard Familiar",
    "cleanbrowsing_adult": "CleanBrowsing Adulto",
    "cleanbrowsing_family": "CleanBrowsing Familiar",
    "controld_open": "Control D Sin filtro",
    "controld_family": "Control D Familiar",
    "opendns_standard": "OpenDNS Estándar",
    "opendns_family": "OpenDNS FamilyShield",
    "mullvad_open": "Mullvad Sin filtro",
    "mullvad_family": "Mullvad Familiar",
    "dns4eu_unfiltered": "DNS4EU Sin filtro",
    "dns4eu_protective": "DNS4EU Protector",
    "dns4eu_child": "DNS4EU Infantil",
}


def fig4_tcp_reclasificado() -> None:
    """14 perfiles TCP/53 reclasificados con huellas verificadas por proveedor (50 dominios, 3 rondas)."""
    data = json.loads((EV_DIR / "reclasificacion-ampliacion-tcp-2026-11-25.json").read_text())
    order = [
        "cloudflare_standard", "cloudflare_security", "cloudflare_family",
        "google_public", "quad9_reference", "quad9_secure",
        "adguard_open", "adguard_family",
        "cleanbrowsing_adult", "cleanbrowsing_family",
        "controld_open", "controld_family",
        "opendns_standard", "opendns_family",
    ]
    labels = [LABELS_PROFILE[p] for p in order]
    y = np.arange(len(order))

    fig, axes = plt.subplots(1, 2, figsize=(8.2, 4.7), sharey=True)
    for ax, qt in zip(axes, ("A", "AAAA")):
        res = [data["per_profile"][p]["counts"][qt]["ALL"].get("resolucion_observada", 0) for p in order]
        blk = [data["per_profile"][p]["counts"][qt]["ALL"].get("bloqueo_senalizado", 0) for p in order]
        ind = [data["per_profile"][p]["counts"][qt]["ALL"].get("indeterminado", 0) for p in order]
        err = [data["per_profile"][p]["counts"][qt]["ALL"].get("error_red", 0) for p in order]

        b1 = np.array(res)
        b2 = np.array(blk)
        b3 = np.array(ind)
        b4 = np.array(err)

        ax.barh(y, b1, color=C_ALLOW, height=0.68, label="Resolución observada")
        ax.barh(y, b2, left=b1, color=C_BLOCK, height=0.68, label="Bloqueo señalizado (huella verificada)")
        ax.barh(y, b3, left=b1 + b2, color=C_NODATA, height=0.68, label="Indeterminado (sin IPv6 / sin ref.)")
        ax.barh(y, b4, left=b1 + b2 + b3, color=C_ERR, height=0.68, label="Error de red")

        for i in range(len(order)):
            if b2[i] > 0:
                ax.text(b1[i] + b2[i] / 2, y[i], f"{b2[i]}", ha="center", va="center",
                        fontsize=7.2, fontweight="bold", color="white")
            if b4[i] > 0:
                ax.text(152, y[i], f"{b4[i]} err.", ha="left", va="center", fontsize=6.8, color=C_ERR, fontweight="bold")

        ax.set_title(f"Registros {qt} (n = 150 obs./perfil)", pad=6)
        ax.set_xlabel("Observaciones (50 dominios × 3 rondas)")
        ax.set_xlim(0, 165 if qt == "A" else 160)
        ax.set_xticks([0, 30, 60, 90, 120, 150])
        ax.grid(axis="x", linestyle=":", alpha=0.5)

    axes[0].set_yticks(y)
    axes[0].set_yticklabels(labels)
    axes[0].invert_yaxis()
    handles, leg_labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, leg_labels, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.55, -0.02))
    fig.tight_layout(rect=[0, 0.08, 1, 1])
    fig.savefig(FIG_DIR / "fig4_tcp_reclasificado.pdf", bbox_inches="tight")
    plt.close(fig)


def fig5_cobertura_pares_reclasificado() -> None:
    """Distribución de cobertura comparable entre los 91 pares TCP/53 tras reclasificación (sin zona vacía)."""
    data = json.loads((EV_DIR / "reclasificacion-ampliacion-tcp-2026-11-25.json").read_text())
    cov_a = {int(k): v for k, v in data["coverage_91_pairs_post_calibration"]["A"].items()}
    cov_aaaa = {int(k): v for k, v in data["coverage_91_pairs_post_calibration"]["AAAA"].items()}

    fig, axes = plt.subplots(1, 2, figsize=(7.6, 2.7), sharey=True)
    for ax, cov, title, color, xlim in [
        (axes[0], cov_a, "Registros A (91 pares)", C_ALLOW, (47.5, 51.0)),
        (axes[1], cov_aaaa, "Registros AAAA (91 pares)", C_BLOCK, (9.5, 15.5)),
    ]:
        xs = sorted(cov.keys())
        ys = [cov[k] for k in xs]
        bars = ax.bar(xs, ys, width=0.55, color=color, edgecolor="#333333", linewidth=0.5)
        for rect, val in zip(bars, ys):
            ax.text(rect.get_x() + rect.get_width() / 2, val + 2.0, f"{val} pares\n({fmt_es(val/91*100, 1)} %)",
                    ha="center", va="bottom", fontsize=7.6, fontweight="bold")
        ax.set_title(title, pad=6)
        ax.set_xlabel("Dominios consistentes comparables por par (de 50)")
        ax.set_xlim(*xlim)
        ax.set_xticks(range(int(xlim[0] + 0.5), int(xlim[1]) + 1))
        ax.set_ylim(0, 102)
        ax.grid(axis="y", linestyle=":", alpha=0.5)
    axes[0].set_ylabel("Número de pares de perfiles")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig5_cobertura_pares_reclasificado.pdf", bbox_inches="tight")
    plt.close(fig)


def fig6_benchmark_9_proveedores() -> None:
    """Comparación unificada de nueve perfiles de ocho proveedores (8 parentales + Quad9 Seguro) sobre el conjunto insesgado A-Z (DoH, A)."""
    ev = json.loads((EV_DIR / "benchmark-pdns-2026-11-26.json").read_text())
    live_g = ev["live_by_group_cf_std_A"]
    cnt_g = ev["group_counts"]
    profiles = [
        "dns4eu_child", "mullvad_family", "adguard_family", "cloudflare_family",
        "opendns_family", "cleanbrowsing_adult", "cleanbrowsing_family", "controld_family", "quad9_secure",
    ]
    groups = [
        ("adultos_reg", f"Adulto reg.\n(UE/Ofcom, n={cnt_g['adultos_reg']})"),
        ("adultos_cand", f"Adulto UT1 A-Z\n(n={cnt_g['adultos_cand']}; {live_g.get('adultos_cand', 0)} act.)"),
        ("apuestas_subtel", f"Apuestas Subtel\n(Chile, n={cnt_g['apuestas_subtel']})"),
        ("apuestas_cand", f"Apuestas SB A-Z\n(n={cnt_g['apuestas_cand']}; {live_g.get('apuestas_cand', 0)} act.)"),
        ("armas_verif", f"Armas oficiales\n(n={cnt_g['armas_verif']})"),
        ("educativo_verif", f"Educativo\n(CRUCH/IPEDS, n={cnt_g['educativo_verif']})"),
    ]
    mat = np.zeros((len(profiles), len(groups)))
    ann = [["" for _ in groups] for _ in profiles]

    for i, pid in enumerate(profiles):
        for j, (gkey, _) in enumerate(groups):
            info = ev["summary_by_group"][pid]["A"][gkey]
            st = info["states_ref_comparable"]
            blk = st.get("bloqueo_senalizado", 0)
            res = st.get("resolucion_observada", 0)
            denom = blk + res
            pct = (blk / denom * 100.0) if denom > 0 else 0.0
            mat[i, j] = pct
            ann[i][j] = f"{fmt_es(pct, 1)} %\n({blk}/{denom})" if denom > 0 else "s/ref"

    fig, ax = plt.subplots(figsize=(8.4, 4.4))
    im = ax.imshow(mat, cmap="PuBu", vmin=0, vmax=100, aspect="auto")

    for i in range(len(profiles)):
        for j in range(len(groups)):
            val = mat[i, j]
            txt_color = "white" if val >= 55 else "#111111"
            ax.text(j, i, ann[i][j], ha="center", va="center", fontsize=7.3,
                    fontweight="bold" if val > 0 else "normal", color=txt_color)

    ax.set_xticks(np.arange(len(groups)))
    ax.set_xticklabels([g[1] for g in groups], fontsize=7.8)
    ax.set_yticks(np.arange(len(profiles)))
    ax.set_yticklabels([LABELS_PROFILE[p] for p in profiles], fontsize=8.0)
    # Thin white grid lines between cells
    ax.set_xticks(np.arange(-0.5, len(groups), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(profiles), 1), minor=True)
    ax.grid(which="minor", color="white", linestyle="-", linewidth=1.2)
    ax.tick_params(which="minor", bottom=False, left=False)
    for sp in ax.spines.values():
        sp.set_visible(False)

    cbar = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    cbar.set_label("Proporción bloqueada en registros A (%)", fontsize=8.0)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig6_benchmark_9_proveedores.pdf", bbox_inches="tight")
    plt.close(fig)


def fig7_matrices_kappa_jaccard() -> None:
    """Matrices pareadas de Cohen's Kappa (triángulo superior) y Jaccard (triángulo inferior) separadas por categoría."""
    ev = json.loads((EV_DIR / "benchmark-pdns-2026-11-26.json").read_text())
    parental = [
        "cloudflare_family", "adguard_family", "cleanbrowsing_adult", "cleanbrowsing_family",
        "controld_family", "opendns_family", "mullvad_family", "dns4eu_child",
    ]
    short = ["CF Fam", "AG Fam", "CB Adu", "CB Fam", "CD Fam", "OD Fam", "MV Fam", "D4 Inf"]
    n = len(parental)
    idx = {p: i for i, p in enumerate(parental)}

    fig, axes = plt.subplots(1, 2, figsize=(8.5, 4.0))
    panels = [
        ("adultos_all", "Contenido adulto (reg. + UT1 A-Z, A)"),
        ("apuestas_all", "Apuestas (Subtel + SB A-Z, A)"),
    ]

    for ax, (skey, title) in zip(axes, panels):
        mat = np.full((n, n), np.nan)
        for row in ev["pairwise_A"][skey]:
            i, j = idx[row["a"]], idx[row["b"]]
            # Upper triangle (i < j): Cohen's Kappa; Lower triangle (j > i): Jaccard
            if i > j:
                i, j = j, i
            mat[i, j] = row["kappa"] if row["kappa"] is not None else np.nan
            mat[j, i] = row["jaccard"] if row["jaccard"] is not None else np.nan

        masked = np.ma.masked_invalid(mat)
        cmap = plt.cm.YlGnBu.copy()
        cmap.set_bad(color="#EFEFEF")
        im = ax.imshow(masked, cmap=cmap, vmin=0, vmax=1, aspect="equal")

        for r in range(n):
            for c in range(n):
                if r == c:
                    ax.text(c, r, "—", ha="center", va="center", fontsize=8.0, color="#666666")
                else:
                    v = mat[r, c]
                    if np.isnan(v):
                        ax.text(c, r, "n/d", ha="center", va="center", fontsize=6.8, color="#777777")
                    else:
                        txt_c = "white" if v >= 0.58 else "#111111"
                        ax.text(c, r, fmt_es(v, 2), ha="center", va="center", fontsize=7.0,
                                fontweight="bold" if v >= 0.5 else "normal", color=txt_c)

        ax.set_title(title, pad=8)
        ax.set_xticks(range(n))
        ax.set_xticklabels(short, rotation=38, ha="right", fontsize=7.6)
        ax.set_yticks(range(n))
        ax.set_yticklabels(short, fontsize=7.6)
        ax.set_xticks(np.arange(-0.5, n, 1), minor=True)
        ax.set_yticks(np.arange(-0.5, n, 1), minor=True)
        ax.grid(which="minor", color="white", linewidth=1.0)
        ax.tick_params(which="minor", bottom=False, left=False)
        for sp in ax.spines.values():
            sp.set_visible(False)

    axes[0].set_xlabel("Triáng. sup.: Kappa (κ) | Triáng. inf.: Jaccard (J)")
    axes[1].set_xlabel("Triáng. sup.: Kappa (κ) | Triáng. inf.: Jaccard (J)")
    cbar = fig.colorbar(im, ax=axes.ravel().tolist(), fraction=0.02, pad=0.025)
    cbar.set_ticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    cbar.ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, pos: fmt_es(x, 1)))
    cbar.set_label("Valor del índice (escala 0,0 a 1,0; valores < 0 al mínimo)", fontsize=7.6)
    fig.savefig(FIG_DIR / "fig7_matrices_kappa_jaccard.pdf", bbox_inches="tight")
    plt.close(fig)


def fig8_transportes_4_capas() -> None:
    """Disponibilidad y paridad de filtrado entre UDP/53, TCP/53 (ambos a 2,5 s), DoH y DoT/853."""
    ev = json.loads((EV_DIR / "transportes-udp-tcp-doh-dot-2026-11-25.json").read_text())
    order = [
        "cloudflare_standard", "cloudflare_family", "google_public",
        "quad9_unfiltered", "quad9_secure",
        "adguard_unfiltered", "adguard_family",
        "cleanbrowsing_family", "controld_family", "opendns_family",
        "mullvad_family", "dns4eu_child",
    ]
    transports = [
        ("udp53", "UDP/53\n2,5 s · n=24"),
        ("tcp53", "TCP/53\n2,5 s · n=96"),
        ("doh", "DoH\n443 · n=96"),
        ("dot853", "DoT\n853 · n=96"),
    ]
    mat = np.full((len(order), len(transports)), np.nan)
    ann = [["" for _ in transports] for _ in order]

    for i, pid in enumerate(order):
        tmap = ev["availability_by_profile_transport"].get(pid, {})
        for j, (tkey, _) in enumerate(transports):
            if tkey not in tmap:
                ann[i][j] = "N/A"
            else:
                ok = tmap[tkey]["ok"]
                tot = ok + tmap[tkey]["err"]
                pct = ok / tot * 100.0 if tot else 0.0
                mat[i, j] = pct
                ms = tmap[tkey]["ms_median"]
                if ok > 0 and ms is not None:
                    ms_str = fmt_es(ms, 1) if ms < 100 else f"{int(ms + 0.5)}"
                    ann[i][j] = f"{pct:.0f} %\n({ms_str} ms)"
                else:
                    ann[i][j] = "0 %\n(sin resp.)"

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.4, 4.2), gridspec_kw={"width_ratios": [1.45, 1.0]})

    # Panel A: Availability matrix with clean discrete-feeling colormap
    disp = np.where(mat < 0, np.nan, mat)
    cmap = plt.cm.RdYlGn.copy()
    cmap.set_bad(color="#E6E6E6")
    ax1.imshow(np.ma.masked_invalid(disp), cmap=cmap, vmin=0, vmax=100, aspect="auto")
    for i in range(len(order)):
        for j in range(len(transports)):
            txt = ann[i][j]
            val = mat[i, j]
            if np.isnan(val) or val < 0:
                tc = "#555555"
            elif val >= 80 or val == 0:
                tc = "white"
            else:
                tc = "#111111"
            ax1.text(j, i, txt, ha="center", va="center", fontsize=7.0,
                     fontweight="bold" if (not np.isnan(val) and val >= 0) else "normal", color=tc)

    ax1.set_title("A. Disponibilidad y mediana RTT por transporte", pad=6)
    ax1.set_xticks(range(len(transports)))
    ax1.set_xticklabels([t[1] for t in transports], fontsize=7.3)
    ax1.set_yticks(range(len(order)))
    ax1.set_yticklabels([LABELS_PROFILE[p] for p in order], fontsize=7.8)
    ax1.set_xticks(np.arange(-0.5, len(transports), 1), minor=True)
    ax1.set_yticks(np.arange(-0.5, len(order), 1), minor=True)
    ax1.grid(which="minor", color="white", linewidth=1.2)
    ax1.tick_params(which="minor", bottom=False, left=False)
    for sp in ax1.spines.values():
        sp.set_visible(False)

    # Panel B: Cross-transport blocking/response parity bar chart
    pair_items = [
        ("udp53_vs_tcp53", "UDP/53 vs. TCP/53\n(3 perfiles sin filtro parental)"),
        ("tcp53_vs_doh", "TCP/53 frente a DoH\n(10 perfiles)"),
        ("tcp53_vs_dot853", "TCP/53 frente a DoT/853\n(10 perfiles)"),
        ("doh_vs_dot853", "DoH frente a DoT/853\n(12 perfiles)"),
    ]
    yp = np.arange(len(pair_items))
    vals = []
    labs = []
    for pk, plab in pair_items:
        pv = ev["transport_parity"][pk]
        pct = pv["matched"] / pv["compared"] * 100.0 if pv["compared"] else 0.0
        vals.append(pct)
        m_s = f"{pv['matched']:,}".replace(",", ".")
        c_s = f"{pv['compared']:,}".replace(",", ".")
        labs.append(f"{m_s}/{c_s} ({fmt_es(pct, 1)} %)")

    bars = ax2.barh(yp, vals, height=0.52, color=C_OK, alpha=0.88)
    for rect, ltxt in zip(bars, labs):
        ax2.text(50, rect.get_y() + rect.get_height() / 2, ltxt,
                 ha="center", va="center", fontsize=8.0, fontweight="bold", color="white")
    ax2.set_yticks(yp)
    ax2.set_yticklabels([p[1] for p in pair_items], fontsize=8.0)
    ax2.set_xlim(0, 108)
    ax2.set_xticks([0, 25, 50, 75, 100])
    ax2.set_xlabel("Paridad exacta de clasificación (%)")
    ax2.set_title("B. Paridad pareada entre transportes", pad=6)
    ax2.grid(axis="x", linestyle=":", alpha=0.5)
    ax2.invert_yaxis()

    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig8_transportes_4_capas.pdf", bbox_inches="tight")
    plt.close(fig)


def fig9_vpn_proxy_laboratorio() -> None:
    """Controles causales de laboratorio (OpenVPN + proxy HTTP) con la paleta unificada."""
    ev = json.loads((EV_DIR / "ampliacion-2026-11-18.json").read_text())
    vpn = ev["vpn_local"]
    px = ev["proxy_local"]

    conds = [("directa", "Directa"), ("sin_filtro", "Regla desactivada"), ("con_filtro", "Regla activada")]
    y = np.arange(len(conds))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.0, 2.65), sharey=True)
    # VPN DNS
    v_allow = [vpn["directa"]["resolucion_observada"], vpn["vpn_sin_filtro"]["resolucion_observada"], vpn["vpn_con_filtro"]["resolucion_observada"]]
    v_block = [vpn["directa"].get("bloqueo_senalizado", 0), vpn["vpn_sin_filtro"].get("bloqueo_senalizado", 0), vpn["vpn_con_filtro"].get("bloqueo_senalizado", 0)]
    ax1.barh(y, v_allow, height=0.55, color=C_ALLOW, label="Resolución DNS / HTTP 200")
    ax1.barh(y, v_block, left=v_allow, height=0.55, color=C_BLOCK, label="Bloqueo señalizado (huella)")
    for i in range(len(conds)):
        if v_allow[i] > 0:
            ax1.text(v_allow[i] / 2, y[i], f"{v_allow[i]}", ha="center", va="center", color="white", fontweight="bold", fontsize=8.0)
        if v_block[i] > 0:
            ax1.text(v_allow[i] + v_block[i] / 2, y[i], f"{v_block[i]}", ha="center", va="center", color="white", fontweight="bold", fontsize=8.0)
    ax1.set_title("OpenVPN (DNS, n = 24 obs./condición)", pad=6)
    ax1.set_xlabel("Consultas DNS (A y AAAA)")
    ax1.set_xlim(0, 26)
    ax1.set_xticks([0, 6, 12, 18, 24])
    ax1.grid(axis="x", linestyle=":", alpha=0.5)
    ax1.invert_yaxis()

    # HTTP Proxy
    p_allow = [px["directa"]["respuesta_http_observada"], px["proxy_sin_filtro"]["respuesta_http_observada"], px["proxy_con_filtro"]["respuesta_http_observada"]]
    p_block = [px["directa"].get("bloqueo_senalizado", 0), px["proxy_sin_filtro"].get("bloqueo_senalizado", 0), px["proxy_con_filtro"].get("bloqueo_senalizado", 0)]
    ax2.barh(y, p_allow, height=0.55, color=C_ALLOW)
    ax2.barh(y, p_block, left=p_allow, height=0.55, color=C_BLOCK)
    for i in range(len(conds)):
        if p_allow[i] > 0:
            ax2.text(p_allow[i] / 2, y[i], f"{p_allow[i]}", ha="center", va="center", color="white", fontweight="bold", fontsize=8.0)
        if p_block[i] > 0:
            ax2.text(p_allow[i] + p_block[i] / 2, y[i], f"{p_block[i]}", ha="center", va="center", color="white", fontweight="bold", fontsize=8.0)
    ax2.set_title("Proxy HTTP local (n = 12 sol./condición)", pad=6)
    ax2.set_xlabel("Solicitudes HTTP")
    ax2.set_xlim(0, 13.5)
    ax2.set_xticks([0, 3, 6, 9, 12])
    ax2.grid(axis="x", linestyle=":", alpha=0.5)

    ax1.set_yticks(y)
    ax1.set_yticklabels([c[1] for c in conds])
    handles, labels = ax1.get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.55, -0.04))
    fig.tight_layout(rect=[0, 0.10, 1, 1])
    fig.savefig(FIG_DIR / "fig9_vpn_proxy_laboratorio.pdf", bbox_inches="tight")
    plt.close(fig)


def fig10_vpn_proxies_externos() -> None:
    """Figura limpia y legible de túneles VPN externos (WARP, AdGuard VPN, RiseupVPN).
    La matriz HTTPS HEAD sobre proxies SOCKS5 se presenta como tabla nativa LaTeX para máxima legibilidad impresa.
    """
    fig, ax1 = plt.subplots(figsize=(8.2, 3.35))
    rows_a = [
        ("WARP · túnel sin filtro (15 dom.)", 0, 30, 0),
        ("WARP · túnel familiar (15 dom.)", 8, 22, 0),
        ("AdGuard VPN · túnel sin filtro (21 dom.)", 0, 41, 1),
        ("AdGuard VPN · túnel familiar (21 dom.)", 8, 34, 0),
        ("RiseupVPN · DNS interno UDP (21 dom.)", 0, 42, 0),
        ("RiseupVPN · DNS4EU sin filtro DoH (21 dom.)", 0, 42, 0),
        ("RiseupVPN · DNS4EU infantil DoH (21 dom.)", 34, 8, 0),
    ]
    y1 = np.arange(len(rows_a))
    blk = np.array([r[1] for r in rows_a])
    alw = np.array([r[2] for r in rows_a])
    err = np.array([r[3] for r in rows_a])

    ax1.barh(y1, blk, height=0.62, color=C_BLOCK, label="Bloqueo señalizado (adulto / política DNS4EU)")
    ax1.barh(y1, alw, left=blk, height=0.62, color=C_ALLOW, label="Resolución observada (permitido o sin filtro)")
    ax1.barh(y1, err, left=blk + alw, height=0.62, color=C_ERR, label="Error de red (espera agotada)")

    for i in range(len(rows_a)):
        if blk[i] > 0:
            ax1.text(blk[i] / 2, y1[i], f"{blk[i]}", ha="center", va="center", color="white", fontweight="bold", fontsize=8.0)
        if alw[i] > 0:
            ax1.text(blk[i] + alw[i] / 2, y1[i], f"{alw[i]}", ha="center", va="center", color="white", fontweight="bold", fontsize=8.0)
        if err[i] > 0:
            ax1.text(blk[i] + alw[i] + err[i] + 0.7, y1[i], "1 err.", ha="left", va="center", color=C_ERR, fontweight="bold", fontsize=7.6)

    ax1.set_yticks(y1)
    ax1.set_yticklabels([r[0] for r in rows_a], fontsize=8.2)
    ax1.set_xlabel("Consultas DNS (registro A, 2 rondas por dominio; excluye controles técnicos)")
    ax1.set_xlim(0, 46)
    ax1.grid(axis="x", linestyle=":", alpha=0.5)
    ax1.invert_yaxis()
    ax1.legend(loc="upper center", bbox_to_anchor=(0.45, -0.22), ncol=2, frameon=False, fontsize=7.8)

    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig10_vpn_proxies_externos.pdf", bbox_inches="tight")
    plt.close(fig)


def fig11_ooni_chile() -> None:
    """Contraste externo real de OONI Web Connectivity en Chile (7 ASNs chilenos, sep–nov 2026)."""
    ev = json.loads((EV_DIR / "ooni-chile-2026-11-25.json").read_text())
    hits = ev["hits_detail"]
    order_doms = ["juegalo.com", "pornhub.com", "xnxx.com", "xvideos.com"]
    hmap = {h["domain"]: h for h in hits}
    labels = [
        "juegalo.com\n(Apuestas · Subtel)",
        "pornhub.com\n(Adulto · UE DSA)",
        "xnxx.com\n(Adulto · UE DSA)",
        "xvideos.com\n(Adulto · UE DSA)",
    ]
    anom = np.array([hmap[d]["anomalies_sep_nov_2026"] for d in order_doms])
    tot = np.array([hmap[d]["count_sep_nov_2026"] for d in order_doms])
    ok = tot - anom
    anom_pct = anom / tot * 100.0
    ok_pct = ok / tot * 100.0

    fig, ax = plt.subplots(figsize=(7.6, 2.7))
    y = np.arange(len(order_doms))
    ax.barh(y, anom_pct, height=0.56, color=C_OMIT, label="Anomalía reportada en OONI (7 ASN)")
    ax.barh(y, ok_pct, left=anom_pct, height=0.56, color=C_ALLOW, label="Sin anomalía reportada en OONI")

    for i in range(len(order_doms)):
        if anom_pct[i] >= 12:
            ax.text(anom_pct[i] / 2, y[i], f"{anom[i]}/{tot[i]} ({fmt_es(anom_pct[i], 1)} %)",
                    ha="center", va="center", color="white", fontweight="bold", fontsize=7.8)
        else:
            ax.text(anom_pct[i] + 1.5, y[i], f"{anom[i]} anom.", ha="left", va="center",
                    color=C_OMIT, fontweight="bold", fontsize=7.0,
                    bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.85))
        if ok_pct[i] >= 15:
            xpos = anom_pct[i] + ok_pct[i] / 2
            ax.text(xpos, y[i], f"{ok[i]}/{tot[i]} ({fmt_es(ok_pct[i], 1)} %)",
                    ha="center", va="center", color="white", fontweight="bold", fontsize=7.8)

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=8.0)
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 20, 40, 60, 80, 100])
    ax.set_xlabel("Proporción de mediciones OONI en Chile (7 ASN, sep.–nov. 2026, tope 50/URL, %)")
    ax.grid(axis="x", linestyle=":", alpha=0.5)
    ax.invert_yaxis()
    ax.legend(loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.48, -0.34))
    fig.tight_layout()
    fig.savefig(FIG_DIR / "fig11_ooni_chile.pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig4_tcp_reclasificado()
    fig5_cobertura_pares_reclasificado()
    fig6_benchmark_9_proveedores()
    fig7_matrices_kappa_jaccard()
    fig8_transportes_4_capas()
    fig9_vpn_proxy_laboratorio()
    fig10_vpn_proxies_externos()
    fig11_ooni_chile()
    print("ALL 8 UNIFIED FIGURES GENERATED SUCCESSFULLY!")


if __name__ == "__main__":
    main()
