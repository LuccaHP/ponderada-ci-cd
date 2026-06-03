# Relatório Técnico — Experimento de Métricas de Pipeline CI/CD

- **Aluno:** Lucca H. P.
- **Repositório:** <https://github.com/LuccaHP/ponderada-ci-cd>
- **Workflow (YAML):** [.github/workflows/ci.yml](../.github/workflows/ci.yml) · [ver no GitHub](https://github.com/LuccaHP/ponderada-ci-cd/blob/main/.github/workflows/ci.yml)
- **Página de execuções:** <https://github.com/LuccaHP/ponderada-ci-cd/actions>
- **Data do experimento:** 2026-06-03
- **Total de execuções reais:** 14 (≥12 exigidas) — 12 sucessos, 2 falhas controladas.

---

## 1. Introdução e objetivo

Este experimento mede e analisa o comportamento de um pipeline CI/CD a partir de
**execuções reais** no GitHub Actions. O objetivo é coletar métricas de desempenho,
estabilidade e gargalos, gerar gráficos e produzir uma análise crítica.

O projeto-base é uma **TODO API em FastAPI** com testes automatizados (unitários e
de integração via `TestClient`), usada como veículo para variar as execuções.

## 2. Setup do experimento

- **Pipeline:** dois jobs — `Lint (ruff)` e `Tests (pytest)`. Cada job: checkout →
  setup Python (com/sem cache) → instalar dependências → lint/testes → artefato (`reports/`).
- **Artefato:** `junit.xml` (+ `coverage.xml` e `test-summary.json`), do qual extraímos
  contagem de testes, falhas e tempo médio.
- **Coleta:** [scripts/collect_metrics.py](../scripts/collect_metrics.py) combina a **API REST
  do GitHub** (durações de run/job/step, status, commit) com o **parse do JUnit XML**.
- **Visualização:** [scripts/plot_metrics.py](../scripts/plot_metrics.py) (pandas + matplotlib).
- **Reprodução:** ver [README.md](../README.md).

### Hipóteses iniciais (definidas ANTES de rodar)

| # | Hipótese |
|---|----------|
| H1 | A etapa de **instalação de dependências** será o maior gargalo de tempo. |
| H2 | O **cache** de dependências reduzirá significativamente o tempo de instalação. |
| H3 | Rodar `lint` e `test` em **paralelo** reduzirá o tempo total do pipeline. |
| H4 | Aumentar o **nº de testes** aumentará a duração do pipeline de forma ~linear. |
| H5 | Um **teste lento** dominará o tempo total e será claramente visível nas métricas. |

## 3. Metodologia — variações executadas

Estratégia **mista**: variações de **código** via commits reais (SHAs distintos) e
variações de **configuração** via `workflow_dispatch` (mesmo SHA `c2d6821`, parâmetros
diferentes — a variação fica registrada nos próprios dados: `test_count`, durações, cache).

| # | Variação | Tipo | Commit (SHA) | Run ID (link) | Conclusão | Duração |
|---|----------|------|--------------|---------------|-----------|---------|
| 1 | Baseline | push | `4fb6f74` | [26890458786](https://github.com/LuccaHP/ponderada-ci-cd/actions/runs/26890458786) | success | 62 s |
| 2 | Teste falhando | push | `aadf19b` | [26890737315](https://github.com/LuccaHP/ponderada-ci-cd/actions/runs/26890737315) | **failure** | 59 s |
| 3 | Correção do teste | push | `7ca57f2` | [26890837079](https://github.com/LuccaHP/ponderada-ci-cd/actions/runs/26890837079) | success | 75 s |
| 4 | Jobs **paralelos** (remove `needs`) | push | `e1401b2` | [26890855354](https://github.com/LuccaHP/ponderada-ci-cd/actions/runs/26890855354) | success | **35 s** |
| 5 | Jobs **sequenciais** (`needs: lint`) | push | `a7b8e78` | [26890897851](https://github.com/LuccaHP/ponderada-ci-cd/actions/runs/26890897851) | success | 56 s |
| 6 | Falha de lint (import não usado) | push | `3bc82f5` | [26890931701](https://github.com/LuccaHP/ponderada-ci-cd/actions/runs/26890931701) | **failure** | **27 s** |
| 7 | Correção do lint | push | `c2d6821` | [26890944036](https://github.com/LuccaHP/ponderada-ci-cd/actions/runs/26890944036) | success | 59 s |
| 8 | Baseline repetido (variância) | dispatch | `c2d6821` | [26891025238](https://github.com/LuccaHP/ponderada-ci-cd/actions/runs/26891025238) | success | 66 s |
| 9 | +50 testes (`bulk_tests=50` → 78 testes) | dispatch | `c2d6821` | [26891030553](https://github.com/LuccaHP/ponderada-ci-cd/actions/runs/26891030553) | success | 62 s |
| 10 | +200 testes (`bulk_tests=200` → 228 testes) | dispatch | `c2d6821` | [26891036184](https://github.com/LuccaHP/ponderada-ci-cd/actions/runs/26891036184) | success | 69 s |
| 11 | Teste lento (`slow_test_seconds=20`) | dispatch | `c2d6821` | [26891040992](https://github.com/LuccaHP/ponderada-ci-cd/actions/runs/26891040992) | success | **91 s** |
| 12 | Sem cache (`use_cache=false`) | dispatch | `c2d6821` | [26891045723](https://github.com/LuccaHP/ponderada-ci-cd/actions/runs/26891045723) | success | 69 s |
| 13 | Com cache #1 (`use_cache=true`) | dispatch | `c2d6821` | [26891050983](https://github.com/LuccaHP/ponderada-ci-cd/actions/runs/26891050983) | success | 72 s |
| 14 | Com cache #2 (`use_cache=true`) | dispatch | `c2d6821` | [26891056200](https://github.com/LuccaHP/ponderada-ci-cd/actions/runs/26891056200) | success | 68 s |

## 4. Evidências reais de execução

- **Lista de runs (Actions):** <https://github.com/LuccaHP/ponderada-ci-cd/actions/workflows/ci.yml>
- **IDs reais dos workflows:** todos na tabela acima (de `26890458786` a `26891056200`).
- **Commits reais:** SHAs na tabela; histórico em
  <https://github.com/LuccaHP/ponderada-ci-cd/commits/main>.
- **Print das execuções reais:** as 14 runs do experimento na aba *Actions* (note os ✅
  sucessos e os ❌ das runs #2 *teste falhando* e #6 *falha de lint*):

![Visão geral das 14 execuções reais no GitHub Actions](prints/actions-overview.png)

Os links da tabela na §3 levam a cada run individual; o print acima e esses links são a
evidência verificável de que as execuções são reais.

## 5. Gráficos

Gerados de `data/metrics.csv` por `scripts/plot_metrics.py`.

| Tempo total por execução | Tempo médio por job |
|---|---|
| ![](../charts/01_pipeline_duration.png) | ![](../charts/02_duration_by_job.png) |

| Sucesso x falha | Nº de testes x duração |
|---|---|
| ![](../charts/03_success_failure_rate.png) | ![](../charts/04_tests_vs_duration.png) |

## 6. Análise (perguntas obrigatórias)

**1. Qual etapa mais contribuiu para o tempo total do pipeline?**
A etapa **"Install dependencies"**, de longe. Em praticamente todas as runs ela consome
**16–20 s** de um job de ~24–26 s — ou seja, **~70% do tempo de cada job**. As etapas de
lint (`ruff`, ~0 s) e de execução de testes (~2–3 s) são desprezíveis em comparação.
**Confirma H1.**

**2. Houve diferença significativa entre execuções com e sem cache?**
**Não — a diferença foi marginal.** Sem cache (run 12): install de ~19–20 s. Com cache
(runs 13/14): install de ~15–18 s. O ganho (~2–4 s) está **dentro da variância natural**
entre runs idênticas. Motivo: as dependências são poucas/pequenas e o cache do pip guarda
downloads, não os pacotes já instalados — as wheels ainda são reinstaladas, e o próprio
restore do cache custa tempo. **Refuta H2** (ver "resultados inesperados").

**3. O paralelismo reduziu o tempo total? Em que condições?**
**Sim, de forma expressiva.** Paralelo (run 4): **35 s**; sequencial (run 5): **56 s** —
redução de **~37%**. Condição: os dois jobs (`lint` e `test`) são independentes e de duração
parecida; sem a dependência `needs: lint`, o tempo total passa de *soma* para *máximo* dos
jobs. **Confirma H3.** Observação: ganho só existe porque há runners disponíveis para rodar
em paralelo e os jobs não compartilham dependência real.

**4. Quais falhas foram mais frequentes?**
Foram 2 falhas em 14 runs (**~14%**), uma de cada tipo: **teste falhando** (run 2,
`test_failures=1`) e **falha de lint** (run 6, job `Tests` *skipped* por causa do `needs`).
No experimento ambas tiveram a mesma frequência; em um cenário real, falhas de lint tendem
a ser mais comuns e mais baratas de detectar.

**5. O pipeline fornece feedback rápido o suficiente para o desenvolvedor?**
**Sim.** O pipeline verde leva ~56–75 s; em paralelo, ~35 s. A falha de lint deu feedback
em **27 s** (a mais rápida de todas), pois o *fail-fast* abortou antes de rodar os testes.
Para um projeto deste porte, < 1 min é um ciclo de feedback excelente.

**6. Que melhorias poderiam ser feitas no pipeline?**
(a) Atacar o gargalo real — **instalação de dependências** — com um cache mais efetivo
(cachear o venv inteiro, ou usar `uv`); (b) rodar `lint` e `test` **em paralelo** por padrão;
(c) usar matriz de versões só quando necessário; (d) *fail-fast* no lint já ajuda; (e) reduzir
overhead de setup do runner.

**7. Quais limitações existem nos dados coletados?**
Amostra pequena (14 runs, 1 execução por configuração → sem média/desvio robustos);
granularidade de tempo da API em segundos inteiros; `workflow_duration` pode incluir fila;
jobs *skipped* geram timing inconsistente (ver §9); variância dos runners hospedados.

**8. Como essa análise poderia apoiar decisões de engenharia?**
Mostra **onde investir**: como a instalação domina (~70%), otimizar cache/empacotamento tem
ROI maior do que mexer nos testes. Quantifica o ganho de **paralelizar** (~37%), justificando
a mudança. E evidencia que, neste estágio, **adicionar testes é "barato"** em tempo de
pipeline — encorajando mais cobertura sem medo de degradar o CI.

## 7. Resultados inesperados (mínimo 2)

- **Inesperado 1 — o cache quase não ajudou.** Esperávamos (H2) uma queda clara no tempo de
  instalação com cache; observamos ganho de apenas ~2–4 s, dentro do ruído. Causa provável:
  poucas dependências + cache de *download* (não de pacotes instalados) + custo do próprio
  restore. Lição: cache não é "bala de prata"; o ganho depende do tamanho/forma das deps.

- **Inesperado 2 — multiplicar os testes por ~8 quase não mudou a duração.** De 29 → 228
  testes (runs 8→10), a etapa de testes foi de **2 s → 3 s** e o total ficou praticamente
  estável (66 → 69 s). Como os testes são triviais e a instalação domina, a contagem de
  testes teve impacto desprezível — refutando a intuição (H4) de crescimento ~linear *neste
  regime*. O scatter "nº de testes × duração" mostra inclinação quase nula.

- **Inesperado 3 (bônus) — a run mais rápida foi uma falha.** A falha de lint (run 6, 27 s)
  foi a execução mais curta de todas, porque o *fail-fast* pulou o job de testes. Falhar cedo
  é, aqui, um comportamento desejável.

## 8. Hipótese inicial vs. resultado observado

| Hipótese | Resultado observado | Confirmada? |
|----------|---------------------|-------------|
| H1 — install é o gargalo | Install = ~70% de cada job (16–20 s) | ✅ Sim |
| H2 — cache acelera muito | Ganho marginal (~2–4 s, dentro do ruído) | ❌ Não |
| H3 — paralelo acelera | 35 s (paralelo) vs 56 s (sequencial), −37% | ✅ Sim |
| H4 — mais testes ≈ linear | 29→228 testes quase não mudou a duração | ❌ Não (neste regime) |
| H5 — teste lento domina | Run lenta = 91 s; etapa de testes 22 s | ✅ Sim |

## 9. Limitações do experimento

- **Amostra pequena:** 1 execução por configuração; sem repetições suficientes para
  estatística robusta (as runs baseline 1/8 já mostram variância de ~62 vs 66 s).
- **Granularidade:** a API reporta durações em **segundos inteiros**, o que apaga diferenças
  finas (relevante no caso do cache).
- **Tempo de fila:** `workflow_duration` (`updated_at − run_started_at`) pode embutir espera
  por runner; aqui a fila foi pequena (lead time ≈ duração).
- **Jobs *skipped*:** na falha de lint, o job `Tests` foi pulado e a API devolveu timing
  inconsistente (registrado como `job_duration = -1`); são linhas a tratar/ignorar na análise.
- **Cache já "quente":** a 1ª run (baseline) já populou o cache, então as runs "com cache"
  sempre tiveram *hit* — não medimos o custo de popular o cache do zero.
- **Ambiente compartilhado:** runners hospedados do GitHub têm variância de hardware/carga
  fora do nosso controle.

## 10. Conclusão

O maior gargalo do pipeline é a **instalação de dependências** (~70% do tempo), não os
testes. **Paralelizar** os jobs trouxe o ganho mais significativo (−37%), enquanto o **cache**
— ao contrário do esperado — teve efeito marginal neste projeto. Aumentar a quantidade de
testes triviais praticamente não custou tempo, e o *fail-fast* garantiu feedback rápido
(27 s) em caso de erro de lint. Recomendação de engenharia: **paralelizar por padrão** e
investir em um **cache mais efetivo (venv/`uv`)** antes de qualquer otimização nos testes.
