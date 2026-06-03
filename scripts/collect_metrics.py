#!/usr/bin/env python3
"""Coleta métricas reais de execuções do GitHub Actions.

Combina DUAS fontes, como exige o enunciado do experimento:

1. **API REST do GitHub** — durações de workflow/job/step, status, commit
   (sha + mensagem), tentativa e timestamps.
2. **Artefato JUnit XML** gerado pelo pipeline — quantidade de testes,
   falhas e tempo médio dos testes (com fallback para ``test-summary.json``).

Saídas:
    data/metrics.csv   uma linha por (run, job), no schema pedido pela atividade.
    data/metrics.json  estrutura aninhada completa (run -> jobs -> steps).

Uso:
    export GITHUB_TOKEN=ghp_xxx           # PAT com permissão de leitura de Actions
    export GITHUB_REPO=owner/repositorio  # ex.: LuccaHP/ponderada-ci-cd
    python scripts/collect_metrics.py [--workflow ci.yml] [--limit 50]

NUNCA commite o token. O script só lê variáveis de ambiente.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

import requests

API_ROOT = "https://api.github.com"
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"

CSV_COLUMNS = [
    "run_id",
    "commit_sha",
    "commit_message",
    "status",
    "workflow_duration",
    "job_name",
    "job_duration",
    "test_count",
    "test_failures",
    "timestamp",
    # Colunas extras úteis para a análise/visualização (opcionais no enunciado).
    "conclusion",
    "run_attempt",
    "test_time_avg",
    "lead_time",
    "step_breakdown",
]


# --------------------------------------------------------------------------- #
# Utilidades                                                                   #
# --------------------------------------------------------------------------- #
def parse_iso(value: str | None) -> datetime | None:
    """Converte timestamp ISO-8601 do GitHub (sufixo Z) em datetime."""
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def iso_diff_seconds(start: str | None, end: str | None) -> float | None:
    """Diferença em segundos entre dois timestamps ISO-8601."""
    s, e = parse_iso(start), parse_iso(end)
    if s is None or e is None:
        return None
    return round((e - s).total_seconds(), 3)


class GitHubClient:
    """Wrapper mínimo da API REST do GitHub com paginação."""

    def __init__(self, token: str, repo: str) -> None:
        self.repo = repo
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )

    def _get(self, path: str, **params: Any) -> requests.Response:
        resp = self.session.get(f"{API_ROOT}{path}", params=params, timeout=60)
        if resp.status_code == 403 and "rate limit" in resp.text.lower():
            raise SystemExit("Rate limit da API atingido. Tente novamente mais tarde.")
        resp.raise_for_status()
        return resp

    def list_runs(self, workflow: str | None, limit: int) -> list[dict[str, Any]]:
        """Lista execuções do workflow (todas, ou só de um arquivo específico)."""
        if workflow:
            path = f"/repos/{self.repo}/actions/workflows/{workflow}/runs"
        else:
            path = f"/repos/{self.repo}/actions/runs"
        runs: list[dict[str, Any]] = []
        page = 1
        while len(runs) < limit:
            data = self._get(path, per_page=100, page=page).json()
            batch = data.get("workflow_runs", [])
            if not batch:
                break
            runs.extend(batch)
            page += 1
        return runs[:limit]

    def list_jobs(self, run_id: int) -> list[dict[str, Any]]:
        path = f"/repos/{self.repo}/actions/runs/{run_id}/jobs"
        return self._get(path, per_page=100).json().get("jobs", [])

    def list_artifacts(self, run_id: int) -> list[dict[str, Any]]:
        path = f"/repos/{self.repo}/actions/runs/{run_id}/artifacts"
        return self._get(path).json().get("artifacts", [])

    def download_artifact_zip(self, artifact_id: int) -> bytes:
        path = f"/repos/{self.repo}/actions/artifacts/{artifact_id}/zip"
        return self._get(path).content


# --------------------------------------------------------------------------- #
# Parse do artefato de testes                                                  #
# --------------------------------------------------------------------------- #
def parse_test_metrics(zip_bytes: bytes) -> dict[str, Any]:
    """Extrai contagem/falhas/tempo médio do JUnit XML (ou do summary JSON)."""
    result = {"test_count": None, "test_failures": None, "test_time_avg": None}
    try:
        archive = zipfile.ZipFile(io.BytesIO(zip_bytes))
    except zipfile.BadZipFile:
        return result

    names = archive.namelist()

    # Preferência 1: JUnit XML.
    junit_name = next((n for n in names if n.endswith("junit.xml")), None)
    if junit_name:
        try:
            root = ET.fromstring(archive.read(junit_name))
        except ET.ParseError:
            root = None
        if root is not None:
            suites = root.findall("testsuite") or ([root] if root.tag == "testsuite" else [])
            tests = sum(int(s.get("tests", 0)) for s in suites)
            failures = sum(int(s.get("failures", 0)) + int(s.get("errors", 0)) for s in suites)
            total_time = sum(float(s.get("time", 0)) for s in suites)
            result["test_count"] = tests
            result["test_failures"] = failures
            result["test_time_avg"] = round(total_time / tests, 4) if tests else 0.0
            return result

    # Preferência 2: summary JSON (fallback gerado pelo pipeline).
    summary_name = next((n for n in names if n.endswith("test-summary.json")), None)
    if summary_name:
        summary = json.loads(archive.read(summary_name))
        tests = int(summary.get("tests", 0))
        result["test_count"] = tests
        result["test_failures"] = int(summary.get("failures", 0)) + int(summary.get("errors", 0))
        result["test_time_avg"] = round(float(summary.get("time", 0)) / tests, 4) if tests else 0.0
    return result


# --------------------------------------------------------------------------- #
# Montagem dos registros                                                       #
# --------------------------------------------------------------------------- #
def build_run_record(client: GitHubClient, run: dict[str, Any]) -> dict[str, Any]:
    """Monta a estrutura aninhada de uma run com seus jobs/steps e métricas de teste."""
    run_id = run["id"]
    workflow_duration = iso_diff_seconds(run.get("run_started_at"), run.get("updated_at"))
    lead_time = iso_diff_seconds(run.get("created_at"), run.get("updated_at"))

    # Métricas de teste vêm do artefato (pode não existir se a run nem chegou a testar).
    test_metrics = {"test_count": None, "test_failures": None, "test_time_avg": None}
    for art in client.list_artifacts(run_id):
        if art["name"].startswith("reports") and not art.get("expired", False):
            try:
                test_metrics = parse_test_metrics(client.download_artifact_zip(art["id"]))
            except requests.HTTPError:
                pass
            break

    jobs_out: list[dict[str, Any]] = []
    for job in client.list_jobs(run_id):
        steps = [
            {
                "name": st.get("name"),
                "conclusion": st.get("conclusion"),
                "duration": iso_diff_seconds(st.get("started_at"), st.get("completed_at")),
            }
            for st in job.get("steps", [])
        ]
        jobs_out.append(
            {
                "name": job.get("name"),
                "status": job.get("status"),
                "conclusion": job.get("conclusion"),
                "duration": iso_diff_seconds(job.get("started_at"), job.get("completed_at")),
                "steps": steps,
            }
        )

    return {
        "run_id": run_id,
        "commit_sha": run.get("head_sha"),
        "commit_message": (run.get("head_commit") or {}).get("message", "").splitlines()[0]
        if run.get("head_commit")
        else "",
        "status": run.get("status"),
        "conclusion": run.get("conclusion"),
        "run_attempt": run.get("run_attempt"),
        "workflow_duration": workflow_duration,
        "lead_time": lead_time,
        "timestamp": run.get("run_started_at"),
        "test_metrics": test_metrics,
        "jobs": jobs_out,
    }


def flatten_to_rows(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Achata cada run em uma linha por job (schema do CSV)."""
    rows: list[dict[str, Any]] = []
    for rec in records:
        tm = rec["test_metrics"]
        jobs = rec["jobs"] or [{"name": None, "duration": None, "conclusion": None, "steps": []}]
        for job in jobs:
            rows.append(
                {
                    "run_id": rec["run_id"],
                    "commit_sha": rec["commit_sha"],
                    "commit_message": rec["commit_message"],
                    "status": rec["status"],
                    "workflow_duration": rec["workflow_duration"],
                    "job_name": job["name"],
                    "job_duration": job["duration"],
                    "test_count": tm["test_count"],
                    "test_failures": tm["test_failures"],
                    "timestamp": rec["timestamp"],
                    "conclusion": rec["conclusion"],
                    "run_attempt": rec["run_attempt"],
                    "test_time_avg": tm["test_time_avg"],
                    "lead_time": rec["lead_time"],
                    "step_breakdown": json.dumps(
                        {s["name"]: s["duration"] for s in job["steps"]}, ensure_ascii=False
                    ),
                }
            )
    return rows


def write_csv(rows: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def write_json(records: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")


# --------------------------------------------------------------------------- #
# CLI                                                                          #
# --------------------------------------------------------------------------- #
def main() -> int:
    parser = argparse.ArgumentParser(description="Coleta métricas do GitHub Actions.")
    parser.add_argument("--workflow", default="ci.yml", help="Arquivo do workflow (default: ci.yml)")
    parser.add_argument("--limit", type=int, default=50, help="Máximo de runs a coletar")
    parser.add_argument(
        "--only-completed", action="store_true", help="Ignorar runs ainda em andamento"
    )
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPO")
    if not token or not repo:
        print("ERRO: defina GITHUB_TOKEN e GITHUB_REPO (owner/repo) no ambiente.", file=sys.stderr)
        return 2

    client = GitHubClient(token, repo)
    print(f"Coletando runs de {repo} (workflow={args.workflow}, limite={args.limit})...")
    runs = client.list_runs(args.workflow, args.limit)
    if args.only_completed:
        runs = [r for r in runs if r.get("status") == "completed"]
    print(f"  {len(runs)} run(s) encontradas.")

    records = []
    for run in runs:
        print(f"  - run {run['id']} ({run.get('conclusion') or run.get('status')})")
        records.append(build_run_record(client, run))

    rows = flatten_to_rows(records)
    write_csv(rows, DATA_DIR / "metrics.csv")
    write_json(records, DATA_DIR / "metrics.json")
    print(f"OK: {len(rows)} linhas -> {DATA_DIR/'metrics.csv'}")
    print(f"OK: {len(records)} runs -> {DATA_DIR/'metrics.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
