#!/usr/bin/env python3
"""Gera os gráficos do experimento a partir de data/metrics.csv.

Produz (no mínimo) os 4 gráficos obrigatórios em charts/:
    01_pipeline_duration.png   tempo total do pipeline por execução
    02_duration_by_job.png     tempo médio por job/etapa
    03_success_failure_rate.png taxa de sucesso x falha
    04_tests_vs_duration.png   relação nº de testes x duração do pipeline

Uso:
    python scripts/plot_metrics.py [--csv data/metrics.csv] [--out charts]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # backend sem display (CI / terminal)
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT_DIR = Path(__file__).resolve().parent.parent


def load_data(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
    return df


def run_level(df: pd.DataFrame) -> pd.DataFrame:
    """Reduz o CSV (1 linha por job) para 1 linha por run, ordenado por tempo."""
    agg = (
        df.sort_values("timestamp")
        .groupby("run_id", as_index=False)
        .agg(
            timestamp=("timestamp", "first"),
            commit_sha=("commit_sha", "first"),
            workflow_duration=("workflow_duration", "first"),
            conclusion=("conclusion", "first"),
            test_count=("test_count", "max"),
            test_failures=("test_failures", "max"),
        )
        .sort_values("timestamp")
        .reset_index(drop=True)
    )
    agg["label"] = [f"#{i+1}\n{str(s)[:7]}" for i, s in enumerate(agg["commit_sha"])]
    return agg


def plot_pipeline_duration(runs: pd.DataFrame, out: Path) -> None:
    fig, ax = plt.subplots(figsize=(11, 5))
    colors = ["#2ca02c" if c == "success" else "#d62728" for c in runs["conclusion"]]
    ax.bar(runs["label"], runs["workflow_duration"], color=colors)
    ax.set_title("Tempo total do pipeline por execução")
    ax.set_xlabel("Execução (ordem cronológica / commit)")
    ax.set_ylabel("Duração (s)")
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    fig.tight_layout()
    fig.savefig(out, dpi=120)
    plt.close(fig)


def plot_duration_by_job(df: pd.DataFrame, out: Path) -> None:
    means = df.groupby("job_name")["job_duration"].mean().sort_values()
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(means.index.astype(str), means.values, color="#1f77b4")
    ax.set_title("Tempo médio por job")
    ax.set_xlabel("Duração média (s)")
    ax.grid(axis="x", linestyle="--", alpha=0.4)
    fig.tight_layout()
    fig.savefig(out, dpi=120)
    plt.close(fig)


def plot_success_failure(runs: pd.DataFrame, out: Path) -> None:
    counts = runs["conclusion"].fillna("desconhecido").value_counts()
    color_map = {"success": "#2ca02c", "failure": "#d62728"}
    colors = [color_map.get(k, "#7f7f7f") for k in counts.index]
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(counts.values, labels=counts.index, autopct="%1.0f%%", colors=colors, startangle=90)
    ax.set_title(f"Taxa de sucesso x falha (n={int(counts.sum())} runs)")
    fig.tight_layout()
    fig.savefig(out, dpi=120)
    plt.close(fig)


def plot_tests_vs_duration(runs: pd.DataFrame, out: Path) -> None:
    valid = runs.dropna(subset=["test_count", "workflow_duration"])
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(valid["test_count"], valid["workflow_duration"], color="#9467bd", s=60, zorder=3)
    # Linha de tendência (se houver variação suficiente).
    if valid["test_count"].nunique() > 1:
        coef = np.polyfit(valid["test_count"], valid["workflow_duration"], 1)
        xs = np.linspace(valid["test_count"].min(), valid["test_count"].max(), 100)
        ax.plot(xs, np.polyval(coef, xs), "--", color="#555", label=f"tendência (slope={coef[0]:.2f})")
        ax.legend()
    ax.set_title("Relação entre nº de testes e duração do pipeline")
    ax.set_xlabel("Quantidade de testes executados")
    ax.set_ylabel("Duração do pipeline (s)")
    ax.grid(linestyle="--", alpha=0.4)
    fig.tight_layout()
    fig.savefig(out, dpi=120)
    plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera gráficos das métricas de CI/CD.")
    parser.add_argument("--csv", default=str(ROOT_DIR / "data" / "metrics.csv"))
    parser.add_argument("--out", default=str(ROOT_DIR / "charts"))
    args = parser.parse_args()

    csv_path = Path(args.csv)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    df = load_data(csv_path)
    runs = run_level(df)
    print(f"Carregado: {len(df)} linhas / {len(runs)} runs de {csv_path}")

    plot_pipeline_duration(runs, out_dir / "01_pipeline_duration.png")
    plot_duration_by_job(df, out_dir / "02_duration_by_job.png")
    plot_success_failure(runs, out_dir / "03_success_failure_rate.png")
    plot_tests_vs_duration(runs, out_dir / "04_tests_vs_duration.png")
    print(f"OK: 4 gráficos gerados em {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
