"""
============================================================
  Análise Estatística: Operador Ternário vs if-else em C
  Disciplina: Avaliação e Desempenho de Sistemas
============================================================
Foco: Intervalo de Confiança (IC 95%) e Overhead
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
import os

# ── Estilo limpo, fundo branco ────────────────────────────
plt.rcParams.update({
    "figure.facecolor":  "white",
    "axes.facecolor":    "white",
    "axes.edgecolor":    "#333333",
    "axes.labelcolor":   "#222222",
    "axes.titlecolor":   "#111111",
    "xtick.color":       "#444444",
    "ytick.color":       "#444444",
    "text.color":        "#222222",
    "grid.color":        "#cccccc",
    "grid.alpha":        0.7,
    "font.family":       "sans-serif",
    "font.size":         12,
    "axes.titlesize":    14,
    "axes.labelsize":    12,
    "legend.fontsize":   11,
    "legend.framealpha": 0.9,
})

COR_TERNARIO = "#2196F3"   # azul
COR_IFELSE   = "#F44336"   # vermelho
CSV_FILE     = "results.csv"

# ══════════════════════════════════════════════════════════
#  1. Leitura
# ══════════════════════════════════════════════════════════

def carregar_dados(path):
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Arquivo '{path}' não encontrado.\n"
            "Execute primeiro:  gcc -O2 -o benchmark benchmark.c && ./benchmark"
        )
    df = pd.read_csv(path)
    print(f"  ✓ {len(df)} amostras carregadas de '{path}'")
    return df

# ══════════════════════════════════════════════════════════
#  2. Estatísticas + IC
# ══════════════════════════════════════════════════════════

def calcular_ic(serie, alpha=0.05):
    n      = len(serie)
    media  = serie.mean()
    s      = serie.std(ddof=1)
    se     = s / np.sqrt(n)
    t_crit = stats.t.ppf(1 - alpha / 2, df=n - 1)
    margem = t_crit * se
    return {
        "n":      n,
        "media":  media,
        "std":    s,
        "se":     se,
        "t_crit": t_crit,
        "margem": margem,
        "ic_inf": media - margem,
        "ic_sup": media + margem,
    }

def imprimir_resultados(rt, ri):
    print("\n" + "="*54)
    print("  RESULTADOS — IC 95% (α = 0,05)")
    print("="*54)
    for r, nome in [(rt, "Operador Ternário (?:)"), (ri, "Estrutura if-else")]:
        print(f"\n  {nome}")
        print(f"  {'─'*40}")
        print(f"  n                : {r['n']}")
        print(f"  Média            : {r['media']:.4f} ns/op")
        print(f"  Desvio Padrão    : {r['std']:.4f} ns/op")
        print(f"  Erro Padrão (SE) : {r['se']:.4f} ns/op")
        print(f"  t crítico        : {r['t_crit']:.4f}")
        print(f"  IC 95%           : [{r['ic_inf']:.4f} ; {r['ic_sup']:.4f}] ns/op")
        print(f"  Margem (±)       : {r['margem']:.4f} ns/op")

    diff = rt["media"] - ri["media"]
    ovhd = diff / ri["media"] * 100
    print(f"\n{'='*54}")
    print("  OVERHEAD DO TERNÁRIO")
    print(f"{'='*54}")
    print(f"  Diferença de médias : {diff:+.4f} ns/op")
    print(f"  Overhead relativo   : {ovhd:+.2f}%")
    sentido = "mais lento" if ovhd > 0 else "mais rápido"
    print(f"  Interpretação       : ternário é {abs(ovhd):.2f}% {sentido}")

    df_tmp = pd.read_csv(CSV_FILE)
    t_stat, p_val = stats.ttest_rel(
        df_tmp["ternario_ns_por_op"],
        df_tmp["ifelse_ns_por_op"]
    )
    print(f"\n{'='*54}")
    print("  TESTE t PAREADO")
    print(f"{'='*54}")
    print(f"  Estatística t : {t_stat:.4f}")
    print(f"  p-value       : {p_val:.4f}")
    if p_val < 0.05:
        print("  Conclusão     : diferença ESTATISTICAMENTE SIGNIFICATIVA")
    else:
        print("  Conclusão     : diferença NÃO significativa (p ≥ 0,05)")
    print()

# ══════════════════════════════════════════════════════════
#  3. Gráfico 1 — Intervalos de Confiança
# ══════════════════════════════════════════════════════════

def plot_ic(rt, ri):
    fig, ax = plt.subplots(figsize=(8, 5))

    operadores = ["Ternário (?:)", "if-else"]
    medias     = [rt["media"],  ri["media"]]
    margens    = [rt["margem"], ri["margem"]]
    cores      = [COR_TERNARIO, COR_IFELSE]
    ic_inf     = [rt["ic_inf"], ri["ic_inf"]]
    ic_sup     = [rt["ic_sup"], ri["ic_sup"]]

    for i, (op, med, marg, cor, inf, sup) in enumerate(
            zip(operadores, medias, margens, cores, ic_inf, ic_sup)):

        # Barra de IC
        ax.errorbar(i, med, yerr=marg,
                    fmt="o", color=cor, markersize=10,
                    capsize=14, capthick=2.5, linewidth=2.5,
                    label=f"{op}  |  IC 95%: [{inf:.3f} ; {sup:.3f}] ns/op",
                    zorder=4)

        # Faixa colorida do IC
        ax.fill_between(
            [i - 0.18, i + 0.18], inf, sup,
            color=cor, alpha=0.12, zorder=2
        )

        # Anotação da média
        ax.text(i, sup + 0.015,
                f"Média = {med:.3f} ns",
                ha="center", va="bottom", fontsize=10,
                color=cor, fontweight="bold")

        # Limites do IC
        ax.text(i + 0.22, sup, f"{sup:.3f}", va="center", fontsize=9, color=cor)
        ax.text(i + 0.22, inf, f"{inf:.3f}", va="center", fontsize=9, color=cor)

    ax.set_xticks([0, 1])
    ax.set_xticklabels(operadores, fontsize=13)
    ax.set_ylabel("Tempo (ns/operação)")
    ax.set_title("Intervalo de Confiança 95% do Tempo de Resposta\n"
                 "Operador Ternário vs if-else  (α = 5%)",
                 fontweight="bold", pad=15)
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(True, axis="y", linestyle="--", alpha=0.6)
    ax.set_xlim(-0.6, 1.6)
    fig.tight_layout()
    return fig

# ══════════════════════════════════════════════════════════
#  4. Gráfico 2 — Overhead por rodada
# ══════════════════════════════════════════════════════════

def plot_overhead(df, overhead_medio):
    overhead_rodadas = ((df["ternario_ns_por_op"] - df["ifelse_ns_por_op"])
                        / df["ifelse_ns_por_op"] * 100)

    fig, ax = plt.subplots(figsize=(10, 4))

    cor_barras = [COR_TERNARIO if v >= 0 else COR_IFELSE
                  for v in overhead_rodadas]

    ax.bar(df["rodada"], overhead_rodadas,
           color=cor_barras, alpha=0.6, width=1.0)

    ax.axhline(0, color="#333333", linewidth=1.2)
    ax.axhline(overhead_medio, color="#E65100", linewidth=2,
               linestyle="--",
               label=f"Overhead médio: {overhead_medio:+.1f}%")

    ax.set_xlabel("Rodada")
    ax.set_ylabel("Overhead (%)")
    ax.set_title("Overhead do Ternário em Relação ao if-else — por Rodada\n"
                 "(azul = ternário mais lento   |   vermelho = ternário mais rápido)",
                 fontweight="bold")
    ax.legend(fontsize=11)
    ax.grid(True, axis="y", linestyle="--", alpha=0.6)
    fig.tight_layout()
    return fig

# ══════════════════════════════════════════════════════════
#  5. Gráfico 3 — Série Temporal
# ══════════════════════════════════════════════════════════

def plot_serie_temporal(df, ternario, ifelse, rt, ri):
    fig, ax = plt.subplots(figsize=(11, 5))

    rodadas = df["rodada"]
    w = 10  # janela da média móvel

    # Linhas brutas (transparentes)
    ax.plot(rodadas, ternario, color=COR_TERNARIO, alpha=0.35, linewidth=0.8)
    ax.plot(rodadas, ifelse,   color=COR_IFELSE,   alpha=0.35, linewidth=0.8)

    # Médias móveis suavizadas
    mm_t = np.convolve(ternario, np.ones(w)/w, mode="valid")
    mm_i = np.convolve(ifelse,   np.ones(w)/w, mode="valid")
    ax.plot(rodadas[w-1:], mm_t, color=COR_TERNARIO, linewidth=2.2,
            label=f"Ternário — média={rt['media']:.3f} ns  |  IC 95%: [{rt['ic_inf']:.3f} ; {rt['ic_sup']:.3f}] ns/op")
    ax.plot(rodadas[w-1:], mm_i, color=COR_IFELSE,   linewidth=2.2,
            label=f"if-else  — média={ri['media']:.3f} ns  |  IC 95%: [{ri['ic_inf']:.3f} ; {ri['ic_sup']:.3f}] ns/op")

    # Faixas do IC 95%
    ax.axhspan(rt["ic_inf"], rt["ic_sup"], color=COR_TERNARIO, alpha=0.08)
    ax.axhspan(ri["ic_inf"], ri["ic_sup"], color=COR_IFELSE,   alpha=0.08)

    # Linhas das médias globais
    ax.axhline(rt["media"], color=COR_TERNARIO, linewidth=1.2, linestyle="--", alpha=0.7)
    ax.axhline(ri["media"], color=COR_IFELSE,   linewidth=1.2, linestyle="--", alpha=0.7)

    ax.set_xlabel("Rodada")
    ax.set_ylabel("Tempo (ns/operação)")
    ax.set_title("Série Temporal do Tempo de Resposta por Rodada\n"
                 "Linha espessa = média móvel (10 rodadas)   |   Faixa colorida = IC 95%",
                 fontweight="bold")
    ax.legend(fontsize=9, loc="upper right")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.set_xlim(1, len(rodadas))
    fig.tight_layout()
    return fig

# ══════════════════════════════════════════════════════════
#  6. Main
# ══════════════════════════════════════════════════════════

def main():
    ALPHA = 0.05

    print("\n" + "="*54)
    print("  Análise — Ternário vs if-else em C")
    print("="*54)

    df       = carregar_dados(CSV_FILE)
    ternario = df["ternario_ns_por_op"]
    ifelse   = df["ifelse_ns_por_op"]

    rt = calcular_ic(ternario, alpha=ALPHA)
    ri = calcular_ic(ifelse,   alpha=ALPHA)

    imprimir_resultados(rt, ri)

    overhead_medio = (rt["media"] - ri["media"]) / ri["media"] * 100

    print("  Gerando gráficos...")
    graficos = {
        "grafico1_intervalo_confianca.png": plot_ic(rt, ri),
        "grafico2_overhead.png":            plot_overhead(df, overhead_medio),
        "grafico3_serie_temporal.png":      plot_serie_temporal(df, ternario, ifelse, rt, ri),
    }

    for nome, fig in graficos.items():
        fig.savefig(nome, dpi=150, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        print(f"  ✓ {nome}")

    print("\n  Concluído!\n")


if __name__ == "__main__":
    main()