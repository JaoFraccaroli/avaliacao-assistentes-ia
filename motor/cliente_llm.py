"""Cliente do Ollama (IA rodando localmente, de graça).

A IA é acessada por uma interface simples (`responder(sistema, mensagem) -> str`),
assim os testes rápidos podem usar uma IA falsa no lugar da verdadeira.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Protocol


class ModeloDeLinguagem(Protocol):
    nome: str

    def responder(self, sistema: str, mensagem: str) -> str: ...


class ClienteOllama:
    """Conversa com o Ollama pela API HTTP local (padrão: http://localhost:11434)."""

    def __init__(self, nome: str, url: str | None = None, timeout: float = 120.0):
        self.nome = nome
        self.url = (url or os.environ.get("OLLAMA_URL", "http://localhost:11434")).rstrip("/")
        self.timeout = timeout

    def responder(self, sistema: str, mensagem: str) -> str:
        corpo = {
            "model": self.nome,
            "messages": [
                {"role": "system", "content": sistema},
                {"role": "user", "content": mensagem},
            ],
            "stream": False,
            # temperatura 0 e semente fixa: respostas o mais repetíveis possível
            # num_predict limita o tamanho da resposta: evita a IA "disparar" texto sem parar
            "options": {"temperature": 0, "seed": 42, "num_ctx": 4096, "num_predict": 300},
        }
        pedido = urllib.request.Request(
            f"{self.url}/api/chat",
            data=json.dumps(corpo).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(pedido, timeout=self.timeout) as resposta:
            dados = json.loads(resposta.read().decode("utf-8"))
        return dados["message"]["content"].strip()


def ollama_disponivel(url: str | None = None) -> bool:
    url = (url or os.environ.get("OLLAMA_URL", "http://localhost:11434")).rstrip("/")
    try:
        with urllib.request.urlopen(f"{url}/api/tags", timeout=3):
            return True
    except (urllib.error.URLError, OSError):
        return False
