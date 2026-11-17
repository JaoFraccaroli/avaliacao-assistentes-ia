"""Avaliação com a IA de verdade (só roda com o Ollama ligado): pytest -m avaliacao

O modelo vem da variável MODELO (padrão: qwen2.5:3b).
"""
import os

import pytest

from conftest import RAIZ
from motor.avaliacao import avaliar
from motor.avaliar import criar_assistente, minimos
from motor.casos import carregar_casos
from motor.cliente_llm import ClienteOllama, ollama_disponivel

pytestmark = [
    pytest.mark.avaliacao,
    pytest.mark.skipif(not ollama_disponivel(), reason="Ollama não está rodando"),
]


@pytest.mark.parametrize("nome", ["loja", "dnd"])
def test_assistente_atinge_os_minimos(nome):
    modelo = ClienteOllama(os.environ.get("MODELO", "qwen2.5:3b"))
    r = avaliar(criar_assistente(nome), modelo, carregar_casos(RAIZ / "casos" / f"{nome}.csv"), minimos(nome))
    reprovadas = [f"{c.descricao}: {c.taxa:.0%} (mínimo {c.minimo:.0%})" for c in r.categorias if not c.aprovada]
    assert not reprovadas, "; ".join(reprovadas)
