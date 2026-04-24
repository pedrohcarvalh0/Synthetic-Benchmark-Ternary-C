/*
 * ============================================================
 *  Avaliação de Desempenho: Operador Ternário vs if-else em C
 *  Disciplina: Avaliação e Desempenho de Sistemas
 * ============================================================
 *
 * Metodologia:
 *   - Programa sintético que mede o tempo de execução isolado do operador ternário e da estrutura if-else.
 *   - Usa clock_gettime(CLOCK_MONOTONIC) para alta resolução (ns).
 *   - Aplica aquecimento (warm-up) para estabilizar caches e evitar efeitos de arranque a frio (cold-start).
 *   - Executa N_ROUNDS rodadas, cada uma com N_OPS operações, armazenando o tempo médio por operação (ns).
 *   - Variável volátil para impedir que o compilador elimine o código morto (dead-code elimination).
 *   - Resultados salvos em CSV para análise estatística.
 */

#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>

/* ── Parâmetros do experimento ───────────────────────────── */
#define N_ROUNDS      200        /* número de amostras coletadas     */
#define N_OPS         1000000    /* operações por rodada             */
#define WARMUP_ROUNDS 20         /* rodadas descartadas (warm-up)    */
#define OUTPUT_FILE   "results.csv"
/* ─────────────────────────────────────────────────────────── */

/* Retorna tempo em nanosegundos */
static inline long long now_ns(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (long long)ts.tv_sec * 1000000000LL + ts.tv_nsec;
}

/*
 * Função que mede o operador ternário.
 * volatile garante que o resultado seja realmente computado.
 * __attribute__((noinline)) impede inlining que distorceria a medição.
 */
__attribute__((noinline))
static double bench_ternary(int n)
{
    volatile int sink = 0;   /* impede dead-code elimination */
    long long t0, t1;
    int i, x;

    t0 = now_ns();
    for (i = 0; i < n; i++) {
        x    = i & 1;          /* alterna 0/1 para evitar branch prediction perfeita */
        sink = (x > 0) ? (sink + 1) : (sink - 1);
    }
    t1 = now_ns();

    (void)sink;                /* suprime warning de variável não usada */
    return (double)(t1 - t0) / (double)n;   /* ns por operação */
}

/*
 * Função equivalente usando if-else.
 * Estrutura idêntica ao bench_ternary para comparação justa.
 */
__attribute__((noinline))
static double bench_ifelse(int n)
{
    volatile int sink = 0;
    long long t0, t1;
    int i, x;

    t0 = now_ns();
    for (i = 0; i < n; i++) {
        x = i & 1;
        if (x > 0)
            sink = sink + 1;
        else
            sink = sink - 1;
    }
    t1 = now_ns();

    (void)sink;
    return (double)(t1 - t0) / (double)n;
}

int main(void)
{
    int    i;
    double ternary_times[N_ROUNDS];
    double ifelse_times[N_ROUNDS];
    FILE  *fp;

    printf("==============================================\n");
    printf("  Benchmark: Ternário vs if-else em C\n");
    printf("==============================================\n");
    printf("  Rodadas de coleta : %d\n", N_ROUNDS);
    printf("  Operações/rodada  : %d\n", N_OPS);
    printf("  Warm-up (descarte): %d rodadas\n", WARMUP_ROUNDS);
    printf("----------------------------------------------\n");
    printf("  Executando warm-up...\n");

    /* ── Warm-up: descarta as primeiras rodadas ─────────── */
    for (i = 0; i < WARMUP_ROUNDS; i++) {
        bench_ternary(N_OPS);
        bench_ifelse(N_OPS);
    }

    printf("  Coletando amostras");
    fflush(stdout);

    /* ── Coleta intercalada para reduzir viés temporal ──── */
    for (i = 0; i < N_ROUNDS; i++) {
        ternary_times[i] = bench_ternary(N_OPS);
        ifelse_times[i]  = bench_ifelse(N_OPS);

        if (i % 20 == 0) { printf("."); fflush(stdout); }
    }
    printf(" concluído!\n");

    /* ── Grava resultados em CSV ─────────────────────────── */
    fp = fopen(OUTPUT_FILE, "w");
    if (!fp) {
        perror("Erro ao abrir arquivo de saída");
        return EXIT_FAILURE;
    }

    fprintf(fp, "rodada,ternario_ns_por_op,ifelse_ns_por_op\n");
    for (i = 0; i < N_ROUNDS; i++) {
        fprintf(fp, "%d,%.6f,%.6f\n",
                i + 1,
                ternary_times[i],
                ifelse_times[i]);
    }

    fclose(fp);

    printf("  Resultados salvos em: %s\n", OUTPUT_FILE);
    printf("==============================================\n");

    return EXIT_SUCCESS;
}
