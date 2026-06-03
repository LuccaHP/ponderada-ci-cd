# Experimento de Métricas de Pipeline CI/CD

Experimento prático que instrumenta um pipeline CI/CD no **GitHub Actions**, coleta
métricas reais de execução, gera gráficos e embasa uma análise crítica sobre
desempenho, estabilidade e gargalos do processo.

O projeto-base é uma **TODO API em FastAPI** com testes automatizados — simples de
propósito, servindo apenas de veículo para gerar e variar as execuções do pipeline.

## Estrutura

```
app/                  # TODO API (FastAPI)
tests/                # testes (pytest): unitários + integração (TestClient)
.github/workflows/    # ci.yml — pipeline CI/CD instrumentado
scripts/
  collect_metrics.py  # coleta via API do GitHub + parse do JUnit -> CSV/JSON
  plot_metrics.py     # pandas + matplotlib -> 4 gráficos
data/                 # metrics.csv / metrics.json (base gerada)
charts/               # gráficos PNG gerados
docs/RELATORIO.md     # relatório técnico do experimento
docs/prints/          # evidências (screenshots das execuções reais)
```

## Pré-requisitos

- Python 3.11+ (o CI usa 3.12).
- Repositório publicado no GitHub (Actions habilitado).
- Um **Personal Access Token (PAT)** para a coleta via API:
  - *Classic*: escopo `repo` (ou `public_repo`) — inclui leitura de Actions.
  - *Fine-grained*: permissões **Actions: Read-only** e **Contents: Read-only**.
  - **Nunca** comite o token. Ele é lido apenas de variáveis de ambiente.

## Como reproduzir o experimento

### 1. Ambiente local

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

### 2. Rodar testes e lint localmente

```bash
ruff check .
pytest --junitxml=reports/junit.xml --cov=app --cov-report=xml:reports/coverage.xml
```

### 3. Disparar execuções do pipeline (≥12, com variações)

`git push` dispara o workflow. Há duas formas de variar:

- **Variações de código** (commits reais): quebrar/consertar um teste, etc.
- **Variações de configuração** (sem editar código), via *Actions → CI → Run workflow*
  ou pela CLI:

```bash
# liga/desliga cache, infla nº de testes, introduz teste lento
gh workflow run ci.yml -f use_cache=false -f bulk_tests=50 -f slow_test_seconds=20
```

Variáveis de ambiente que os testes leem (também configuráveis localmente):

| Variável            | Efeito                                            |
|---------------------|---------------------------------------------------|
| `BULK_TESTS`        | nº de testes triviais extras (infla a contagem)   |
| `SLOW_TEST_SECONDS` | duração de um teste artificialmente lento         |

A variação **paralelo vs. sequencial** é feita por commit no `ci.yml`
(comentar/remover `needs: lint` no job `test`). Veja a matriz completa em
[docs/RELATORIO.md](docs/RELATORIO.md).

### 4. Coletar as métricas

```bash
export GITHUB_TOKEN=ghp_xxxxxxxx
export GITHUB_REPO=SEU_USUARIO/ponderada-ci-cd
python scripts/collect_metrics.py --workflow ci.yml --limit 50
# -> data/metrics.csv e data/metrics.json
```

### 5. Gerar os gráficos

```bash
python scripts/plot_metrics.py
# -> charts/01..04_*.png
```

### 6. Relatório

Preencha [docs/RELATORIO.md](docs/RELATORIO.md) com os dados/evidências reais
(IDs de run, commits, prints, gráficos e análise).

## Esquema do CSV

```
run_id,commit_sha,commit_message,status,workflow_duration,job_name,job_duration,test_count,test_failures,timestamp,conclusion,run_attempt,test_time_avg,lead_time,step_breakdown
```

Uma linha por **(run, job)**; as colunas após `timestamp` são extras úteis para a análise.
