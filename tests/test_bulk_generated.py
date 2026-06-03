"""Testes parametrizados usados para VARIAÇÕES do experimento de CI/CD.

Dois eixos de variação, controlados por variáveis de ambiente para que o
mesmo arquivo sirva tanto para edição via commit quanto para `workflow_dispatch`:

* ``BULK_TESTS``        -> quantos testes triviais extras gerar (default 0).
* ``SLOW_TEST_SECONDS`` -> duração de um teste artificialmente lento (default 0 = pulado).

Exemplos:
    BULK_TESTS=50 pytest          # infla a contagem de testes
    SLOW_TEST_SECONDS=20 pytest   # introduz um teste lento
"""

from __future__ import annotations

import os
import time

import pytest

BULK_TESTS = int(os.environ.get("BULK_TESTS", "0"))
SLOW_TEST_SECONDS = float(os.environ.get("SLOW_TEST_SECONDS", "0"))


@pytest.mark.parametrize("n", range(BULK_TESTS))
def test_bulk(n: int) -> None:
    # Teste trivial e determinístico; só existe para inflar a contagem.
    assert n + n == 2 * n


@pytest.mark.skipif(SLOW_TEST_SECONDS <= 0, reason="teste lento desativado (SLOW_TEST_SECONDS<=0)")
def test_slow() -> None:
    time.sleep(SLOW_TEST_SECONDS)
    assert True
